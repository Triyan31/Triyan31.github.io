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
