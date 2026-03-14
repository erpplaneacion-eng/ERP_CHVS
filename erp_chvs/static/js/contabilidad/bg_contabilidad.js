// bg_contabilidad.js — Fondo Three.js temático de contabilidad/finanzas

(function () {
    const canvas = document.getElementById('contabilidad-bg-canvas');
    const parent = document.getElementById('contabilidad-dashboard-background');
    if (!canvas || !parent || typeof THREE === 'undefined') return;

    let scene, camera, renderer;
    let linesMesh;

    // Sprites de texto contable
    const sprites     = [];
    const spriteVel   = [];
    const spritePos   = [];   // Float32Array para líneas de conexión

    // Paleta del módulo contabilidad
    const C_VERDE  = 0x1a7f64;
    const C_TEAL   = 0x0d9488;
    const C_NAVY   = 0x1e3a8a;
    const SPRITE_COUNT = 22;
    const CONNECT_DIST = 7;

    const SYMBOLS = [
        '$', '%', 'COP', '↑', '→', '∑',
        '$ 1.2M', '85%', '↑12%', '18%',
        '$ 890K', '45%', '128', '96%',
        '+ 3.4%', '142', 'RC', 'IVA',
        '$ 320K', '72%', '∑ COP', '↓'
    ];

    let mouseX = 0, mouseY = 0;

    /* ─── helpers ─────────────────────────────────────────────────── */
    function rand(min, max) { return min + Math.random() * (max - min); }

    function getSize() {
        return { w: parent.offsetWidth, h: parent.offsetHeight };
    }

    function crearSprite(texto, hexColor) {
        const c   = document.createElement('canvas');
        c.width   = 192;
        c.height  = 64;
        const ctx = c.getContext('2d');
        ctx.font        = 'bold 28px monospace';
        ctx.fillStyle   = hexColor;
        ctx.textAlign   = 'center';
        ctx.fillText(texto, 96, 44);
        const tex = new THREE.CanvasTexture(c);
        const mat = new THREE.SpriteMaterial({ map: tex, transparent: true, opacity: 0.28 });
        const sp  = new THREE.Sprite(mat);
        sp.scale.set(5.5, 2, 1);
        return sp;
    }

    /* ─── init ────────────────────────────────────────────────────── */
    function init() {
        const { w, h } = getSize();

        scene  = new THREE.Scene();
        scene.background = new THREE.Color(0xffffff);

        camera = new THREE.PerspectiveCamera(50, w / h, 1, 500);
        camera.position.z = 30;

        renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
        renderer.setPixelRatio(window.devicePixelRatio);
        renderer.setSize(w, h);

        // ── Líneas horizontales de libro contable ──────────────────
        const gridMat = new THREE.LineBasicMaterial({
            color: 0xb2dbd6,
            transparent: true,
            opacity: 0.45
        });
        for (let y = -12; y <= 14; y += 3.2) {
            const geo = new THREE.BufferGeometry().setFromPoints([
                new THREE.Vector3(-32, y, -9),
                new THREE.Vector3( 32, y, -9)
            ]);
            scene.add(new THREE.Line(geo, gridMat));
        }

        // ── Sprites de texto contable ──────────────────────────────
        const spColors = ['#1a7f64', '#0d9488', '#1e3a8a'];
        const rawPos   = new Float32Array(SPRITE_COUNT * 3);

        for (let i = 0; i < SPRITE_COUNT; i++) {
            const sp = crearSprite(SYMBOLS[i], spColors[i % 3]);
            const x  = rand(-22, 22);
            const y  = rand(-9,  10);
            const z  = rand(-3,   3);
            sp.position.set(x, y, z);
            scene.add(sp);
            sprites.push(sp);
            rawPos[i * 3]     = x;
            rawPos[i * 3 + 1] = y;
            rawPos[i * 3 + 2] = z;
            spriteVel.push({
                x: (Math.random() - 0.5) * 0.022,
                y: (Math.random() - 0.5) * 0.016
            });
        }
        // guardamos referencia mutable
        spritePos.push(rawPos);

        // ── Líneas de conexión entre sprites cercanos ──────────────
        const maxSeg  = SPRITE_COUNT * SPRITE_COUNT;
        const lineBuf = new Float32Array(maxSeg * 3);
        const lineGeo = new THREE.BufferGeometry();
        lineGeo.setAttribute('position', new THREE.BufferAttribute(lineBuf, 3));
        linesMesh = new THREE.LineSegments(lineGeo, new THREE.LineBasicMaterial({
            color:       C_TEAL,
            transparent: true,
            opacity:     0.13
        }));
        scene.add(linesMesh);

        // ── Eventos ────────────────────────────────────────────────
        parent.addEventListener('mousemove', (e) => {
            const rect = parent.getBoundingClientRect();
            mouseX = ((e.clientX - rect.left) / rect.width  - 0.5) * 5;
            mouseY = -((e.clientY - rect.top)  / rect.height - 0.5) * 5;
        });

        new ResizeObserver(() => {
            const { w, h } = getSize();
            camera.aspect = w / h;
            camera.updateProjectionMatrix();
            renderer.setSize(w, h);
        }).observe(parent);

        animate();
    }

    /* ─── loop ────────────────────────────────────────────────────── */
    function animate() {
        requestAnimationFrame(animate);

        // Parallax suave de cámara
        camera.position.x += (mouseX - camera.position.x) * 0.04;
        camera.position.y += (mouseY - camera.position.y) * 0.04;
        camera.lookAt(scene.position);

        // Mover sprites de texto
        const pos   = spritePos[0];
        const BX    = 24, BY = 12;
        sprites.forEach((sp, i) => {
            sp.position.x += spriteVel[i].x;
            sp.position.y += spriteVel[i].y;
            if (Math.abs(sp.position.x) > BX) spriteVel[i].x *= -1;
            if (Math.abs(sp.position.y) > BY) spriteVel[i].y *= -1;
            pos[i * 3]     = sp.position.x;
            pos[i * 3 + 1] = sp.position.y;
            pos[i * 3 + 2] = sp.position.z;
        });

        // Líneas de conexión
        const lp = linesMesh.geometry.attributes.position.array;
        let vpos = 0, numLines = 0;
        for (let i = 0; i < SPRITE_COUNT; i++) {
            for (let j = i + 1; j < SPRITE_COUNT; j++) {
                const dx   = pos[i * 3] - pos[j * 3];
                const dy   = pos[i * 3 + 1] - pos[j * 3 + 1];
                const dist = Math.sqrt(dx * dx + dy * dy);
                if (dist < CONNECT_DIST) {
                    lp[vpos++] = pos[i * 3];     lp[vpos++] = pos[i * 3 + 1]; lp[vpos++] = pos[i * 3 + 2];
                    lp[vpos++] = pos[j * 3];     lp[vpos++] = pos[j * 3 + 1]; lp[vpos++] = pos[j * 3 + 2];
                    numLines++;
                }
            }
        }
        linesMesh.geometry.setDrawRange(0, numLines * 2);
        linesMesh.geometry.attributes.position.needsUpdate = true;

        renderer.render(scene, camera);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
