# PRISMA Mathematical Formulation

This document provides the mathematical derivations, physical hypotheses, and numerical schemes governing microscale particle transport inside a biaxial Random Positioning Machine (RPM).

---

- [PRISMA Mathematical Formulation](#prisma-mathematical-formulation)
  - [1. Reference Frames \& Kinematics](#1-reference-frames--kinematics)
    - [1.1 Frame Definitions](#11-frame-definitions)
    - [1.2 Coordinate Rotation Matrix](#12-coordinate-rotation-matrix)
    - [1.3 Instantaneous Angular Velocity \& Acceleration](#13-instantaneous-angular-velocity--acceleration)
  - [2. Dynamic Force Balance in Non-Inertial Frame](#2-dynamic-force-balance-in-non-inertial-frame)
    - [2.1 Viscous Drag: Stokes' Law](#21-viscous-drag-stokes-law)
    - [2.2 Generalized Buoyancy \& Fictitious Non-Inertial Forces](#22-generalized-buoyancy--fictitious-non-inertial-forces)
    - [2.3 Hydrodynamic Added Mass Effect](#23-hydrodynamic-added-mass-effect)
    - [2.4 Synthesis: Second Newton's Law in $\\mathcal{R}\_2$](#24-synthesis-second-newtons-law-in-mathcalr_2)
  - [3. The Overdamped Stokes Regime ($Re\_p \\ll 1$)](#3-the-overdamped-stokes-regime-re_p-ll-1)
    - [3.1 Normalization and Dimensionless Coefficients](#31-normalization-and-dimensionless-coefficients)
    - [3.2 Asymptotic Reduction to First-Order Dynamics](#32-asymptotic-reduction-to-first-order-dynamics)
  - [4. Cytoskeletal Elastic Coupling ($\\vec{F}_{\\text{ext}} = \\vec{F}_{\\text{elast}}$)](#4-cytoskeletal-elastic-coupling-vecftextext--vecftextelast)
    - [4.1 Kelvin-Voigt Filament Damping](#41-kelvin-voigt-filament-damping)
    - [4.2 Elimination of Virtual Mass in Creeping Flow](#42-elimination-of-virtual-mass-in-creeping-flow)
    - [4.3 Analytical Static Benchmark](#43-analytical-static-benchmark)
  - [5. Numerical Integration Scheme (Explicit RK4)](#5-numerical-integration-scheme-explicit-rk4)
    - [5.1 Integration Step](#51-integration-step)

---

## 1. Reference Frames & Kinematics

Modeling cellular or colloidal suspensions in a Random Positioning Machine requires establishing the kinematic relationships across multiple rotating reference frames. The primary objective of the RPM is to continuously randomize the apparent orientation of the static gravitational vector relative to the sample frame, driving its time-averaged value toward zero.

### 1.1 Frame Definitions

- **$\mathcal{R}_0 = (O; \vec{x}_0, \vec{y}_0, \vec{z}_0)$ (Laboratory Frame)**: Inertial reference frame. The static terrestrial gravity vector is:
  $$\vec{g}_0 = \begin{pmatrix} 0 \\ 0 \\ -g \end{pmatrix}_{\mathcal{R}_0} \quad \text{with } g = 9.81\text{ m/s}^2$$
- **$\mathcal{R}_1$ (Outer Frame / Tilt)**: Rotates by angle $\theta_2$ around the horizontal axis $\vec{y}_0$.
- **$\mathcal{R}_2 = (O; \vec{x}_2, \vec{y}_2, \vec{z}_2)$ (Inner Frame / Sample Cuvette)**: Rotates by angle $\theta_1$ around the gimbal axis $\vec{z}_1$ (coinciding with $\vec{z}_0$ at rest $\theta_1 = \theta_2 = 0$).

### 1.2 Coordinate Rotation Matrix

The complete orientation transformation from $\mathcal{R}_0$ (lab) to $\mathcal{R}_2$ (sample) is governed by the canonical sequence:
$$R = R_z(\theta_1) R_y(-\theta_2)$$

> **Convention note:** In standard right-handed kinematics consistent with `CanonicalTwoAxis`, the tilt rotation around $\vec{y}_0$ is parameterized as $R_y(-\theta_2)$ so that at rest ($\theta_1 = \theta_2 = 0$), the gravity vector points strictly along $-\vec{z}_2$.

Evaluating the matrix product:
$$\begin{align*} R &=  \begin{pmatrix} \cos\theta_1 & -\sin\theta_1 & 0 \\ \sin\theta_1 & \cos\theta_1 & 0 \\ 0 & 0 & 1 \end{pmatrix} \begin{pmatrix} \cos\theta_2 & 0 & -\sin\theta_2 \\ 0 & 1 & 0 \\ \sin\theta_2 & 0 & \cos\theta_2 \end{pmatrix} \\ &=  \begin{pmatrix} \cos\theta_1 \cos\theta_2 & -\sin\theta_1 & -\cos\theta_1 \sin\theta_2 \\ \sin\theta_1 \cos\theta_2 & \cos\theta_1 & -\sin\theta_1 \sin\theta_2 \\ \sin\theta_2 & 0 & \cos\theta_2 \end{pmatrix} \end{align*}$$

The apparent gravity vector $\vec{g}_{\mathcal{R}_2}(t)$ experienced in the moving sample frame is:
$$\vec{g}_{\mathcal{R}_2}(t) = R(t) \vec{g}_0 = g \begin{pmatrix} \cos\theta_1 \sin\theta_2 \\ \sin\theta_1 \sin\theta_2 \\ -\cos\theta_2 \end{pmatrix}$$

### 1.3 Instantaneous Angular Velocity & Acceleration

Expressed in the moving frame $\mathcal{R}_2$, the angular velocity vector $\vec{\Omega}_{\mathcal{R}_2}$ reads:
$$\vec{\Omega}_{\mathcal{R}_2} = \begin{pmatrix} -\dot{\theta}_2 \sin\theta_1 \\ \dot{\theta}_2 \cos\theta_1 \\ \dot{\theta}_1 \end{pmatrix}_{\mathcal{R}_2}$$

The instantaneous angular acceleration is computed via numerical differentiation:
$$\dot{\vec{\Omega}}_{\mathcal{R}_2} = \frac{\mathrm{d}\vec{\Omega}_{\mathcal{R}_2}}{\mathrm{d}t}$$

> **Physical note:** The derivative $\dot{\vec{\Omega}}_{\mathcal{R}_2}$ governs the fictitious Euler force, acting perpendicularly to position whenever motor velocities vary.

---

## 2. Dynamic Force Balance in Non-Inertial Frame

Consider a spherical particle of radius $R$ and density $\rho_p$ suspended in a fluid of density $\rho_f$ and dynamic viscosity $\mu$. The motion of the particle center of mass $\vec{r}(t)$ is evaluated in the rotating sample frame $\mathcal{R}_2$.

### 2.1 Viscous Drag: Stokes' Law

The particle Reynolds number $\text{Re}_p$ compares fluid inertial forces to viscous shear forces:
$$\text{Re}_p = \frac{\rho_f \|\vec{v}\| (2R)}{\mu}$$

> **Laminar Flow Hypothesis:** Inside a microscale container or cellular cytoplasm, velocities and length scales are microscopic ($\text{Re}_p \ll 0.1$), ensuring a strictly laminar, creeping flow regime (creeping Stokes flow).

Under this hypothesis, boundary layer separation and turbulence are absent. The viscous resistance exerted by the surrounding fluid on the moving sphere is given by Stokes' drag law:
$$\vec{F}_d = - 6 \pi \mu R \, \vec{v}$$

where:
- $\mu$ is the fluid dynamic viscosity ($\text{Pa}\cdot\text{s} = \text{kg}\cdot\text{m}^{-1}\cdot\text{s}^{-1}$),
- $R$ is the particle radius ($\text{m}$),
- $\vec{v} = \frac{\mathrm{d}\vec{r}}{\mathrm{d}t}$ is the particle velocity relative to the fluid in $\mathcal{R}_2$.

### 2.2 Generalized Buoyancy & Fictitious Non-Inertial Forces

**Refactor.** Because the frame $\mathcal{R}_2$ rotates with angular velocity $\vec{\Omega}$ and angular acceleration $\dot{\vec{\Omega}}$, any body inside it experiences apparent acceleration fields. We define the total apparent kinematic acceleration vector $\vec{a}_{\text{app}}$ as:
$$\vec{a}_{\text{app}}(\vec{r}, t) = \vec{g}_{\mathcal{R}_2}(t) - \vec{\Omega} \times (\vec{\Omega} \times \vec{r}) - \dot{\vec{\Omega}} \times \vec{r}$$

This vector gathers:
- The apparent static gravity $\vec{g}_{\mathcal{R}_2}(t)$,
- The centrifugal acceleration $-\vec{\Omega} \times (\vec{\Omega} \times \vec{r})$,
- The Euler angular acceleration $-\dot{\vec{\Omega}} \times \vec{r}$.

**Fictitious Forces.** Applying Newton's mechanics in the non-inertial frame $\mathcal{R}_2$ produces body forces on the particle mass $m_p$:

$$
    \vec{F}_{\text{inertial, } p} = m_p \, \vec{a}_{\text{app}}(\vec{r}, t) - 2 m_p \left( \vec{\Omega} \times \frac{\mathrm{d}\vec{r}}{\mathrm{d}t} \right)
$$
where the last term is the complementary Coriolis force.

**Generalized Archimedes Buoyancy.** The fluid surrounding the particle also undergoes the acceleration field $\vec{a}_{\text{app}}$, creating a hydrostatic/dynamic pressure gradient throughout the medium. Integrating this pressure field over the sphere surface yields the generalized buoyancy force:
$$
    \vec{F}_b = - m_f \, \vec{a}_{\text{app}}(\vec{r}, t)
$$
where $m_f = \rho_f V_p$ is the mass of the displaced fluid ($V_p = \frac{4}{3}\pi R^3$).

**Net Effective Driving Force.** Combining the non-Coriolis body force with generalized buoyancy yields the net buoyant driving force:
$$\vec{F}_e = \vec{F}_{\text{inertial, } p}^{\text{drive}} + \vec{F}_b = (m_p - m_f) \, \vec{a}_{\text{app}}(\vec{r}, t) = (\rho_p - \rho_f) V_p \, \vec{a}_{\text{app}}(\vec{r}, t)$$

> **Sedimentation Criterion:**
> - If $\rho_p > \rho_f$, the net density contrast is positive: the inclusion sediments along the apparent field $\vec{a}_{\text{app}}$.
> - If $\rho_p < \rho_f$, the inclusion floats against $\vec{a}_{\text{app}}$.
> - If $\rho_p = \rho_f$ (neutral buoyancy), $\vec{F}_e = \vec{0}$, suppressing sedimentation entirely.

### 2.3 Hydrodynamic Added Mass Effect

When a solid body accelerates relative to a surrounding fluid, it must displace and accelerate an adjacent volume of fluid. The kinetic energy transmitted to the unbounded fluid is:
$$
    E_{\text{c, fluid}} = \frac{1}{2} \int_{\mathbb{R}^3 \setminus \mathcal{V}_p} \rho_f \|\vec{u}_f\|^2 \, \mathrm{d}V = \frac{1}{2} \left( \frac{1}{2} \rho_f V_p \right) \|\vec{v}\|^2
$$

By identification with $E_c = \frac{1}{2} m_{\text{add}} \|\vec{v}\|^2$, the hydrodynamic added mass for an unconfined sphere is:
$$
    m_{\text{add}} = \frac{1}{2} \rho_f V_p = \frac{1}{2} m_f
$$

The reactive inertial resistance exerted by the displaced fluid against particle acceleration is therefore:
$$
    \vec{F}_{\text{added mass}} = - m_{\text{add}} \frac{\mathrm{d}^2\vec{r}}{\mathrm{d}t^2} = -\frac{1}{2} m_f \frac{\mathrm{d}^2\vec{r}}{\mathrm{d}t^2}.
$$

### 2.4 Synthesis: Second Newton's Law in $\mathcal{R}_2$

The total hydrodynamic force exerted by the fluid on the particle is:
$$
    \begin{align*}
        \vec{F}_{\text{fluid}\to p} &= \vec{F}_b + \vec{F}_d + \vec{F}_{\text{added mass}} \\
        &= -m_f \vec{a}_{\text{app}} - 6\pi\mu R \frac{\mathrm{d}\vec{r}}{\mathrm{d}t} - \frac{1}{2}m_f \frac{\mathrm{d}^2\vec{r}}{\mathrm{d}t^2}
    \end{align*}
$$

Applying Newton's second law in $\mathcal{R}_2$ along with potential external forces $\vec{F}_{\text{ext}}$ (e.g. cytoskeletal tethering):
$$
    m_p \frac{\mathrm{d}^2\vec{r}}{\mathrm{d}t^2} = \vec{F}_{\text{fluid}\to p} - 2 m_p \left( \vec{\Omega} \times \frac{\mathrm{d}\vec{r}}{\mathrm{d}t} \right) + m_p \vec{a}_{\text{app}} + \vec{F}_{\text{ext}}
$$

Substituting $\vec{F}_{\text{fluid}\to p}$:
$$
    m_p \frac{\mathrm{d}^2\vec{r}}{\mathrm{d}t^2} + \frac{1}{2}m_f \frac{\mathrm{d}^2\vec{r}}{\mathrm{d}t^2} = -6\pi\mu R \frac{\mathrm{d}\vec{r}}{\mathrm{d}t} + (m_p - m_f) \vec{a}_{\text{app}}(\vec{r}, t) - 2 m_p \left( \vec{\Omega} \times \frac{\mathrm{d}\vec{r}}{\mathrm{d}t} \right) + \vec{F}_{\text{ext}}
$$

Defining the effective virtual mass $m^* = m_p + \frac{1}{2}m_f = V_p (\rho_p + \frac{1}{2}\rho_f)$, we arrive at the complete dynamic momentum balance:

$$ 
    \begin{align*}
        m^* \frac{\mathrm{d}^2\vec{r}}{\mathrm{d}t^2} &= -6\pi\mu R \frac{\mathrm{d}\vec{r}}{\mathrm{d}t} \\ 
        &+ (m_p - m_f)\left( \vec{g}_{\mathcal{R}_2}(t) - \vec{\Omega} \times (\vec{\Omega} \times \vec{r}) - \dot{\vec{\Omega}} \times \vec{r} \right) \\
        &- 2 m_p \left( \vec{\Omega} \times \frac{\mathrm{d}\vec{r}}{\mathrm{d}t} \right) \\
        &+ \vec{F}_{\text{ext}}.
    \end{align*}
$$

---

## 3. The Overdamped Stokes Regime ($Re_p \ll 1$)

### 3.1 Normalization and Dimensionless Coefficients

Dividing the complete momentum balance from Section 2 by the virtual mass $m^* = V_p (\rho_p + \frac{1}{2}\rho_f)$ yields:
$$
    \frac{\mathrm{d}^2\vec{r}}{\mathrm{d}t^2} = -\frac{6\pi\mu R}{m^*} \frac{\mathrm{d}\vec{r}}{\mathrm{d}t} + \frac{m_p - m_f}{m^*} \vec{a}_{\text{app}}(\vec{r}, t) - 2 \frac{m_p}{m^*} \left( \vec{\Omega} \times \frac{\mathrm{d}\vec{r}}{\mathrm{d}t} \right) + \frac{\vec{F}_{\text{ext}}}{m^*}
$$

We identify the characteristic timescales and dimensionless parameters:
- **Viscous relaxation timescale ($\tau_v$):**
  $$\frac{6\pi\mu R}{m^*} = \frac{6\pi\mu R}{\frac{4}{3}\pi R^3 (\rho_p + \frac{1}{2}\rho_f)} = \frac{9}{2} \frac{\mu}{R^2 (\rho_p + \frac{1}{2}\rho_f)} \equiv \frac{1}{\tau_v}$$
  $$\implies \tau_v = \frac{2}{9} \frac{R^2 (\rho_p + \frac{1}{2}\rho_f)}{\mu} = \frac{m^*}{6\pi\mu R}$$
- **Buoyancy / density contrast factor ($\beta$):**
  $$\beta = \frac{m_p - m_f}{m^*} = \frac{\rho_p - \rho_f}{\rho_p + \frac{1}{2}\rho_f}$$
- **Coriolis factor ($\gamma$):**
  $$\gamma = \frac{m_p}{m^*} = \frac{\rho_p}{\rho_p + \frac{1}{2}\rho_f}$$

The normalized governing equation of motion is then: 
$$
    \frac{\mathrm{d}^2\vec{r}}{\mathrm{d}t^2} = -\frac{1}{\tau_v} \frac{\mathrm{d}\vec{r}}{\mathrm{d}t} + \beta \, \vec{a}_{\text{app}}(\vec{r}, t) - 2\gamma \left( \vec{\Omega} \times \frac{\mathrm{d}\vec{r}}{\mathrm{d}t} \right) + \frac{\vec{F}_{\text{ext}}}{m^*}
$$

### 3.2 Asymptotic Reduction to First-Order Dynamics

In microscale transport (e.g., cell organelles or dense micro-beads in viscous glycerol), the viscous relaxation timescale satisfies:
$$
    \tau_v \sim 10^{-6}\text{ s to } 10^{-4}\text{ s} \ll T_{\text{RPM}} \sim 1\text{ to } 10\text{ s}
$$

Because $\tau_v$ is orders of magnitude smaller than the mechanical period of the RPM:
1. Relative particle acceleration vanishes quasi-instantaneously ($\frac{\mathrm{d}^2\vec{r}}{\mathrm{d}t^2} \approx \vec{0}$).
2. The non-inertial Coriolis force is dominated by viscous shear drag:
   $$\frac{\Vert{}\vec{F}_{\text{coriolis}}\Vert{}}{\Vert{}\vec{F}_d\Vert{}} \sim \frac{2 m_p \Omega v}{6\pi\mu R v} \sim \tau_v \Omega \ll 1$$
3. Inertial acceleration and Coriolis terms drop out, reducing the balance to an instantaneous equilibrium between viscous drag, buoyant driving forces, and external constraints:
   $$\vec{0} = -\frac{1}{\tau_v} \frac{\mathrm{d}\vec{r}}{\mathrm{d}t} + \beta \, \vec{a}_{\text{app}}(\vec{r}, t) + \frac{\vec{F}_{\text{ext}}}{m^*}$$

Multiplying through by $\tau_v$ resolves the terminal drift velocity:
$$
    \frac{\mathrm{d}\vec{r}}{\mathrm{d}t} = \vec{v}_{\text{limit}}(\vec{r}, t) = \tau_v \beta \, \vec{a}_{\text{app}}(\vec{r}, t) + \frac{\tau_v}{m^*} \vec{F}_{\text{ext}}
$$

---

## 4. Cytoskeletal Elastic Coupling ($\vec{F}_{\text{ext}} = \vec{F}_{\text{elast}}$)

### 4.1 Kelvin-Voigt Filament Damping

In cellular mechanotransduction (such as statolith motion in plant statocytes), inclusions are anchored to an intracellular network of actin microfilaments. We model this tethering as an isotropic linear elastic restoring force directed toward a rest anchor $\vec{x}_0$:
$$
    \vec{F}_{\text{ext}} \equiv \vec{F}_{\text{elast}} = -k (\vec{r} - \vec{x}_0)
$$
where $k$ is the effective spring stiffness of the filament network ($\text{N/m}$).

### 4.2 Elimination of Virtual Mass in Creeping Flow

Substituting $\vec{F}_{\text{elast}}$ into the terminal velocity equation yields the coefficient:
$$\frac{\tau_v}{m^*} \vec{F}_{\text{elast}} = -\frac{\tau_v k}{m^*} (\vec{r} - \vec{x}_0)$$

Recalling the definition $\tau_v = \frac{m^*}{6\pi\mu R}$, the virtual mass $m^*$ cancels out identically:
$$\frac{\tau_v k}{m^*} = \left(\frac{m^*}{6\pi\mu R}\right) \frac{k}{m^*} = \frac{k}{6\pi\mu R}$$

We define the **viscoelastic relaxation timescale** $\tau_k$:
$$\tau_k = \frac{6\pi\mu R}{k}$$

The terminal drift equation with cytoskeletal coupling reads:
$$\frac{\mathrm{d}\vec{r}}{\mathrm{d}t} = \vec{v}_{\text{limit}}(\vec{r}, t) = \tau_v \beta \left( \vec{g}_{\mathcal{R}_2}(t) - \vec{\Omega} \times (\vec{\Omega} \times \vec{r}) - \dot{\vec{\Omega}} \times \vec{r} \right) - \frac{\vec{r} - \vec{x}_0}{\tau_k}$$

### 4.3 Analytical Static Benchmark

Under static terrestrial gravity ($\vec{g}_0 = -g\vec{e}_z$) with motors halted ($\vec{\Omega} = \vec{0}$), the equation decouples along the $z$-axis:
$$\frac{\mathrm{d}z}{\mathrm{d}t} = -\tau_v \beta g - \frac{z - z_0}{\tau_k}$$

The steady-state equilibrium position $z_{\text{eq}}$ is reached when $\frac{\mathrm{d}z}{\mathrm{d}t} = 0$:
$$z_{\text{eq}} = z_0 - \tau_k \tau_v \beta g = z_0 - \frac{(\rho_p - \rho_f) V_p g}{k} = z_0 - \frac{(m_p - m_f)g}{k}$$

The exact closed-form solution governing relaxation toward equilibrium is:
$$z(t) = z_{\text{eq}} + (z(0) - z_{\text{eq}}) e^{-t / \tau_k}$$
This analytical solution serves as the primary verification unit test for the solver (`tests/test_solver.py`).

---

<!-- ## 5. Geometric Boundary Enforcement (Cellular Confinement)

Let the inclusion move inside a closed spherical boundary (cell membrane or cuvette) of radius $R_{\text{cell}}$ centered at $\vec{c}$ in $\mathcal{R}_2$. 
Because the inclusion is a rigid sphere of radius $R$, its center of mass is strictly constrained within an effective spherical domain of radius:
$$R_{\text{max}} = R_{\text{cell}} - R$$

At any position $\vec{r}$, the outward surface normal is:
$$\vec{n} = \frac{\vec{r} - \vec{c}}{\Vert{}\vec{r} - \vec{c}\Vert{}}$$

### 5.1 Low-Reynolds Inelastic Contact Law

In microscale Stokes flow, the interstitial fluid film between approaching solid boundaries creates a singular lubrication resistance diverging as $\mathcal{O}(1/h)$ (where $h$ is the film thickness). Consequently:
- Mechanical rebounds are suppressed by lubrication dissipation ($e = 0$).
- When driven against the boundary, the particle slips tangentially along the membrane without penetrating the wall.

### 5.2 Projection Algorithm

A collision/contact event occurs if the particle position exceeds the boundary while moving outward:
$$\Vert{}\vec{r} - \vec{c}\Vert{} \ge R_{\text{max}} \quad \text{and} \quad \vec{v} \cdot \vec{n} > 0$$

Upon detecting penetration:
1. **Geometric Relocation (Non-Penetration Constraint):**
   $$\vec{r} \leftarrow \vec{c} + R_{\text{max}} \vec{n}$$
2. **Normal Velocity Annihilation:**
   Decomposing velocity into normal and tangential components ($\vec{v} = \vec{v}_n + \vec{v}_t$ with $\vec{v}_n = (\vec{v} \cdot \vec{n})\vec{n}$):
   $$\vec{v} \leftarrow \vec{v} - (\vec{v} \cdot \vec{n})\vec{n} = \vec{v}_t$$

--- -->

## 5. Numerical Integration Scheme (Explicit RK4)

The first-order autonomous system $\frac{\mathrm{d}\vec{r}}{\mathrm{d}t} = \vec{v}_{\text{limit}}(\vec{r}, t)$ is solved over discrete time steps $\Delta t = t_{n+1} - t_n$ using an explicit 4th-order Runge-Kutta scheme.

### 5.1 Integration Step

$$\begin{aligned} \vec{k}_1 &= \vec{v}_{\text{limit}}(\vec{r}_n, t_n) \\ \vec{k}_2 &= \vec{v}_{\text{limit}}\left(\vec{r}_n + \frac{\Delta t}{2}\vec{k}_1, t_n + \frac{\Delta t}{2}\right) \\ \vec{k}_3 &= \vec{v}_{\text{limit}}\left(\vec{r}_n + \frac{\Delta t}{2}\vec{k}_2, t_n + \frac{\Delta t}{2}\right) \\ \vec{k}_4 &= \vec{v}_{\text{limit}}(\vec{r}_n + \Delta t \, \vec{k}_3, t_{n+1}) \\ \vec{r}_{n+1}^* &= \vec{r}_n + \frac{\Delta t}{6} (\vec{k}_1 + 2\vec{k}_2 + 2\vec{k}_3 + \vec{k}_4) \end{aligned}$$

Kinematic variables at half-steps ($t_n + \frac{\Delta t}{2}$) are obtained via linear interpolation:
$$\vec{g}_{\text{mid}} = \frac{1}{2}(\vec{g}_n + \vec{g}_{n+1}), \quad \vec{\Omega}_{\text{mid}} = \frac{1}{2}(\vec{\Omega}_n + \vec{\Omega}_{n+1}), \quad \dot{\vec{\Omega}}_{\text{mid}} = \frac{1}{2}(\dot{\vec{\Omega}}_n + \dot{\vec{\Omega}}_{n+1})$$

<!-- ### 5.2 Operator Splitting for Boundary Conditions

To maintain 4th-order local convergence during unconstrained drift while strictly guaranteeing physical non-penetration:
1. The elastic restoring term $-\frac{\vec{r} - \vec{x}_0}{\tau_k}$ is evaluated inside each Runge-Kutta intermediate evaluation ($\vec{k}_1, \vec{k}_2, \vec{k}_3, \vec{k}_4$).
2. The boundary projection is applied once per full step on the tentative state $\vec{r}_{n+1}^*$:
   $$\vec{r}_{n+1} = \begin{cases} \vec{c} + R_{\text{max}} \frac{\vec{r}_{n+1}^* - \vec{c}}{\Vert{}\vec{r}_{n+1}^* - \vec{c}\Vert{}}, & \text{if } \Vert{}\vec{r}_{n+1}^* - \vec{c}\Vert{} > R_{\text{max}} \\ \vec{r}_{n+1}^*, & \text{otherwise} \end{cases}$$
3. Post-integration particle velocities and instant Reynolds numbers are evaluated using central finite differences:
   $$\vec{v}_n = \frac{\vec{r}_{n+1} - \vec{r}_{n-1}}{2 \Delta t}, \quad Re_p(t_n) = \frac{2 R \rho_f \Vert{}\vec{v}_n\Vert{}}{\mu}$$ -->