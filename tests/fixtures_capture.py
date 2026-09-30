"""Capture-directory fixtures for building & exercising `capture assemble`.

These build realistic `--optimize-disk` capture directories using the REAL
`ChunkedGzipSink`, so what `assemble` reads here is byte-identical to what a
production Pi capture writes. Three shapes:

    build_capture(dir)                     -> clean: every chunk closed (valid gzip)
    build_capture(dir, truncate_last=True) -> last chunk flushed but never closed
                                              (crash mid-capture: no gzip trailer)
    build_capture(dir, drop_chunk=i)       -> chunk i removed (manual-rsync gap)
    build_capture_tar(dir)                 -> the same, packed into a sibling
                                              store-mode `<dir>.tar` exactly as
                                              the listener's --bundle produces
                                              (dir removed by default)

Each also gets the crash-safe `<test_id>.meta` sidecar and a `<test_id>.log`.

`build_reference()` writes the plain single-CSV that `assemble(clean_dir)` must
reproduce **byte-for-byte** — your golden oracle while coding assemble. Because
both paths reuse the same rows and the same metadata string, and both sinks emit
`\\r\\n` rows under `newline=""`, equality is exact.

Run as a script to drop inspectable fixtures on disk + a self-check that proves
the oracle holds (that concat is the fixtures validating themselves — NOT the
`assemble` you'll write, which also does the CLI, the tar bundle, gap handling
and the tolerant read of a truncated final chunk):

    .venv/bin/python -m tests.fixtures_capture            # -> ./_capfix/
    .venv/bin/python -m tests.fixtures_capture /tmp/capfix
"""

import csv
import gzip
import io
import math
import os
import shutil
import sys
import tarfile
import zlib
from pathlib import Path

# Repo root on the path when run as a bare script (python tests/fixtures_capture.py).
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.stats.sinks import ChunkedGzipSink, PlainCSVSink  # noqa: E402
from tests.conftest import CAP_COLS                          # noqa: E402


# --------------------------------------------------------------------------- #
# realistic capture content (metadata + rows)
# --------------------------------------------------------------------------- #

def sample_metadata(test_id, protocol="T4"):
    """A `# key: value` block in the listener's exact format (bar lines + kv),
    terminated with a single '\\n'. `read_capture_header` parses this as-is, so
    an assembled CSV carrying it feeds straight into `stats`."""
    bar = "# " + "=" * 60
    lines = [
        bar,
        "#  GRAVILAB TEST CONFIG — self-describing capture (one per test)",
        bar,
        "# --- meta ---",
        f"# test_id: {test_id}",
        "# timestamp_start: 2026-08-07T10:00:00",
        f"# protocol: {protocol}",
        "# operator_notes: fixture",
        "# --- software ---",
        "# tool_version: fixture",
        "# firmware_version: fixture",
        bar,
    ]
    return "\n".join(lines) + "\n"


def sample_rows(n):
    """`n` telemetry rows in the real capture schema (CAP_COLS). Deterministic —
    no RNG — so fixtures are byte-reproducible. Every 3rd row is a motor sample;
    the rest are IMU rows carrying list-literal strings ('[..]') exactly like the
    live stream (the quoted commas are what make byte-fidelity through gzip worth
    testing). Missing columns are left to DictWriter -> empty, as in prod."""
    rows = []
    for i in range(n):
        ts = 1_700_000_000.000 + i * 0.05
        if i % 3 == 2:                                   # motor sample
            rows.append({
                "timestamp_received": f"{ts:.3f}",
                "kind": "motor", "node": "odrv0", "msg_type": "MOTOR",
                "pos_deg": round(0.5 * i, 3), "setpoint_deg": round(0.5 * i, 3),
                "vel_rpm": round(10.0 + (i % 5), 2), "iq": 0.42,
                "bus_v": 24.0, "engaged": True, "state": "CLOSED_LOOP",
            })
        else:                                            # IMU sample
            rows.append({
                "timestamp_received": f"{ts:.3f}",
                "kind": "imu", "node": "esp32-a", "sensor_hz": 20, "push_hz": 20,
                "sensor_id": "sensor_1", "msg_type": "MEASURE",
                "t": round(ts, 3), "t_ok": 1, "tsf": i * 50_000,
                "q2": "[1.0, 0.0, 0.0, 0.0]", "a": "[0.0, 0.0, 9.81]",
                "gr": "[0.0, 0.0, 9.81]", "rssi": -60 - (i % 7),
            })
    return rows


# --------------------------------------------------------------------------- #
# fixture builders
# --------------------------------------------------------------------------- #

def _write_truncated_chunk(path, columns, rows):
    """Write a chunk the way a *crashed* run leaves it: rows flushed to a zlib
    SYNC point, then the process dies before close -> no gzip trailer. Mirrors
    ChunkedGzipSink.flush() exactly, but snapshots the bytes from a BytesIO
    BEFORE any close, so nothing ever appends the trailer (GC included). The
    flushed rows are recoverable via zlib.decompressobj; a plain gzip.open().read()
    raises at EOF — which is precisely what `assemble` must tolerate."""
    raw = io.BytesIO()
    gz = gzip.GzipFile(fileobj=raw, mode="wb")
    text = io.TextIOWrapper(gz, newline="", encoding="utf-8")
    w = csv.DictWriter(text, fieldnames=columns, extrasaction="ignore")
    w.writeheader()
    for r in rows:
        w.writerow(r)
    text.flush()
    gz.flush(zlib.Z_SYNC_FLUSH)          # sync point: bytes so far are decodable
    raw.flush()
    with open(path, "wb") as f:
        f.write(raw.getvalue())          # trailer-less: gz is intentionally never closed


def _write_log(path, test_id, n_chunks, n_rows):
    """A minimal run journal, as the FileHandler would have bundled it."""
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"2026-08-07 10:00:00 INFO launch start · id={test_id}\n")
        for i in range(1, n_chunks):
            f.write(f"2026-08-07 10:{i:02d}:00 INFO 🔁 chunk rotated → chunk_{i:03d}.csv.gz\n")
        f.write(f"2026-08-07 10:{n_chunks:02d}:00 INFO 🏁 session end · rx={n_rows} messages\n")


def build_capture(capture_dir, *, test_id="T4_fixture", protocol="T4",
                  n_rows=25, rows_per_chunk=10,
                  truncate_last=False, drop_chunk=None, with_log=True):
    """Build a `--optimize-disk` capture directory and return its Path.

    Chunks are rotated deterministically every `rows_per_chunk` rows (via the
    sink's own `_rotate` — test-only; production rotates on time). Yields
    ceil(n_rows / rows_per_chunk) chunks, the last one partial.

    truncate_last : the final chunk is written flushed-but-not-closed (crash).
    drop_chunk    : delete chunk `i` after building (manual-offload gap).
    """
    capture_dir = str(capture_dir)
    rows = sample_rows(n_rows)
    meta = sample_metadata(test_id, protocol)
    n_chunks = math.ceil(n_rows / rows_per_chunk)
    if truncate_last and n_chunks < 2:
        raise ValueError("need >= 2 chunks to truncate the last one")

    # The sink writes every cleanly-closed chunk. When truncating, hold back the
    # final chunk's rows and write that chunk by hand (below) so the sink never
    # finalises it into a valid gzip.
    n_clean = (n_chunks - 1) if truncate_last else n_chunks
    clean_rows = rows[: n_clean * rows_per_chunk]

    sink = ChunkedGzipSink(capture_dir, CAP_COLS, test_id, segment_seconds=10_000)
    for i, r in enumerate(clean_rows):
        if i and i % rows_per_chunk == 0:
            sink._rotate()                       # explicit boundary (deterministic)
        sink.write_row(r)
    sink.write_metadata(meta)                    # sidecar, as a heartbeat would
    sink.close()                                 # finalise chunks 0..n_clean-1

    if truncate_last:
        _write_truncated_chunk(
            os.path.join(capture_dir, f"chunk_{n_chunks - 1:03d}.csv.gz"),
            CAP_COLS, rows[n_clean * rows_per_chunk:])

    if drop_chunk is not None:
        os.remove(os.path.join(capture_dir, f"chunk_{drop_chunk:03d}.csv.gz"))

    if with_log:
        _write_log(os.path.join(capture_dir, f"{test_id}.log"),
                   test_id, n_chunks, n_rows)
    return Path(capture_dir)


def build_reference(csv_path, *, test_id="T4_fixture", protocol="T4", n_rows=25):
    """Write the plain single-CSV that `assemble(clean capture)` must reproduce
    byte-for-byte: metadata block + one column header + all rows. Same rows and
    same metadata string as build_capture -> exact byte target."""
    rows = sample_rows(n_rows)
    meta = sample_metadata(test_id, protocol)
    sink = PlainCSVSink(str(csv_path), CAP_COLS)
    for r in rows:
        sink.write_row(r)
    sink.write_metadata(meta)
    sink.close()
    return Path(csv_path)


def build_capture_tar(capture_dir, *, keep_dir=False, **kwargs):
    """Build a capture dir (via build_capture) then pack it into a sibling
    store-mode `<dir>.tar`, byte-for-byte as the listener's --bundle does:
    tarfile mode "w" (no gzip — chunks are already compressed), arcname =
    basename so extraction recreates `<test_id>/chunk_000...`. Returns the .tar
    Path. keep_dir=False (default, mirroring prod) removes the source dir so only
    the .tar remains; keep_dir=True leaves the dir alongside for A/B testing your
    assembler on the dir vs the tar. **kwargs pass straight to build_capture
    (test_id, protocol, n_rows, rows_per_chunk, truncate_last, drop_chunk...)."""
    cap = build_capture(capture_dir, **kwargs)
    src = str(cap)
    tar_path = src + ".tar"
    with tarfile.open(tar_path, "w") as tar:            # "w" = store; never "w:gz"
        tar.add(src, arcname=os.path.basename(src))
    if not keep_dir:
        shutil.rmtree(src)
    return Path(tar_path)


# --------------------------------------------------------------------------- #
# script entry point: drop fixtures + prove the oracle
# --------------------------------------------------------------------------- #

def _read_sidecar(capture_dir):
    metas = sorted(Path(capture_dir).glob("*.meta"))
    return metas[0].read_text(encoding="utf-8") if metas else None


def _sorted_chunks(capture_dir):
    chunks = list(Path(capture_dir).glob("chunk_*.csv.gz"))
    return sorted(chunks, key=lambda p: int(p.stem.split("_")[1].split(".")[0]))


def _tolerant_lines(path):
    """Read a chunk's text even if the gzip trailer is missing (truncated run)."""
    raw = Path(path).read_bytes()
    dec = zlib.decompressobj(16 + zlib.MAX_WBITS)
    try:
        text = dec.decompress(raw) + dec.flush()
    except zlib.error:
        text = dec.decompress(raw)               # keep whatever decoded before the tear
    return text.decode("utf-8", errors="replace").splitlines(keepends=True)


def _inventory(name, capture_dir):
    print(f"\n[{name}] {capture_dir}")
    for p in _sorted_chunks(capture_dir):
        try:
            with gzip.open(p, "rt", newline="") as fh:
                n = len(fh.read().splitlines()) - 1
            state = f"valid   · {n:>3} rows"
        except (EOFError, gzip.BadGzipFile, zlib.error):
            n = len(_tolerant_lines(p)) - 1
            state = f"TRUNCATED · {n:>3} rows recovered"
        print(f"    {p.name:<20} {p.stat().st_size:>6}B  {state}")
    for extra in sorted(Path(capture_dir).glob("*.meta")) + sorted(Path(capture_dir).glob("*.log")):
        print(f"    {extra.name:<20} {extra.stat().st_size:>6}B")


def _selfcheck_roundtrip(clean_dir, reference_csv):
    """Prove the fixtures are internally consistent: a naive concat of the clean
    chunks (sidecar + chunk0 with header + later chunks header-stripped) equals
    the reference plain CSV byte-for-byte. This is the TARGET your `assemble`
    must hit — not a substitute for it."""
    out = io.StringIO()
    out.write(_read_sidecar(clean_dir))
    for i, chunk in enumerate(_sorted_chunks(clean_dir)):
        with gzip.open(chunk, "rt", newline="") as fh:
            lines = fh.readlines()
        out.write("".join(lines if i == 0 else lines[1:]))   # drop repeated header
    got = out.getvalue()
    with open(reference_csv, "r", newline="") as f:
        want = f.read()
    assert got == want, "fixture round-trip != reference (chunks/reference drifted)"
    print(f"\n[selfcheck] concat(clean chunks) == reference.csv  ✓  ({len(got)} bytes)")


def _inventory_tar(name, tar_path):
    print(f"\n[{name}] {tar_path}  ({Path(tar_path).stat().st_size}B, store mode)")
    with tarfile.open(tar_path) as tar:
        for m in tar.getmembers():
            if m.isfile():
                print(f"    {m.name:<34} {m.size:>6}B")


def _selfcheck_tar(tar_path, reference_csv, workdir):
    """Prove the .tar faithfully carries the capture: extract it and run the same
    concat check against the reference. Validates the FIXTURE (that the tar holds
    a complete capture), NOT the assembler you'll write to read tars directly."""
    workdir = Path(workdir)
    shutil.rmtree(workdir, ignore_errors=True)
    workdir.mkdir(parents=True)
    with tarfile.open(tar_path) as tar:
        tar.extractall(workdir, filter="data")
    extracted = next(p for p in workdir.iterdir() if p.is_dir())   # arcname=basename
    _selfcheck_roundtrip(extracted, reference_csv)
    print(f"[selfcheck] {Path(tar_path).name} extracts to a faithful capture  ✓")


def main():
    base = Path(sys.argv[1] if len(sys.argv) > 1 else "_capfix")
    clean = build_capture(base / "clean", n_rows=25, rows_per_chunk=10)
    trunc = build_capture(base / "truncated", n_rows=25, rows_per_chunk=10,
                          truncate_last=True)
    gap = build_capture(base / "gap", n_rows=25, rows_per_chunk=10, drop_chunk=1)
    tar = build_capture_tar(base / "bundled", n_rows=25, rows_per_chunk=10)
    ref = build_reference(base / "reference.csv", n_rows=25)

    _inventory("clean", clean)
    _inventory("truncated", trunc)
    _inventory("gap", gap)
    _inventory_tar("bundled.tar", tar)
    print(f"\n[reference] {ref}  ({ref.stat().st_size}B) — assemble(clean) must equal this")
    _selfcheck_roundtrip(clean, ref)
    _selfcheck_tar(tar, ref, base / "_extracted")
    print("\nfixtures ready. Point your `assemble` at the dirs and at bundled.tar.")


if __name__ == "__main__":
    main()
