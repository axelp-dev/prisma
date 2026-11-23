# PRISMA — Analyse des Résultats de Simulation & Interprétation Biologique

Ce document présente le cadre physique du module de simulation **PRISMA** (*Particle in Random-positioning Integrator for Simulated Microgravity Analysis*), détaille les six profils cinématiques évalués et synthétise les résultats obtenus en comparant le régime cellulaire viscoélastique (`statolith`) au régime macroscopique libre (`glycerol_bead`).

---

## 1. Modèle Physique & Architecture du Module de Simulation

Le module de simulation numérique résout la dynamique d'une particule sphérique immergée dans un fluide visqueux au sein d'une enceinte confinée soumise à une rotation bi-axiale (Random Positioning Machine — RPM).

### 1.1 Équations du Mouvement en Régime Sur-Amorti ($Re_p \ll 1$)

Dans le référentiel tournant lié à l'échantillon ($\mathcal{R}_2$), la particule de rayon $R$, de masse volumique $\rho$ et de volume $V = \frac{4}{3}\pi R^3$ est soumise à :

- **La gravité apparente** $\vec{g}_{\mathcal{R}_2}(t) = \mathbf{R}_{\mathcal{R}_0 \to \mathcal{R}_2}(t)\,\vec{g}_0$, modulée par la poussée d'Archimède via le facteur de flottabilité $\beta = 1 - \frac{\rho_f}{\rho}$.
- **Les forces d'inertie d'entraînement** : accélération centrifuge $-\vec{\Omega} \times (\vec{\Omega} \times \vec{r})$ et accélération angulaire d'Euler $-\dot{\vec{\Omega}} \times \vec{r}$.
- **La traînée visqueuse de Stokes** $\vec{F}_d = -6\pi\mu_f R\,\vec{v}$, caractérisée par le temps de relaxation inertiel $\tau_v = \frac{2 \rho R^2}{9 \mu_f}$.
- **Un rappel élastique linéaire (optionnel)** $\vec{F}_k = -k(\vec{r} - \vec{x}_0)$, modélisant l'ancrage d'un organite au réseau d'actine du cytosquelette autour de sa position d'équilibre $\vec{x}_0$, associé au temps de relaxation viscoélastique $\tau_k = \frac{6\pi\mu_f R}{k}$ et à la fréquence de coupure $f_k = \frac{1}{2\pi\tau_k}$.

À l'échelle cellulaire ou en milieu très visqueux, le nombre de Reynolds particulaire $Re_p = \frac{2 R \rho_f \lVert\vec{v}\rVert}{\mu_f}$ reste très inférieur à $0{,}1$ ($\tau_v \ll \Delta t$). L'inertie propre de la particule ($\tau_v \frac{d\vec{v}}{dt}$) devient négligeable, réduisant la dynamique à une équation différentielle ordinaire du premier ordre en régime sur-amorti :

$$\frac{d\vec{r}}{dt} = \vec{v}_{\text{lim}}(\vec{r}, t) = \tau_v \beta \left( \vec{g}_{\mathcal{R}_2}(t) - \vec{\Omega} \times (\vec{\Omega} \times \vec{r}) - \dot{\vec{\Omega}} \times \vec{r} \right) - \frac{\vec{r} - \vec{x}_0}{\tau_k}$$

### 1.2 Implémentation Numérique (`Simulation` & `RK4Overdamped`)

L'architecture logicielle repose sur trois composants découplés :

1. **`PhysicalSystem` & `SimulationConfig`** : encapsulent les propriétés de la particule, du fluide et du confinement ($R_{\text{tube}}$). Deux configurations de référence (*presets*) sont définies :
   - **`statolith`** : organite cellulaire ($R = 1{,}5\text{ µm}$, $\rho = 1500\text{ kg/m}^3$) dans un cytoplasme visqueux ($\rho_f = 1050\text{ kg/m}^3$, $\mu_f = 0{,}1\text{ Pa}\cdot\text{s}$) avec rappel élastique du cytosquelette ($k = 10^{-4}\text{ N/m}$) et rayon cellulaire $R_{\text{tube}} = 20\text{ µm}$.
   - **`glycerol_bead`** : bille macroscopique libre ($R = 1{,}5\text{ mm}$, $\rho = 1202\text{ kg/m}^3$) sans rappel élastique ($k = 0$) dans une solution de glycérol ($\rho_f = 1200\text{ kg/m}^3$, $\mu_f = 1{,}412\text{ Pa}\cdot\text{s}$) confinée dans un tube de rayon $R_{\text{tube}} = 50\text{ mm}$.
2. **Intégrateur `RK4Overdamped`** : intègre la trajectoire $\vec{r}(t)$ par la méthode de Runge-Kutta d'ordre 4 avec interpolation linéaire aux demi-pas des grandeurs cinématiques ($\vec{g}_{\mathcal{R}_2}$, $\vec{\Omega}$, $\dot{\vec{\Omega}}$).
3. **Confinement sphérique inélastique** : à chaque pas d'intégration, si $\lVert\vec{r}_{n+1}\rVert > R_{\text{tube}}$, la position est projetée radialement sur la paroi interne ($\vec{r}_{n+1} \leftarrow R_{\text{tube}} \frac{\vec{r}_{n+1}}{\lVert\vec{r}_{n+1}\rVert}$) et la composante radiale sortante de la vitesse est annulée ($v_n = \vec{v}\cdot\hat{n} = 0$), permettant à la particule de glisser tangentiellement le long de la paroi ou de redécoller lorsque la force résultante s'inverse.

---

## 2. Description des Profils Cinématiques Testés

Six lois de commande des deux cadres cardans ($\theta_1$ axe interne, $\theta_2$ axe externe) sont évaluées pour couvrir les régimes témoins, déterministes et stochastiques :

- **`static_1g` (Contrôle statique au sol)** : Les deux axes sont maintenus immobiles ($\omega_1 = \omega_2 = 0$). L'échantillon subit le vecteur gravité terrestre constant $\vec{g}_{\mathcal{R}_2} = -g_0 \vec{e}_z$, servant de référence pour quantifier la sédimentation libre ou l'élongation élastique statique.
- **`clinostat_1d` (Clinostat 2D mono-axial)** : L'axe interne est bloqué ($\omega_1 = 0$) tandis que l'axe externe tourne à vitesse angulaire constante ($\omega_2 = \pi/4\text{ rad/s} \approx 7{,}5\text{ RPM}$). La gravité apparente est moyennée uniquement dans un plan orthogonal à l'axe de rotation.
- **`centrifuge_sweep` (Rampe centrifuge asymptotique)** : Les deux axes accélèrent simultanément selon une loi exponentielle saturante $\omega_1(t) = \omega_2(t) = \omega_{\max}(1 - e^{-t/\tau})$ avec $\omega_{\max} = \pi\text{ rad/s}$ ($\sim 30\text{ RPM}$) et $\tau = 25\text{ s}$. Ce profil permet de tester l'effet des accélérations angulaires transitoires et du régime centrifuge à haute vitesse.
- **`desynchronized_sine` (Oscillations harmoniques désynchronisées)** : Chaque cadre effectue un mouvement sinusoïdal d'amplitude $\pi\text{ rad}$ à des pulsations incommensurables ($\omega_1 = 5\sqrt{2}\text{ rad/s}$, $\omega_2 = 2{,}0\text{ rad/s}$, déphasage $\phi = 15\text{ rad}$), générant une trajectoire de Lissajous bornée sur la sphère unité.
- **`constant_speed_ratio` (Rotation bi-axiale à rapport irrationnel)** : Les deux moteurs tournent en continu à vitesses angulaires constantes liées par un rapport non harmonique ($\omega_2 = 0{,}732\,\omega_1$). L'absence d'accélération angulaire ($\dot{\vec{\Omega}} = \vec{0}$) annule les forces d'Euler tout en évitant la fermeture périodique des orbites.
- **`random_walk` (Marche aléatoire stochastique 3D)** : Reproduit le mode standard des RPM commerciaux en tirant aléatoirement les vitesses et sens de rotation dans $[-\omega_{\max}, \omega_{\max}]$ ($\omega_{\max} = \pi/2\text{ rad/s} \approx 15\text{ RPM}$) à intervalles réguliers, assurant une exploration isotrope et apériodique de l'espace sphérique.

---

## 3. Bilan Comparatif des Trajectoires Simulées

- **`static_1g` (Témoin statique au sol)**
  - **Signature cinématique :** Gravité résiduelle constante égale à $1{,}00\ g_0$ et isotropie nulle ($0{,}00$).
  - **Comportement `statolith` ($k = 10^{-4}\text{ N/m}$) :** Sédimentation jusqu'à la paroi inférieure ($20\text{ µm}$).
  - **Comportement `glycerol_bead` ($k = 0$) :** Chute libre rectiligne à vitesse limite constante ($v_z \approx -6{,}95\text{ µm/s}$) jusqu'au fond de l'enceinte ($50\text{ mm}$).
  - **Verdict :** Référence de contrôle terrestre ($1g$).

- **`clinostat_1d` (Clinostat 2D mono-axial)**
  - **Signature cinématique :** Gravité résiduelle quasi nulle uniquement dans le plan de rotation, isotropie limitée ($\sim 0{,}50$).
  - **Comportement `statolith` :** Orbite circulaire plane de rayon $R \approx 0{,}62\text{ nm}$.
  - **Comportement `glycerol_bead` :** Orbite circulaire plane de rayon $R \approx 9\text{ µm}$ sans dérive nette.
  - **Verdict :** Insuffisant en 3D car la gravité n'est moyennée que dans un seul plan (persistance d'un biais axial).

- **`centrifuge_sweep` (Rampe centrifuge asymptotique)**
  - **Signature cinématique :** Forte gravité résiduelle ($\approx 0{,}50\ g_0$) et faible isotropie ($0{,}375$).
  - **Comportement `statolith` :** Trajectoire en courbe de Viviani confinée sur une enveloppe de $0{,}6\text{ nm}$.
  - **Comportement `glycerol_bead` :** Dérive radiale continue vers la paroi sous l'effet de l'accélération centrifuge.
  - **Verdict :** Inadapté à la simulation de microgravité en raison des effets centrifuges et de la composante résiduelle élevée.

- **`desynchronized_sine` (Oscillations harmoniques désynchronisées)**
  - **Signature cinématique :** Gravité résiduelle notable ($\approx 0{,}30\ g_0$) et isotropie partielle ($0{,}456$).
  - **Comportement `statolith` :** Enveloppe sphérique de $0{,}6\text{ nm}$ autour de $\vec{x}_0$ avec dérive nulle.
  - **Comportement `glycerol_bead` :** Dérive verticale quasi linéaire ($1{,}27\text{ mm}$ en $10\text{ min}$).
  - **Verdict :** Insuffisant : l'oscillation bornée des cardans laisse un biais gravitaire moyen non nul selon l'axe vertical ($g_z \neq 0$).

- **`constant_speed_ratio` (Rotation bi-axiale à rapport irrationnel)**
  - **Signature cinématique :** Gravité résiduelle très faible ($2{,}85 \times 10^{-4}\ g_0$) et forte isotropie ($0{,}750$).
  - **Comportement `statolith` :** Coquille sphérique régulière de rayon $R \approx 0{,}62\text{ nm}$.
  - **Comportement `glycerol_bead` :** Orbite quasi-périodique bornée ($R_g \approx 19\text{ µm}$) à dérive quasi nulle.
  - **Verdict :** **Meilleur compromis déterministe** — annule efficacement la dérive sans générer d'accélérations angulaires d'Euler ($\dot{\vec{\Omega}} = \vec{0}$).

- **`random_walk` (Marche aléatoire stochastique 3D)**
  - **Signature cinématique :** Gravité résiduelle inférieure à $10^{-2}\ g_0$ et isotropie tendant vers l'unité ($\to 1{,}00$).
  - **Comportement `statolith` :** Exploration homogène d'une sphère pleine autour de $\vec{x}_0$ ($R_g \approx 0{,}6\text{ nm}$).
  - **Comportement `glycerol_bead` :** Marche aléatoire diffusive présentant une dérive macroscopique ($25{,}7\text{ mm}$ en $4\text{ h}$) en l'absence d'ancrage.
  - **Verdict :** **Meilleure isotropie biologique** — son caractère apériodique évite toute accoutumance mécanique des capteurs cellulaires.

---

## 4. Sélection de la Trajectoire Optimale

Le choix du profil moteur dépend directement de la contrainte expérimentale privilégiée :

1. **Pour une microgravité biologique réaliste (éviter la mécanotransduction périodique) : `random_walk`**
   - C'est le seul profil qui brise toute cohérence de phase tout en tendant vers une isotropie sphérique complète ($\lambda_1 \approx \lambda_2 \approx \lambda_3 \approx 1/3$).
   - En contrepartie, ses inversions aléatoires de vitesse génèrent de légères accélérations d'Euler ($\dot{\vec{\Omega}} \times \vec{r}$) et une diffusion brownienne macroscopique en l'absence d'ancrage élastique ($k = 0$).

2. **Pour une annulation gravitaire pure et reproductible à bruit inertiel nul : `constant_speed_ratio`**
   - Grâce au rapport irrationnel entre les deux axes ($\omega_2 = 0{,}732\,\omega_1$), les accélérations angulaires sont strictement nulles ($\dot{\vec{\Omega}} = \vec{0}$), ce qui élimine totalement les forces fictives d'Euler.
   - La gravité résiduelle chute sous $3\times 10^{-4}\ g_0$ et la particule reste confinée dans un voisinage micrométrique de son point de départ même sans cytosquelette ($k = 0$).

---

## 5. Interprétation Biologique : Organite Cellulaire en Suspension

Les simulations mettent en évidence le **rôle mécanique fondamental du cytosquelette** (modélisé par la raideur élastique $k$ du réseau d'actine) dans la perception de la gravité (graviperception) :

- **Un régime strictement rampant (Stokes pur) :**
  - Pour un statolithe ($R = 1{,}5\text{ µm}$, $\rho = 1500\text{ kg/m}^3$), le nombre de Reynolds reste de l'ordre de $Re_p \sim 10^{-11}$ (et $\sim 10^{-5}$ pour une bille macroscopique dans du glycérol), bien en deçà du seuil $Re_p = 0{,}1$. L'inertie propre de l'organite est négligeable devant la dissipation visqueuse du cytoplasme.

- **Le cytosquelette agit comme un filtre passe-bas mécanique :**
  - Avec $k = 10^{-4}\text{ N/m}$, le temps de relaxation viscoélastique vaut $\tau_k = \frac{6\pi\mu R}{k} \approx 28{,}3\text{ ms}$, ce qui correspond à une **fréquence de coupure $f_k = \frac{1}{2\pi\tau_k} \approx 5{,}63\text{ Hz}$**.
  - Tant que la rotation du RPM s'effectue à des fréquences inférieures à $f_k$ ($0{,}1\text{ à }0{,}5\text{ Hz}$), l'organite suit quasi instantanément le vecteur gravité apparent $\vec{g}_{\mathcal{R}_2}(t)$ sur une micro-sphère d'équilibre de rayon $r_{\text{eq}} = \frac{\Delta\rho\, V\, g_0}{k} \approx 0{,}62\text{ nm}$.

- **Mécanisme de simulation de l'apesanteur sans contact membranaire :**
  - **Sans réseau d'actine ($k = 0$) :** La moindre gravité résiduelle non nulle (`desynchronized_sine`) ou diffusion directionnelle (`random_walk`) entraîne une dérive lente mais inexorable jusqu'à la paroi ($R_{\text{tube}}$).
  - **Avec réseau d'actine ($k > 0$) :** L'organite reste confiné à moins d'un nanomètre de sa position d'équilibre $\vec{x}_0$ et **ne touche jamais la membrane plasmique** (`Boundary Contact % = 0.00%`). Sur une trajectoire isotrope (`random_walk` ou `constant_speed_ratio`), l'organite balaye uniformément toutes les directions autour de $\vec{x}_0$ : la contrainte mécanique moyenne exercée sur les filaments d'actine s'annule dans le temps, empêchant l'ouverture directionnelle des canaux mécanosensibles et reproduisant ainsi l'état d'apesanteur fonctionnelle.
