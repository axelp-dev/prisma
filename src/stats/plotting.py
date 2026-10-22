"""PRISMA Plotting module: Graphical utilities for trajectory reports."""

from typing import Tuple
import matplotlib.pyplot as plt
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

    lat_centers = 0.5 * (lat_edges[:-1] + lat_edges[1:])
    cos_lat = np.cos(lat_centers)
    cos_lat[cos_lat == 0.0] = 1e-6
    area_elements = (
        (lon_edges[1] - lon_edges[0])
        * (lat_edges[1] - lat_edges[0])
        * cos_lat[None, :]
    )
    density = hist / (np.sum(hist) * area_elements)

    Lon, Lat = np.meshgrid(lon_edges, lat_edges)
    mesh = ax.pcolormesh(Lon, Lat, density.T, cmap="magma", shading="auto")
    ax.grid(True, linestyle="--", alpha=0.5, color="gray")
    ax.set_title(
        r"Surface Density of $\vec{g}_{\mathrm{R2}}$ (Mollweide Projection)",
        fontsize=10,
        fontweight="bold",
        color=THEME["primary"],
        pad=10,
    )
    cbar = plt.colorbar(
        mesh, ax=ax, orientation="horizontal", shrink=0.6, pad=0.12
    )
    cbar.set_label(
        r"Probability Density [$sr^{-1}$] (Uniform isotropic $\approx 0.08$)",
        fontsize=8,
    )
    cbar.ax.tick_params(labelsize=7)


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