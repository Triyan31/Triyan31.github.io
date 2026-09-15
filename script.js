const root = document.body;
const toggle = document.getElementById('themeToggle');
const storedTheme = localStorage.getItem('tal-theme');
if (storedTheme === 'light') root.classList.add('light');

toggle?.addEventListener('click', () => {
  root.classList.toggle('light');
  localStorage.setItem('tal-theme', root.classList.contains('light') ? 'light' : 'dark');
});

const observer = new IntersectionObserver((entries) => {
  entries.forEach((entry) => {
    if (entry.isIntersecting) {
      entry.target.classList.add('visible');
      observer.unobserve(entry.target);
    }
  });
}, { threshold: 0.12 });

document.querySelectorAll('.reveal').forEach((el) => observer.observe(el));

const navLinks = [...document.querySelectorAll('.nav-links a')];
const sections = [...document.querySelectorAll('main section[id]')];
const sectionObserver = new IntersectionObserver((entries) => {
  entries.forEach((entry) => {
    if (!entry.isIntersecting) return;
    navLinks.forEach((link) => link.classList.toggle('active', link.getAttribute('href') === `#${entry.target.id}`));
  });
}, { rootMargin: '-35% 0px -55% 0px', threshold: 0 });
sections.forEach((section) => sectionObserver.observe(section));

const spotlight = document.getElementById('spotlight');
const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
if (spotlight && !reducedMotion) {
  window.addEventListener('pointermove', (event) => {
    spotlight.style.left = `${event.clientX}px`;
    spotlight.style.top = `${event.clientY}px`;
  }, { passive: true });
}
