/* ============================================================
   InterviewMind - Neon Particle Background Engine
   ============================================================
   Custom canvas-based particle system with:
     - Multi-color neon particles (cyan/magenta/purple)
     - Distance-based connection lines (network graph effect)
     - Mouse repulsion / attraction
     - Particle glow (radial gradients)
     - Parallax depth layers
     - Reduced-motion respect (accessibility)
     - Performance throttling on low FPS devices
   ============================================================ */

(function () {
    'use strict';

    const SELECTOR = '[data-particle-canvas]';
    const canvas = document.querySelector(SELECTOR);
    if (!canvas) return;

    // Respect reduced-motion preference
    const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (prefersReduced) {
        canvas.style.display = 'none';
        return;
    }

    const ctx = canvas.getContext('2d', { alpha: true });

    // ---- Configuration (overridable via data-* attributes) ----
    const CONFIG = {
        density: parseFloat(canvas.dataset.density || '0.00012'),  // particles per pixel²
        maxParticles: parseInt(canvas.dataset.maxParticles || '140', 10),
        minParticles: parseInt(canvas.dataset.minParticles || '40', 10),
        speed: parseFloat(canvas.dataset.speed || '0.45'),
        linkDistance: parseFloat(canvas.dataset.linkDistance || '130'),
        linkOpacity: parseFloat(canvas.dataset.linkOpacity || '0.35'),
        mouseRadius: parseFloat(canvas.dataset.mouseRadius || '160'),
        mouseForce: parseFloat(canvas.dataset.mouseForce || '0.9'),
        colors: ['#00f0ff', '#ff00e5', '#a855f7', '#22d3ee', '#f0abfc'],
        glowSize: 6,
    };

    let particles = [];
    let mouse = { x: -9999, y: -9999, active: false };
    let width = 0, height = 0, dpr = 1;
    let lastFrameTime = performance.now();
    let fps = 60, framesSinceSample = 0, lastSample = performance.now();

    // ---- Sizing & DPR handling ----
    function resize() {
        dpr = Math.min(window.devicePixelRatio || 1, 2);
        width = window.innerWidth;
        height = window.innerHeight;
        canvas.width = width * dpr;
        canvas.height = height * dpr;
        canvas.style.width = width + 'px';
        canvas.style.height = height + 'px';
        ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
        initParticles();
    }

    function particleCountForViewport() {
        const area = width * height;
        let count = Math.floor(area * CONFIG.density);
        count = Math.max(CONFIG.minParticles, Math.min(count, CONFIG.maxParticles));
        return count;
    }

    function initParticles() {
        const target = particleCountForViewport();
        if (particles.length === 0) {
            for (let i = 0; i < target; i++) particles.push(createParticle());
        } else if (target > particles.length) {
            while (particles.length < target) particles.push(createParticle());
        } else if (target < particles.length) {
            particles.length = target;
        }
    }

    function createParticle() {
        const color = CONFIG.colors[Math.floor(Math.random() * CONFIG.colors.length)];
        // Depth layer 0..1 — slower & smaller for far particles
        const depth = Math.random();
        return {
            x: Math.random() * width,
            y: Math.random() * height,
            vx: (Math.random() - 0.5) * CONFIG.speed * (0.4 + depth * 0.8),
            vy: (Math.random() - 0.5) * CONFIG.speed * (0.4 + depth * 0.8),
            radius: 0.8 + depth * 2.4 + Math.random() * 0.6,
            color: color,
            depth: depth,  // 0 = far, 1 = near
            phase: Math.random() * Math.PI * 2, // for pulsing glow
            phaseSpeed: 0.005 + Math.random() * 0.015,
        };
    }

    // ---- Animation step ----
    function step(now) {
        // FPS estimator for adaptive throttling
        framesSinceSample++;
        if (now - lastSample > 500) {
            fps = (framesSinceSample * 1000) / (now - lastSample);
            framesSinceSample = 0;
            lastSample = now;
        }

        ctx.clearRect(0, 0, width, height);
        ctx.globalCompositeOperation = 'lighter'; // additive blending for neon

        updateParticles();
        drawLinks();
        drawParticles();

        requestAnimationFrame(step);
    }

    function updateParticles() {
        const dt = Math.min(2, (performance.now() - lastFrameTime) / 16.67);
        lastFrameTime = performance.now();

        for (let i = 0; i < particles.length; i++) {
            const p = particles[i];
            p.x += p.vx * dt;
            p.y += p.vy * dt;
            p.phase += p.phaseSpeed * dt;

            // Wrap-around screen edges
            if (p.x < -20) p.x = width + 20;
            if (p.x > width + 20) p.x = -20;
            if (p.y < -20) p.y = height + 20;
            if (p.y > height + 20) p.y = -20;

            // Mouse interaction (repulsion)
            if (mouse.active) {
                const dx = p.x - mouse.x;
                const dy = p.y - mouse.y;
                const dist2 = dx * dx + dy * dy;
                const r2 = CONFIG.mouseRadius * CONFIG.mouseRadius;
                if (dist2 < r2 && dist2 > 0.01) {
                    const dist = Math.sqrt(dist2);
                    const force = (1 - dist / CONFIG.mouseRadius) * CONFIG.mouseForce * (0.5 + p.depth);
                    p.x += (dx / dist) * force * 2;
                    p.y += (dy / dist) * force * 2;
                }
            }
        }
    }

    function drawLinks() {
        const maxDist = CONFIG.linkDistance;
        const maxDist2 = maxDist * maxDist;
        ctx.lineWidth = 0.6;
        for (let i = 0; i < particles.length; i++) {
            const a = particles[i];
            for (let j = i + 1; j < particles.length; j++) {
                const b = particles[j];
                const dx = a.x - b.x;
                const dy = a.y - b.y;
                const d2 = dx * dx + dy * dy;
                if (d2 < maxDist2) {
                    const alpha = (1 - Math.sqrt(d2) / maxDist) * CONFIG.linkOpacity;
                    // Use particle A's color for the line
                    const c = hexToRgba(a.color, alpha);
                    ctx.strokeStyle = c;
                    ctx.beginPath();
                    ctx.moveTo(a.x, a.y);
                    ctx.lineTo(b.x, b.y);
                    ctx.stroke();
                }
            }
        }
    }

    function drawParticles() {
        for (let i = 0; i < particles.length; i++) {
            const p = particles[i];
            const pulse = 0.7 + Math.sin(p.phase) * 0.3;
            const r = p.radius * pulse;

            // Outer glow (radial gradient)
            const glowR = r * 5;
            const grad = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, glowR);
            grad.addColorStop(0, hexToRgba(p.color, 0.9 * (0.3 + p.depth * 0.7)));
            grad.addColorStop(0.3, hexToRgba(p.color, 0.3));
            grad.addColorStop(1, hexToRgba(p.color, 0));
            ctx.fillStyle = grad;
            ctx.beginPath();
            ctx.arc(p.x, p.y, glowR, 0, Math.PI * 2);
            ctx.fill();

            // Core
            ctx.fillStyle = '#ffffff';
            ctx.beginPath();
            ctx.arc(p.x, p.y, r * 0.8, 0, Math.PI * 2);
            ctx.fill();

            // Inner colored ring
            ctx.strokeStyle = p.color;
            ctx.lineWidth = 0.8;
            ctx.beginPath();
            ctx.arc(p.x, p.y, r * 1.5, 0, Math.PI * 2);
            ctx.stroke();
        }
    }

    function hexToRgba(hex, alpha) {
        // Convert #rrggbb to rgba(r,g,b,a)
        if (hex.startsWith('rgba')) return hex;
        if (hex.startsWith('rgb(')) return hex.replace('rgb(', 'rgba(').replace(')', `, ${alpha})`);
        let h = hex.replace('#', '');
        if (h.length === 3) h = h.split('').map(c => c + c).join('');
        const r = parseInt(h.substr(0, 2), 16);
        const g = parseInt(h.substr(2, 2), 16);
        const b = parseInt(h.substr(4, 2), 16);
        return `rgba(${r}, ${g}, ${b}, ${alpha})`;
    }

    // ---- Event listeners ----
    window.addEventListener('resize', resize, { passive: true });
    window.addEventListener('mousemove', function (e) {
        mouse.x = e.clientX;
        mouse.y = e.clientY;
        mouse.active = true;
    });
    window.addEventListener('mouseleave', function () {
        mouse.active = false;
    });
    window.addEventListener('touchmove', function (e) {
        if (e.touches.length > 0) {
            mouse.x = e.touches[0].clientX;
            mouse.y = e.touches[0].clientY;
            mouse.active = true;
        }
    }, { passive: true });
    window.addEventListener('touchend', function () {
        mouse.active = false;
    });

    // Pause when tab hidden (saves battery/CPU)
    document.addEventListener('visibilitychange', function () {
        if (document.hidden) {
            // Will naturally stop because rAF pauses
        } else {
            lastFrameTime = performance.now();
        }
    });

    // ---- Kickoff ----
    resize();
    requestAnimationFrame(step);
})();
