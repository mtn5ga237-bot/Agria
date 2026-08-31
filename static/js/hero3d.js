/* Hero 3D d'AgriA : nuage de particules organique evoquant l'analyse IA d'un sol,
 * autour d'un icosaedre filaire. Implemente avec Three.js (BufferGeometry + Points
 * pour les particules, conformement aux bonnes pratiques de performance : segments
 * limites, nombre de particules borne et adapte a la taille d'ecran). */
(function () {
    const conteneur = document.getElementById('hero-3d');
    if (!conteneur || typeof THREE === 'undefined') return;

    const reduitAnimation = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const estMobile = window.innerWidth < 768;
    const nbParticules = estMobile ? 900 : 2200;

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(50, conteneur.clientWidth / conteneur.clientHeight, 0.1, 100);
    camera.position.z = 7;

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setSize(conteneur.clientWidth, conteneur.clientHeight);
    conteneur.appendChild(renderer.domElement);

    // --- Nuage de particules (sphere organique) ---
    const geometrieParticules = new THREE.BufferGeometry();
    const positions = new Float32Array(nbParticules * 3);
    const rayonBase = 2.6;
    for (let i = 0; i < nbParticules; i++) {
        const theta = Math.random() * Math.PI * 2;
        const phi = Math.acos(2 * Math.random() - 1);
        const rayon = rayonBase + (Math.random() - 0.5) * 1.1;
        positions[i * 3] = rayon * Math.sin(phi) * Math.cos(theta);
        positions[i * 3 + 1] = rayon * Math.sin(phi) * Math.sin(theta);
        positions[i * 3 + 2] = rayon * Math.cos(phi);
    }
    geometrieParticules.setAttribute('position', new THREE.BufferAttribute(positions, 3));

    const materiauParticules = new THREE.PointsMaterial({
        size: 0.045,
        color: 0x22c55e,
        transparent: true,
        opacity: 0.85,
        blending: THREE.AdditiveBlending,
        depthWrite: false,
    });
    const particules = new THREE.Points(geometrieParticules, materiauParticules);
    scene.add(particules);

    // --- Icosaedre filaire central (symbolise le reseau / la structure du modele IA) ---
    const geometrieCoeur = new THREE.IcosahedronGeometry(1.5, 1);
    const materiauCoeur = new THREE.MeshBasicMaterial({ color: 0x38bdf8, wireframe: true, transparent: true, opacity: 0.55 });
    const coeur = new THREE.Mesh(geometrieCoeur, materiauCoeur);
    scene.add(coeur);

    // --- Anneau exterieur filaire, contra-rotatif : renforce la profondeur "reseau de donnees" ---
    const geometrieAnneau = new THREE.IcosahedronGeometry(2.15, 0);
    const materiauAnneau = new THREE.MeshBasicMaterial({ color: 0xa78bfa, wireframe: true, transparent: true, opacity: 0.22 });
    const anneau = new THREE.Mesh(geometrieAnneau, materiauAnneau);
    scene.add(anneau);

    // --- Halo lumineux (intensite respirante) ---
    const halo = new THREE.PointLight(0x22c55e, 40, 20);
    halo.position.set(2, 2, 4);
    scene.add(halo);

    function redimensionner() {
        const largeur = conteneur.clientWidth, hauteur = conteneur.clientHeight;
        camera.aspect = largeur / hauteur;
        camera.updateProjectionMatrix();
        renderer.setSize(largeur, hauteur);
    }
    window.addEventListener('resize', redimensionner);

    // Parallaxe douce : la scene suit legerement le curseur (souris) pour une sensation interactive.
    let ciblePointeurX = 0, ciblePointeurY = 0, pointeurX = 0, pointeurY = 0;
    if (!reduitAnimation && !estMobile) {
        conteneur.addEventListener('mousemove', (e) => {
            const rect = conteneur.getBoundingClientRect();
            ciblePointeurX = ((e.clientX - rect.left) / rect.width - 0.5) * 2;
            ciblePointeurY = ((e.clientY - rect.top) / rect.height - 0.5) * 2;
        });
        conteneur.addEventListener('mouseleave', () => { ciblePointeurX = 0; ciblePointeurY = 0; });
    }

    let idAnimation;
    let angle = 0;
    function animer() {
        angle += 0.0022;
        pointeurX += (ciblePointeurX - pointeurX) * 0.05;
        pointeurY += (ciblePointeurY - pointeurY) * 0.05;
        particules.rotation.y = angle + pointeurX * 0.3;
        particules.rotation.x = angle * 0.3 + pointeurY * 0.2;
        coeur.rotation.y = -angle * 1.4 + pointeurX * 0.4;
        coeur.rotation.x = angle * 0.6 + pointeurY * 0.3;
        anneau.rotation.y = angle * 0.55 - pointeurX * 0.2;
        anneau.rotation.x = -angle * 0.35 + pointeurY * 0.15;
        halo.intensity = 32 + Math.sin(angle * 6) * 10;
        camera.position.x = pointeurX * 0.4;
        camera.position.y = -pointeurY * 0.4;
        camera.lookAt(0, 0, 0);
        renderer.render(scene, camera);
        idAnimation = requestAnimationFrame(animer);
    }

    if (reduitAnimation) {
        renderer.render(scene, camera);
    } else {
        animer();
    }

    document.addEventListener('visibilitychange', () => {
        if (document.hidden && idAnimation) { cancelAnimationFrame(idAnimation); }
        else if (!document.hidden && !reduitAnimation) { animer(); }
    });
})();
