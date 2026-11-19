"""
Some usefull functions and tools which don't need to depend
to a specific module/class.
"""

import datetime
from pathlib import Path


def get_metadata(filepath: str | Path) -> dict:
    """
    Get CSV trajectory metadata.
    - filepath: CSV filepath to parse
    """
    raw_lines = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line.startswith("#"):
                break
            clean_line = line.lstrip("#").strip()
            if clean_line:
                raw_lines.append(clean_line)
    # Parse params
    params = {}
    for item in raw_lines:
        if ":" in item:
            # Using maxsplit = 1 to prevent datetime splits
            key, val = item.split(":", 1)
            key = key.strip()
            val = val.strip()
            # Automatic conversion int/float else string
            try:
                if "." in val or "e" in val.lower():
                    val = float(val)
                else:
                    val = int(val)
            except ValueError:
                pass
            params[key] = val
    # Add title
    return params


def convert_to_pdf_path(fp: str | Path) -> Path:
    """
    Convert a entered filepath into the same filepath
    with a '.pdf' extension.
    """
    return Path(fp).with_suffix(".pdf")


def get_date():
    """
    Return datetime.datetime string date format.
    """
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
