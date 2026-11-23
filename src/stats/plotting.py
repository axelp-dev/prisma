"""PRISMA Plotting module: Graphical utilities for trajectory and simulation reports."""

import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np

THEME = {
    "primary": "#0F294A",  # Deep navy for titles
    "secondary": "#005AB5",  # High-contrast royal blue (X / theta1)
    "accent": "#D55E00",  # High-contrast vermilion orange (Y / theta2)
    "tertiary": "#00796B",  # Deep teal-green (Z / g_z)
    "text": "#1A202C",  # Near-black slate for crisp labels
    "bg": "#FFFFFF",  # Pure white background for maximum contrast
    "grid": "#CBD5E0",  # Distinct light gray grid
    "border": "#A0AEC0",  # Crisp axis spines
    "danger": "#C53030",  # Strong crimson for thresholds/boundaries
    "success": "#2F855A",  # Strong forest green
}


def _decimate(
    *arrays: np.ndarray,
    max_points: int = 3000,
    randomized: bool = False,
    seed: int = 42,
) -> tuple[np.ndarray, ...]:
    """Subsample aligned arrays along axis 0.

    - randomized=False: regular stride (best for continuous line plots).
    - randomized=True : stratified jittered sampling (eliminates stroboscopic
      aliasing on periodic/constant-speed scatter plots).
    """
    if not arrays:
        return ()
    n = len(arrays[0])
    if n <= max_points:
        return arrays

    if randomized:
        rng = np.random.default_rng(seed)
        edges = np.linspace(0, n, max_points + 1, dtype=int)
        offsets = rng.integers(0, np.maximum(1, np.diff(edges)))
        idx = np.clip(edges[:-1] + offsets, 0, n - 1)
        idx[0] = 0
        idx[-1] = n - 1
        return tuple(arr[idx] for arr in arrays)

    step = max(1, n // max_points)
    return tuple(arr[::step] for arr in arrays)


def apply_axes_styling(ax: plt.Axes) -> None:
    """Apply unified high-contrast styling across 2D plots."""
    ax.set_facecolor(THEME["bg"])
    ax.grid(True, linestyle="--", linewidth=0.6, color=THEME["grid"], alpha=0.85)
    ax.tick_params(colors=THEME["text"], labelsize=8)
    for spine in ax.spines.values():
        spine.set_color(THEME["border"])
        spine.set_linewidth(0.9)


def render_particle_3d_confinement(
    positions: np.ndarray,
    x0: np.ndarray,
    r_tube: float,
    timestamps: np.ndarray,
    ax: plt.Axes,
) -> None:
    """Render 3D particle path enclosed within transparent spherical tube."""
    scale = 1e3 if r_tube >= 1e-3 else 1e6
    unit_str = "mm" if scale == 1e3 else "µm"

    pos_s = positions * scale
    x0_s = x0 * scale
    r_s = r_tube * scale

    # Decimate for fast 3D rendering
    pos_plot, t_plot = _decimate(pos_s, timestamps, max_points=2500, randomized=True)

    # 1. Wireframe boundary sphere
    phi = np.linspace(0, 2 * np.pi, 24)
    theta = np.linspace(0, np.pi, 12)
    xs = r_s * np.outer(np.cos(phi), np.sin(theta))
    ys = r_s * np.outer(np.sin(phi), np.sin(theta))
    zs = r_s * np.outer(np.ones_like(phi), np.cos(theta))
    ax.plot_wireframe(xs, ys, zs, color="#718096", alpha=0.35, linewidth=0.6)

    # 2. Connecting path line + high-contrast chronological scatter (plasma avoids pale middle tones)
    # ax.plot(
    #    pos_plot[:, 0],
    #    pos_plot[:, 1],
    #    pos_plot[:, 2],
    #    color="#4A5568",
    #    linewidth=0.9,
    #    alpha=0.55,
    # )

    sc = ax.scatter(
        pos_plot[:, 0],
        pos_plot[:, 1],
        pos_plot[:, 2],
        c=t_plot,
        cmap="plasma",
        s=8,
        alpha=0.9,
        rasterized=True,
    )

    # 3. Initial anchor & final position markers
    ax.scatter(
        [x0_s[0]],
        [x0_s[1]],
        [x0_s[2]],
        color=THEME["success"],
        edgecolors="black",
        linewidths=0.6,
        s=55,
        marker="^",
        zorder=10,
        label=r"Start $\vec{x}_0$",
    )
    ax.scatter(
        [pos_s[-1, 0]],
        [pos_s[-1, 1]],
        [pos_s[-1, 2]],
        color=THEME["danger"],
        edgecolors="black",
        linewidths=0.6,
        s=45,
        marker="o",
        zorder=10,
        label="End",
    )

    ax.set_box_aspect([1, 1, 1])

    # Zoom around particle trajectory
    all_pts = np.vstack([pos_s, x0_s.reshape(1, 3)])
    center = np.mean(all_pts, axis=0)
    extent = np.max(np.abs(all_pts - center)) * 1.15
    extent = max(extent, 1e-6)
    ax.set_xlim([center[0] - extent, center[0] + extent])
    ax.set_ylim([center[1] - extent, center[1] + extent])
    ax.set_zlim([center[2] - extent, center[2] + extent])

    ax.set_xlabel(f"X [{unit_str}]", fontsize=8, labelpad=2)
    ax.set_ylabel(f"Y [{unit_str}]", fontsize=8, labelpad=2)
    ax.set_zlabel(f"Z [{unit_str}]", fontsize=8, labelpad=2)
    ax.set_title(
        f"Particle 3D Path ({unit_str})",
        fontsize=10,
        fontweight="bold",
        color=THEME["primary"],
        pad=8,
    )
    ax.legend(loc="upper left", fontsize=7.5, frameon=True, facecolor="white")
    plt.colorbar(sc, ax=ax, shrink=0.55, pad=0.08, label="Time [s]")


def render_temporal_dynamics(metrics: dict, fig: plt.Figure) -> None:
    """Populate Page 2 with coordinates, velocities, boundary distance, and Re_p."""
    axs = fig.subplots(2, 2)
    scale = metrics["scale"]
    unit_str = metrics["unit_str"]

    t_p, pos_p, vel_p, r_dist_p, re_p = _decimate(
        metrics["timestamp"],
        metrics["positions"] * scale,
        metrics["velocities"] * scale,
        metrics["radial_distances"] * scale,
        metrics["reynolds"],
        max_points=3500,
    )

    # 1. Position coordinates
    ax = axs[0, 0]
    apply_axes_styling(ax)
    ax.plot(t_p, pos_p[:, 0], label=r"$x(t)$", color=THEME["secondary"], linewidth=1.3)
    ax.plot(t_p, pos_p[:, 1], label=r"$y(t)$", color=THEME["accent"], linewidth=1.3)
    ax.plot(t_p, pos_p[:, 2], label=r"$z(t)$", color=THEME["tertiary"], linewidth=1.3)
    ax.axhline(0, color="#718096", linestyle=":", linewidth=0.8)
    ax.set_ylabel(f"Position [{unit_str}]", fontsize=8, fontweight="bold")
    ax.set_title(
        "Coordinate Trajectories", fontsize=9, fontweight="bold", color=THEME["primary"]
    )
    ax.legend(frameon=True, facecolor="white", ncol=3, fontsize=8)

    # 2. Velocity components
    ax = axs[0, 1]
    apply_axes_styling(ax)
    ax.plot(
        t_p, vel_p[:, 0], label=r"$v_x(t)$", color=THEME["secondary"], linewidth=1.3
    )
    ax.plot(t_p, vel_p[:, 1], label=r"$v_y(t)$", color=THEME["accent"], linewidth=1.3)
    ax.plot(t_p, vel_p[:, 2], label=r"$v_z(t)$", color=THEME["tertiary"], linewidth=1.3)
    ax.set_ylabel(f"Velocity [{unit_str}/s]", fontsize=8, fontweight="bold")
    ax.set_title(
        "Hydrodynamic Velocity", fontsize=9, fontweight="bold", color=THEME["primary"]
    )
    ax.legend(frameon=True, facecolor="white", ncol=3, fontsize=8)

    # 3. Radial distance vs confinement limit
    ax = axs[1, 0]
    apply_axes_styling(ax)
    r_tube_s = metrics["r_tube"] * scale
    ax.plot(
        t_p,
        r_dist_p,
        color=THEME["secondary"],
        linewidth=1.4,
        label=r"$\|\vec{r}(t)\|$",
    )
    ax.axhline(
        r_tube_s,
        color=THEME["danger"],
        linestyle="--",
        linewidth=1.3,
        label=r"Boundary $R_{\mathrm{tube}}$",
    )
    ax.set_xlabel("Time [s]", fontsize=8, fontweight="bold")
    ax.set_ylabel(f"Distance [{unit_str}]", fontsize=8, fontweight="bold")
    ax.set_title(
        "Cell/Tube Confinement Proximity",
        fontsize=9,
        fontweight="bold",
        color=THEME["primary"],
    )
    ax.legend(frameon=True, facecolor="white", fontsize=8)

    # 4. Instantaneous Reynolds number series
    ax = axs[1, 1]
    apply_axes_styling(ax)
    ax.plot(t_p, re_p, color=THEME["primary"], linewidth=1.3, label=r"$Re_p(t)$")
    ax.axhline(
        0.1,
        color=THEME["danger"],
        linestyle="--",
        linewidth=1.3,
        label=r"Stokes limit $Re_p = 0.1$",
    )
    ax.set_yscale("log")
    ax.set_xlabel("Time [s]", fontsize=8, fontweight="bold")
    ax.set_ylabel(r"$Re_p$ [$\log_{10}$]", fontsize=8, fontweight="bold")
    ax.set_title(
        "Particle Reynolds Number History",
        fontsize=9,
        fontweight="bold",
        color=THEME["primary"],
    )
    ax.legend(frameon=True, facecolor="white", fontsize=8)

    fig.tight_layout()


def render_spectral_and_phase_analysis(metrics: dict, fig: plt.Figure) -> None:
    """Populate Page 3 with FFT spectra, phase portrait, and radial distribution."""
    axs = fig.subplots(2, 2)
    scale = metrics["scale"]
    unit_str = metrics["unit_str"]

    # 1. FFT Comparison: Gravity vs Particle Displacement
    ax = axs[0, 0]
    apply_axes_styling(ax)
    fg_p, ag_p = _decimate(
        metrics["fft_freqs_g"], metrics["fft_amp_g"], max_points=3000
    )
    fz_p, az_p = _decimate(
        metrics["fft_freqs_z"], metrics["fft_amp_z"] * scale, max_points=3000
    )
    ax.plot(
        fg_p,
        ag_p,
        color=THEME["accent"],
        linewidth=1.2,
        alpha=0.85,
        label=r"Forcing $g_z$ [$\mathrm{m/s^2}$]",
    )
    ax.plot(
        fz_p,
        az_p,
        color=THEME["secondary"],
        linewidth=1.3,
        label=f"Response $z$ [{unit_str}]",
    )
    if metrics["tau_k_cutoff_hz"]:
        ax.axvline(
            metrics["tau_k_cutoff_hz"],
            color=THEME["danger"],
            linestyle="--",
            linewidth=1.2,
            label=f"Cutoff $f_k = {metrics['tau_k_cutoff_hz']:.2e}$ Hz",
        )
    max_f = np.max(metrics["fft_freqs_g"]) if len(metrics["fft_freqs_g"]) > 0 else 10.0
    ax.set_xlim([0, min(10.0, max_f)])
    ax.set_xlabel("Frequency [Hz]", fontsize=8, fontweight="bold")
    ax.set_ylabel("Amplitude", fontsize=8, fontweight="bold")
    ax.set_title(
        "Frequency Spectra (FFT)", fontsize=9, fontweight="bold", color=THEME["primary"]
    )
    ax.legend(frameon=True, facecolor="white", fontsize=7.5)

    # 2. Phase Portrait (z vs v_z)
    ax = axs[0, 1]
    apply_axes_styling(ax)
    pos_p, vel_p = _decimate(
        metrics["positions"] * scale,
        metrics["velocities"] * scale,
        max_points=3500,
    )
    ax.plot(pos_p[:, 2], vel_p[:, 2], color=THEME["primary"], linewidth=0.9, alpha=0.85)
    ax.set_xlabel(f"Vertical Position $z$ [{unit_str}]", fontsize=8, fontweight="bold")
    ax.set_ylabel(
        f"Vertical Velocity $v_z$ [{unit_str}/s]", fontsize=8, fontweight="bold"
    )
    ax.set_title(
        "Phase Portrait ($z$ vs $v_z$)",
        fontsize=9,
        fontweight="bold",
        color=THEME["primary"],
    )

    # 3. Radial distance histogram (uses full distribution for statistical accuracy)
    ax = axs[1, 0]
    apply_axes_styling(ax)
    r_dist_s = metrics["radial_distances"] * scale
    r_tube_s = metrics["r_tube"] * scale
    ax.hist(
        r_dist_s,
        bins=35,
        density=True,
        color=THEME["secondary"],
        edgecolor="white",
        linewidth=0.6,
        alpha=0.85,
    )
    ax.axvline(
        r_tube_s,
        color=THEME["danger"],
        linestyle="--",
        linewidth=1.3,
        label=r"Boundary $R_{\mathrm{tube}}$",
    )
    ax.set_xlabel(f"Radial Distance $r$ [{unit_str}]", fontsize=8, fontweight="bold")
    ax.set_ylabel("Probability Density", fontsize=8, fontweight="bold")
    ax.set_title(
        "Radial Distribution Density",
        fontsize=9,
        fontweight="bold",
        color=THEME["primary"],
    )
    ax.legend(frameon=True, facecolor="white", fontsize=8)

    # 4. Orthogonal Transverse Orbit (x vs y)
    ax = axs[1, 1]
    apply_axes_styling(ax)
    ax.plot(
        pos_p[:, 0], pos_p[:, 1], color=THEME["secondary"], linewidth=1.0, alpha=0.85
    )
    circle = plt.Circle(
        (0, 0),
        r_tube_s,
        color=THEME["danger"],
        fill=False,
        linestyle="--",
        linewidth=1.1,
    )
    ax.add_patch(circle)
    ax.set_aspect("equal", "box")
    ax.set_xlim([-r_tube_s * 1.1, r_tube_s * 1.1])
    ax.set_ylim([-r_tube_s * 1.1, r_tube_s * 1.1])
    ax.set_xlabel(f"x [{unit_str}]", fontsize=8, fontweight="bold")
    ax.set_ylabel(f"y [{unit_str}]", fontsize=8, fontweight="bold")
    ax.set_title(
        "Transverse Orbit (x, y)",
        fontsize=9,
        fontweight="bold",
        color=THEME["primary"],
    )

    fig.tight_layout()


def render_unit_sphere_trajectory(
    g_values: np.ndarray, timestamps: np.ndarray, ax: plt.Axes
) -> None:
    """Render gravity path over the 3D unit sphere."""
    phi = np.linspace(0, 2 * np.pi, 26)
    theta = np.linspace(0, np.pi, 13)
    xs = np.outer(np.cos(phi), np.sin(theta))
    ys = np.outer(np.sin(phi), np.sin(theta))
    zs = np.outer(np.ones_like(phi), np.cos(theta))
    ax.plot_wireframe(xs, ys, zs, color="#718096", alpha=0.35, linewidth=0.5)

    g_plot, t_plot = _decimate(g_values, timestamps, max_points=3000, randomized=True)
    norms = np.linalg.norm(g_plot, axis=1, keepdims=True)
    norms[norms == 0.0] = 1.0
    u = g_plot / norms

    sc = ax.scatter(
        u[:, 0],
        u[:, 1],
        u[:, 2],
        c=t_plot,
        cmap="plasma",
        s=9,
        alpha=0.9,
        rasterized=True,
    )
    ax.set_box_aspect([1, 1, 1])
    ax.set_xlim([-1, 1])
    ax.set_ylim([-1, 1])
    ax.set_zlim([-1, 1])
    ax.set_xlabel(r"$X_{\mathrm{R2}}$", fontsize=8, labelpad=2)
    ax.set_ylabel(r"$Y_{\mathrm{R2}}$", fontsize=8, labelpad=2)
    ax.set_zlabel(r"$Z_{\mathrm{R2}}$", fontsize=8, labelpad=2)
    ax.set_title(
        r"3D Trajectory on Unit Sphere ($\vec{g}_{\mathrm{R2}} / g_0$)",
        fontsize=10,
        fontweight="bold",
        color=THEME["primary"],
        pad=8,
    )
    plt.colorbar(sc, ax=ax, shrink=0.55, pad=0.08, label="Time [s]")


def render_mollweide_heatmap(
    lon: np.ndarray,
    lat: np.ndarray,
    ax: plt.Axes,
    bins: tuple[int, int] = (72, 36),
) -> None:
    """Render surface probability density in Mollweide equal-area projection."""
    lon_edges = np.linspace(-np.pi, np.pi, bins[0] + 1)
    lat_edges = np.linspace(-np.pi / 2, np.pi / 2, bins[1] + 1)
    hist, _, _ = np.histogram2d(lon, lat, bins=[lon_edges, lat_edges])

    lat_centers = 0.5 * (lat_edges[:-1] + lat_edges[1:])
    cos_lat = np.clip(np.cos(lat_centers), 1e-3, 1.0)
    d_lon = lon_edges[1] - lon_edges[0]
    d_lat = lat_edges[1] - lat_edges[0]
    area_elements = d_lon * d_lat * cos_lat[None, :]

    total_samples = np.sum(hist)
    density = (
        hist / (total_samples * area_elements)
        if total_samples > 0
        else np.zeros_like(hist)
    )

    density_plot = density.T
    density_masked = np.ma.masked_where(density_plot == 0.0, density_plot)

    non_zero_vals = density[density > 0]
    if len(non_zero_vals) > 0:
        v_max = max(float(np.percentile(non_zero_vals, 98)), 0.16)
    else:
        v_max = 0.16

    ax.set_facecolor("#F8FAFC")
    ax.grid(True, linestyle=":", alpha=0.7, color="#718096", linewidth=0.7)

    Lon, Lat = np.meshgrid(lon_edges, lat_edges)

    # Use with_extremes to avoid PendingDeprecationWarning on set_bad
    # cmap = plt.get_cmap("YlOrRd").with_extremes(bad="#F8FAFC")
    # norm = mcolors.PowerNorm(gamma=0.6, vmin=0.0, vmax=v_max)
    base_cmap = plt.get_cmap("plasma_r")
    colors = base_cmap(np.linspace(0.15, 1.0, 256))
    cmap = mcolors.ListedColormap(colors).with_extremes(bad="#F1F5F9")
    norm = mcolors.PowerNorm(gamma=0.5, vmin=0.0, vmax=v_max)

    mesh = ax.pcolormesh(
        Lon,
        Lat,
        density_masked,
        cmap=cmap,
        norm=norm,
        shading="flat",
        edgecolors="none",
    )

    ax.set_title(
        r"Surface Density of $\vec{g}_{\mathrm{R2}}$ (Mollweide Projection)",
        fontsize=10,
        fontweight="bold",
        color=THEME["primary"],
        pad=10,
    )

    cbar = plt.colorbar(
        mesh,
        ax=ax,
        orientation="horizontal",
        shrink=0.65,
        pad=0.10,
        extend="max",
    )
    cbar.set_label(
        r"Probability Density [$\mathrm{sr}^{-1}$] (Uniform isotropic $\approx 0.08$)",
        fontsize=8,
    )
    cbar.ax.tick_params(labelsize=7)
    if v_max >= 0.08:
        cbar.ax.axvline(0.08, color=THEME["secondary"], linestyle="--", linewidth=1.4)


def render_motor_kinematics(metrics: dict, fig: plt.Figure) -> None:
    """Populate figure with gimbal positions, velocities, apparent gravity, and convergence."""
    axs = fig.subplots(2, 2)

    t_p, th1_p, th2_p, w1_p, w2_p, w_norm_p, g_p, res_p = _decimate(
        metrics["timestamp"],
        metrics["theta1"],
        metrics["theta2"],
        metrics["omega1"],
        metrics["omega2"],
        metrics["omega_norm_series"],
        metrics["g"],
        metrics["residual_norm_series"],
        max_points=3000,
    )

    # 1. Motor positions (dashed overlay reveals overlapping curves when theta1 == theta2)
    ax = axs[0, 0]
    apply_axes_styling(ax)
    ax.plot(
        t_p,
        th1_p,
        label=r"$\theta_1$ (Inner gimbal)",
        color=THEME["secondary"],
        linewidth=1.6,
    )
    ax.plot(
        t_p,
        th2_p,
        label=r"$\theta_2$ (Outer gimbal)",
        color=THEME["accent"],
        linestyle="--",
        linewidth=1.5,
    )
    ax.set_ylabel("Angle [rad]", fontsize=8, fontweight="bold")
    ax.set_title(
        "Gimbal Positions", fontsize=9, fontweight="bold", color=THEME["primary"]
    )
    ax.legend(frameon=True, facecolor="white", fontsize=8)

    # 2. Angular velocities
    ax = axs[0, 1]
    apply_axes_styling(ax)
    ax.plot(
        t_p,
        w1_p,
        label=r"$\omega_1 = \dot{\theta}_1$",
        color=THEME["secondary"],
        linewidth=1.6,
    )
    ax.plot(
        t_p,
        w2_p,
        label=r"$\omega_2 = \dot{\theta}_2$",
        color=THEME["accent"],
        linestyle="--",
        linewidth=1.5,
    )
    ax.plot(
        t_p,
        w_norm_p,
        label=r"$\|\vec{\Omega}_{\mathrm{R2}}\|$ total",
        color=THEME["text"],
        linestyle=":",
        linewidth=1.2,
    )
    ax.set_ylabel("Velocity [rad/s]", fontsize=8, fontweight="bold")
    ax.set_title(
        "Angular Velocities",
        fontsize=9,
        fontweight="bold",
        color=THEME["primary"],
    )
    ax.legend(frameon=True, facecolor="white", fontsize=8)

    # 3. Apparent gravity components (zoom on last 25s if duration > 40s to avoid solid block)
    ax = axs[1, 0]
    apply_axes_styling(ax)
    t_full = metrics["timestamp"]
    g_full = metrics["g"]
    if len(t_full) > 1 and (t_full[-1] - t_full[0]) > 40.0:
        mask = t_full >= (t_full[-1] - 25.0)
        t_g, g_sub = _decimate(t_full[mask], g_full[mask], max_points=1500)
        title_g = r"Apparent Gravity in $\mathrm{R}_2$ (Last 25 s)"
    else:
        t_g, g_sub = t_p, g_p
        title_g = r"Apparent Gravity Vector in $\mathrm{R}_2$"

    ax.plot(
        t_g,
        g_sub[:, 0],
        label=r"$g_x$",
        color=THEME["secondary"],
        linewidth=1.2,
        alpha=0.9,
    )
    ax.plot(
        t_g,
        g_sub[:, 1],
        label=r"$g_y$",
        color=THEME["accent"],
        linewidth=1.2,
        alpha=0.9,
    )
    ax.plot(
        t_g,
        g_sub[:, 2],
        label=r"$g_z$",
        color=THEME["tertiary"],
        linewidth=1.2,
        alpha=0.85,
    )
    ax.axhline(0.0, color="#718096", linestyle=":", linewidth=0.8)
    ax.set_xlabel("Time [s]", fontsize=8, fontweight="bold")
    ax.set_ylabel(r"$g_{\mathrm{R2}}\ [\mathrm{m/s^2}]$", fontsize=8)
    ax.set_title(title_g, fontsize=9, fontweight="bold", color=THEME["primary"])
    ax.legend(frameon=True, facecolor="white", ncol=3, fontsize=8, loc="upper right")

    # 4. Residual gravity convergence
    ax = axs[1, 1]
    apply_axes_styling(ax)
    ax.plot(
        t_p,
        res_p,
        color=THEME["danger"],
        linewidth=1.5,
        label=r"$\|\langle \vec{g} \rangle\| / g_0$",
    )
    ax.axhline(
        0.01,
        color="#4A5568",
        linestyle="--",
        linewidth=1.0,
        label=r"Target $10^{-2} g_0$",
    )
    ax.axhline(
        0.001,
        color="#718096",
        linestyle=":",
        linewidth=1.0,
        label=r"Target $10^{-3} g_0$",
    )
    ax.set_yscale("log")
    ax.set_xlabel("Time [s]", fontsize=8, fontweight="bold")
    ax.set_ylabel(r"Ratio [$\log_{10}$]", fontsize=8)
    ax.set_title(
        "Residual Gravity Convergence",
        fontsize=9,
        fontweight="bold",
        color=THEME["primary"],
    )
    ax.legend(frameon=True, facecolor="white", fontsize=8)
