"""PRISMA Plotting module: Graphical utilities for trajectory reports."""

from typing import Tuple
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np

THEME = {
    "primary": "#1A365D",
    "secondary": "#2B6CB0",
    "accent": "#DD6B20",
    "text": "#2D3748",
    "bg": "#F7FAFC",
    "grid": "#E2E8F0",
    "border": "#CBD5E0",
    "danger": "#E53E3E",
    "success": "#38A169",
}



def render_particle_3d_confinement(
    positions: np.ndarray,
    x0: np.ndarray,
    r_tube: float,
    timestamps: np.ndarray,
    ax: plt.Axes,
) -> None:
    """Render 3D particle path enclosed within transparent spherical tube."""
    # Scale coordinates to readable units (mm or um)
    scale = 1e3 if r_tube >= 1e-3 else 1e6
    unit_str = "mm" if scale == 1e3 else r"\mu\mathrm{m}"

    pos_s = positions * scale
    x0_s = x0 * scale
    r_s = r_tube * scale

    # 1. Wireframe boundary sphere
    phi = np.linspace(0, 2 * np.pi, 24)
    theta = np.linspace(0, np.pi, 12)
    xs = r_s * np.outer(np.cos(phi), np.sin(theta))
    ys = r_s * np.outer(np.sin(phi), np.sin(theta))
    zs = r_s * np.outer(np.ones_like(phi), np.cos(theta))
    ax.plot_wireframe(xs, ys, zs, color="#A0AEC0", alpha=0.8, linewidth=0.5)

    # 2. Chronological trajectory scatter
    sc = ax.scatter(
        pos_s[:, 0],
        pos_s[:, 1],
        pos_s[:, 2],
        c=timestamps,
        cmap="coolwarm",
        s=4,
        alpha=0.75,
        rasterized=True,
    )

    ax.plot(
        pos_s[:, 0],
        pos_s[:, 1],
        pos_s[:, 2],
        color="gray",
        linewidth=0.8,
        alpha=0.6,
        linestyle="-",
    )

    # 3. Initial/Anchor position
    ax.scatter(
        [x0_s[0]],
        [x0_s[1]],
        [x0_s[2]],
        color=THEME["accent"],
        s=40,
        marker="^",
        label=r"Anchor $\vec{x}_0$",
    )

    ax.set_box_aspect([1, 1, 1])

    # Set wireframe zoom
    all_pts = np.vstack([pos_s, x0_s.reshape(1, 3)])
    center = np.mean(all_pts, axis=0)
    extent = np.max(np.abs(all_pts - center)) * 1.15
    extent = max(extent, 1e-6)
    ax.set_xlim([center[0] - extent, center[0] + extent])
    ax.set_ylim([center[1] - extent, center[1] + extent])
    ax.set_zlim([center[2] - extent, center[2] + extent])

    ax.set_xlabel(f"$X\\ [{unit_str}]$", fontsize=8, labelpad=2)
    ax.set_ylabel(f"$Y\\ [{unit_str}]$", fontsize=8, labelpad=2)
    ax.set_zlabel(f"$Z\\ [{unit_str}]$", fontsize=8, labelpad=2)
    ax.set_title(
        f"Particle 3D Path ({unit_str})",
        fontsize=10,
        fontweight="bold",
        color=THEME["primary"],
        pad=8,
    )
    plt.colorbar(sc, ax=ax, shrink=0.55, pad=0.08, label="Time [s]")


def render_temporal_dynamics(metrics: dict, fig: plt.Figure) -> None:
    """Populate Page 2 with coordinates, velocities, boundary distance, and Re_p."""
    axs = fig.subplots(2, 2)
    t = metrics["timestamp"]
    scale = metrics["scale"]
    unit_str = metrics["unit_str"]

    # 1. Position coordinates
    ax = axs[0, 0]
    apply_axes_styling(ax)
    pos_s = metrics["positions"] * scale
    ax.plot(t, pos_s[:, 0], label=r"$x(t)$", color="#3182CE", linewidth=1.0)
    ax.plot(t, pos_s[:, 1], label=r"$y(t)$", color="#DD6B20", linewidth=1.0)
    ax.plot(t, pos_s[:, 2], label=r"$z(t)$", color="#38A169", linewidth=1.0)
    ax.axhline(0, color="gray", linestyle=":", linewidth=0.8)
    ax.set_ylabel(f"Position [{unit_str}]", fontsize=8, fontweight="bold")
    ax.set_title("Coordinate Trajectories", fontsize=9, fontweight="bold", color=THEME["primary"])
    ax.legend(frameon=True, facecolor="white", ncol=3, fontsize=8)

    # 2. Velocity components
    ax = axs[0, 1]
    apply_axes_styling(ax)
    vel_s = metrics["velocities"] * scale
    ax.plot(t, vel_s[:, 0], label=r"$v_x(t)$", color="#3182CE", linewidth=1.0)
    ax.plot(t, vel_s[:, 1], label=r"$v_y(t)$", color="#DD6B20", linewidth=1.0)
    ax.plot(t, vel_s[:, 2], label=r"$v_z(t)$", color="#38A169", linewidth=1.0)
    ax.set_ylabel(f"Velocity [{unit_str}/s]", fontsize=8, fontweight="bold")
    ax.set_title("Hydrodynamic Velocity", fontsize=9, fontweight="bold", color=THEME["primary"])
    ax.legend(frameon=True, facecolor="white", ncol=3, fontsize=8)

    # 3. Radial distance vs confinement limit
    ax = axs[1, 0]
    apply_axes_styling(ax)
    r_dist_s = metrics["radial_distances"] * scale
    r_tube_s = metrics["r_tube"] * scale
    ax.plot(t, r_dist_s, color=THEME["secondary"], linewidth=1.2, label=r"$\|\vec{r}(t)\|$")
    ax.axhline(r_tube_s, color=THEME["danger"], linestyle="--", linewidth=1.2, label=r"Boundary $R_{\mathrm{tube}}$")
    ax.set_xlabel("Time [s]", fontsize=8, fontweight="bold")
    ax.set_ylabel(f"Distance [{unit_str}]", fontsize=8, fontweight="bold")
    ax.set_title("Cell/Tube Confinement Proximity", fontsize=9, fontweight="bold", color=THEME["primary"])
    ax.legend(frameon=True, facecolor="white", fontsize=8)

    # 4. Instantaneous Reynolds number series
    ax = axs[1, 1]
    apply_axes_styling(ax)
    ax.plot(t, metrics["reynolds"], color="#4A5568", linewidth=1.1, label=r"$Re_p(t)$")
    ax.axhline(0.1, color=THEME["danger"], linestyle="--", linewidth=1.2, label=r"Stokes limit $Re_p = 0.1$")
    ax.set_yscale("log")
    ax.set_xlabel("Time [s]", fontsize=8, fontweight="bold")
    ax.set_ylabel(r"$Re_p$ [$\log_{10}$]", fontsize=8, fontweight="bold")
    ax.set_title("Particle Reynolds Number History", fontsize=9, fontweight="bold", color=THEME["primary"])
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
    ax.plot(
        metrics["fft_freqs_g"],
        metrics["fft_amp_g"],
        color=THEME["accent"],
        linewidth=1.0,
        label=r"Forcing $g_z$ [$\mathrm{m/s^2}$]",
    )
    ax.plot(
        metrics["fft_freqs_z"],
        metrics["fft_amp_z"] * scale,
        color=THEME["secondary"],
        linewidth=1.2,
        label=f"Response $z$ [{unit_str}]",
    )
    if metrics["tau_k_cutoff_hz"]:
        ax.axvline(
            metrics["tau_k_cutoff_hz"],
            color=THEME["danger"],
            linestyle="--",
            linewidth=1.0,
            label=f"Cutoff $f_k = {metrics['tau_k_cutoff_hz']:.2e}$ Hz",
        )
    ax.set_xlim([0, min(10.0, np.max(metrics["fft_freqs_g"]))])
    ax.set_xlabel("Frequency [Hz]", fontsize=8, fontweight="bold")
    ax.set_ylabel("Amplitude", fontsize=8, fontweight="bold")
    ax.set_title("Frequency Spectra (FFT)", fontsize=9, fontweight="bold", color=THEME["primary"])
    ax.legend(frameon=True, facecolor="white", fontsize=7.5)

    # 2. Phase Portrait (z vs v_z)
    ax = axs[0, 1]
    apply_axes_styling(ax)
    z_s = metrics["positions"][:, 2] * scale
    vz_s = metrics["velocities"][:, 2] * scale
    ax.plot(z_s, vz_s, color=THEME["primary"], linewidth=0.6, alpha=0.8)
    ax.set_xlabel(f"Vertical Position $z$ [{unit_str}]", fontsize=8, fontweight="bold")
    ax.set_ylabel(f"Vertical Velocity $v_z$ [{unit_str}/s]", fontsize=8, fontweight="bold")
    ax.set_title("Phase Portrait ($z$ vs $v_z$)", fontsize=9, fontweight="bold", color=THEME["primary"])

    # 3. Radial distance histogram
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
        linewidth=0.5,
        alpha=0.75,
    )
    ax.axvline(r_tube_s, color=THEME["danger"], linestyle="--", linewidth=1.2, label=r"Boundary $R_{\mathrm{tube}}$")
    ax.set_xlabel(f"Radial Distance $r$ [{unit_str}]", fontsize=8, fontweight="bold")
    ax.set_ylabel("Probability Density", fontsize=8, fontweight="bold")
    ax.set_title("Radial Distribution Density", fontsize=9, fontweight="bold", color=THEME["primary"])
    ax.legend(frameon=True, facecolor="white", fontsize=8)

    # 4. Orthogonal Transverse Orbit (x vs y)
    ax = axs[1, 1]
    apply_axes_styling(ax)
    pos_s = metrics["positions"] * scale
    ax.plot(pos_s[:, 0], pos_s[:, 1], color=THEME["secondary"], linewidth=0.8, alpha=0.7)
    circle = plt.Circle((0, 0), r_tube_s, color="#A0AEC0", fill=False, linestyle="--", linewidth=1.0)
    ax.add_patch(circle)
    ax.set_aspect("equal", "box")
    ax.set_xlim([-r_tube_s * 1.1, r_tube_s * 1.1])
    ax.set_ylim([-r_tube_s * 1.1, r_tube_s * 1.1])
    ax.set_xlabel(f"$x$ [{unit_str}]", fontsize=8, fontweight="bold")
    ax.set_ylabel(f"$y$ [{unit_str}]", fontsize=8, fontweight="bold")
    ax.set_title("Transverse Orbit ($x, y$)", fontsize=9, fontweight="bold", color=THEME["primary"])

    fig.tight_layout()


def apply_axes_styling(ax: plt.Axes) -> None:
    """Apply unified styling across 2D plots."""
    ax.set_facecolor(THEME["bg"])
    ax.grid(True, linestyle="--", linewidth=0.6, color=THEME["grid"], alpha=0.8)
    ax.tick_params(colors=THEME["text"], labelsize=8)
    for spine in ax.spines.values():
        spine.set_color(THEME["border"])
        spine.set_linewidth(0.8)


def render_unit_sphere_trajectory(
    g_values: np.ndarray, timestamps: np.ndarray, ax: plt.Axes
) -> None:
    """Render gravity path over the 3D unit sphere."""
    phi = np.linspace(0, 2 * np.pi, 26)
    theta = np.linspace(0, np.pi, 13)
    xs = np.outer(np.cos(phi), np.sin(theta))
    ys = np.outer(np.sin(phi), np.sin(theta))
    zs = np.outer(np.ones_like(phi), np.cos(theta))
    ax.plot_wireframe(xs, ys, zs, color="#A0AEC0", alpha=0.25, linewidth=0.5)

    norms = np.linalg.norm(g_values, axis=1, keepdims=True)
    norms[norms == 0.0] = 1.0
    u = g_values / norms

    sc = ax.scatter(
        u[:, 0],
        u[:, 1],
        u[:, 2],
        c=timestamps,
        cmap="viridis",
        s=6,
        alpha=0.8,
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
    bins: Tuple[int, int] = (72, 36),
) -> None:
    """Render surface probability density in Mollweide equal-area projection."""
    lon_edges = np.linspace(-np.pi, np.pi, bins[0] + 1)
    lat_edges = np.linspace(-np.pi / 2, np.pi / 2, bins[1] + 1)
    hist, _, _ = np.histogram2d(lon, lat, bins=[lon_edges, lat_edges])

    # 1. Calcul d'aire élémentaire sécurisé aux pôles
    lat_centers = 0.5 * (lat_edges[:-1] + lat_edges[1:])
    # Évite l'explosion numérique sur les pôles extrêmes
    cos_lat = np.clip(np.cos(lat_centers), 1e-3, 1.0)
    d_lon = lon_edges[1] - lon_edges[0]
    d_lat = lat_edges[1] - lat_edges[0]
    area_elements = d_lon * d_lat * cos_lat[None, :]

    total_samples = np.sum(hist)
    if total_samples > 0:
        density = hist / (total_samples * area_elements)
    else:
        density = np.zeros_like(hist)

    # 2. Masquage des zéros pour laisser le fond propre et visible
    density_plot = density.T
    density_masked = np.ma.masked_where(density_plot == 0.0, density_plot)

    # 3. Écrêtage robuste (percentile 98) pour éviter l'écrasement dynamique
    non_zero_vals = density[density > 0]
    if len(non_zero_vals) > 0:
        v_max = float(np.percentile(non_zero_vals, 98))
        v_max = max(v_max, 0.16)  # Au moins le double de la valeur uniforme (~0.08)
    else:
        v_max = 0.16

    # 4. Fond de carte neutre clair
    ax.set_facecolor("#F8FAFC")
    ax.grid(True, linestyle=":", alpha=0.6, color="#A0AEC0", linewidth=0.7)

    Lon, Lat = np.meshgrid(lon_edges, lat_edges)

    # Colormap contrastée (YlOrRd : jaune clair -> orange -> rouge vif)
    # ou "viridis" / "plasma" sans le noir
    cmap = plt.cm.YlOrRd.copy()
    cmap.set_bad(color="#F8FAFC")  # Couleur des cellules vides (masquées)

    # Échelle avec gamma doux (PowerNorm) pour rehausser les densités faibles
    norm = mcolors.PowerNorm(gamma=0.6, vmin=0.0, vmax=v_max)

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
        color=THEME.get("primary", "#1A365D"),
        pad=10,
    )

    # 5. Colorbar claire
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
    # Repère visuel de la valeur uniforme théorique (0.08)
    if v_max >= 0.08:
        cbar.ax.axvline(0.08, color="#2B6CB0", linestyle="--", linewidth=1.2)

def render_motor_kinematics(metrics: dict, fig: plt.Figure) -> None:
    """Populate figure with gimbal positions, velocities, apparent gravity, and convergence."""
    axs = fig.subplots(2, 2)
    t = metrics["timestamp"]

    # 1. Motor positions
    ax = axs[0, 0]
    apply_axes_styling(ax)
    ax.plot(
        t,
        metrics["theta1"],
        label=r"$\theta_1$ (Inner gimbal)",
        color=THEME["secondary"],
        linewidth=1.2,
    )
    ax.plot(
        t,
        metrics["theta2"],
        label=r"$\theta_2$ (Outer gimbal)",
        color=THEME["accent"],
        linewidth=1.2,
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
        t,
        metrics["omega1"],
        label=r"$\omega_1 = \dot{\theta}_1$",
        color=THEME["secondary"],
        linewidth=1.2,
    )
    ax.plot(
        t,
        metrics["omega2"],
        label=r"$\omega_2 = \dot{\theta}_2$",
        color=THEME["accent"],
        linewidth=1.2,
    )
    ax.plot(
        t,
        metrics["omega_norm_series"],
        label=r"$\|\vec{\Omega}_{\mathrm{R2}}\|$ total",
        color=THEME["text"],
        linestyle=":",
        linewidth=1.0,
    )
    ax.set_ylabel("Velocity [rad/s]", fontsize=8, fontweight="bold")
    ax.set_title(
        "Angular Velocities",
        fontsize=9,
        fontweight="bold",
        color=THEME["primary"],
    )
    ax.legend(frameon=True, facecolor="white", fontsize=8)

    # 3. Apparent gravity components
    ax = axs[1, 0]
    apply_axes_styling(ax)
    ax.plot(
        t, metrics["g"][:, 0], label=r"$g_x$", color="#3182CE", linewidth=1.0
    )
    ax.plot(
        t, metrics["g"][:, 1], label=r"$g_y$", color="#DD6B20", linewidth=1.0
    )
    ax.plot(
        t, metrics["g"][:, 2], label=r"$g_z$", color="#38A169", linewidth=1.0
    )
    ax.axhline(0.0, color="gray", linestyle=":", linewidth=0.8)
    ax.set_xlabel("Time [s]", fontsize=8, fontweight="bold")
    ax.set_ylabel(r"$g_{\mathrm{R2}}\ [\mathrm{m/s^2}]$", fontsize=8)
    ax.set_title(
        r"Apparent Gravity Vector in $\mathrm{R}_2$",
        fontsize=9,
        fontweight="bold",
        color=THEME["primary"],
    )
    ax.legend(frameon=True, facecolor="white", ncol=3, fontsize=8)

    # 4. Residual gravity convergence
    ax = axs[1, 1]
    apply_axes_styling(ax)
    ax.plot(
        t,
        metrics["residual_norm_series"],
        color=THEME["danger"],
        linewidth=1.4,
        label=r"$\|\langle \vec{g} \rangle\| / g_0$",
    )
    ax.axhline(
        0.01,
        color="#718096",
        linestyle="--",
        linewidth=0.9,
        label=r"Target $10^{-2} g_0$",
    )
    ax.axhline(
        0.001,
        color="#A0AEC0",
        linestyle=":",
        linewidth=0.9,
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