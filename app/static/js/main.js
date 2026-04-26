// Janawaz – Main JS

// Mobile nav toggle
document.getElementById('navToggle')?.addEventListener('click', function () {
    document.getElementById('navLinks')?.classList.toggle('open');
});

// Auto-dismiss flash messages after 5s
document.querySelectorAll('.flash').forEach(el => {
    setTimeout(() => el.remove(), 5000);
});

// Smooth scroll for anchor links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            e.preventDefault();
            target.scrollIntoView({ behavior: 'smooth' });
        }
    });
});
