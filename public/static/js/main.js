/* ============================================================
   InterviewMind - Main front-end logic
   ============================================================
   Lightweight helpers shared across all pages.
   ============================================================ */

(function () {
    'use strict';

    // Auto-dismiss flash messages after 5s
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(a => {
        setTimeout(() => {
            a.style.transition = 'opacity 0.5s, transform 0.5s';
            a.style.opacity = '0';
            a.style.transform = 'translateY(-10px)';
            setTimeout(() => a.remove(), 500);
        }, 5000);
    });

    // Close mobile nav on link click
    document.querySelectorAll('.nav-links a').forEach(link => {
        link.addEventListener('click', () => {
            const navLinks = document.querySelector('.nav-links');
            if (navLinks.classList.contains('is-open')) {
                navLinks.classList.remove('is-open');
            }
        });
    });

    // Smooth-scroll for in-page anchors
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                e.preventDefault();
                target.scrollIntoView({ behavior: 'smooth' });
            }
        });
    });

    // Lazy fade-in on scroll for cards not already animated
    const observerOptions = { threshold: 0.1, rootMargin: '0px 0px -50px 0px' };
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-fade-up');
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);
    document.querySelectorAll('.card:not(.animate-fade-up)').forEach(el => observer.observe(el));

    // Console banner for the curious
    if (typeof console !== 'undefined' && console.log) {
        console.log(
            '%cInterviewMind %cv1.0.0\n%cBuilt with Flask + HTML5 Canvas. View source on GitHub — academic project.',
            'color:#00f0ff;font-size:18px;font-weight:bold;text-shadow:0 0 8px #00f0ff;',
            'color:#a8a8c0;font-size:11px;',
            'color:#6c6c85;font-size:11px;'
        );
    }
})();
