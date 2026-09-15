const root = document.body;
const toggle = document.getElementById('themeToggle');
const storedTheme = localStorage.getItem('tal-theme');
if (storedTheme === 'light') root.classList.add('light');

toggle?.addEventListener('click', () => {
  root.classList.toggle('light');
  localStorage.setItem('tal-theme', root.classList.contains('light') ? 'light' : 'dark');
});

const revealObserver = new IntersectionObserver((entries) => {
  entries.forEach((entry) => {
    if (entry.isIntersecting) {
      entry.target.classList.add('visible');
      revealObserver.unobserve(entry.target);
    }
  });
}, { threshold: 0.12 });

function observeReveals(scope = document) {
  scope.querySelectorAll('.reveal:not(.visible)').forEach((el) => revealObserver.observe(el));
}
observeReveals();

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

const escapeHtml = (value = '') => String(value).replace(/[&<>'"]/g, (char) => ({
  '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;'
}[char]));

async function loadJson(path) {
  const response = await fetch(path, { cache: 'no-cache' });
  if (!response.ok) throw new Error(`Unable to load ${path}: ${response.status}`);
  return response.json();
}

function projectClass(project) {
  if (project.featured) return 'project project-iam featured reveal';
  if (project.status === 'product') return 'project project-product reveal';
  return 'project reveal';
}

function statusClass(project) {
  if (project.status === 'product') return 'status product-status';
  if (project.status === 'research') return 'status research-status';
  if (project.visibility === 'public') return 'status public-status';
  return 'status';
}

function renderProjects(data) {
  const container = document.querySelector('#work .projects');
  if (!container || !Array.isArray(data.projects)) return;
  const visible = data.projects.filter((p) => p.available !== false);
  container.innerHTML = visible.map((project, index) => {
    const tag = project.url ? 'a' : 'article';
    const link = project.url ? ` href="${escapeHtml(project.url)}" target="_blank" rel="noreferrer"` : '';
    const meta = project.github?.language ? `<span>${escapeHtml(project.github.language)}</span>` : '';
    return `<${tag} class="${projectClass(project)}"${link}>
      <div class="project-top"><span class="${statusClass(project)}"><i></i> ${escapeHtml(project.label)}</span><span>${String(index + 1).padStart(2, '0')}${project.url ? ' ↗' : ''}</span></div>
      <div class="project-symbol">${escapeHtml(project.symbol)}</div>
      <h3>${escapeHtml(project.title)}</h3><p>${escapeHtml(project.description)}</p>
      <div class="chips">${(project.tags || []).map((tag) => `<span>${escapeHtml(tag)}</span>`).join('')}${meta}</div>
    </${tag}>`;
  }).join('');
  observeReveals(container);
}

function renderPublications(data) {
  const container = document.querySelector('#research .publication-list');
  if (!container || !Array.isArray(data.publications)) return;
  const verified = data.publications.filter((p) => p.verification === 'verified').sort((a, b) => b.year - a.year);
  container.innerHTML = `<div class="pub-label">SELECTED VERIFIED PUBLICATIONS</div>` + verified.map((pub, index) => {
    const details = [pub.venue, ...(pub.keywords || [])].filter(Boolean).map(escapeHtml).join(' · ');
    const title = pub.doi ? `<a href="https://doi.org/${encodeURIComponent(pub.doi)}" target="_blank" rel="noreferrer">${escapeHtml(pub.title)} ↗</a>` : escapeHtml(pub.title);
    return `<article><span>${escapeHtml(pub.year)}</span><div><h3>${title}</h3><p>${details}</p></div><b>${String(index + 1).padStart(2, '0')}</b></article>`;
  }).join('');
}

function renderTeaching(data) {
  const container = document.querySelector('#teaching .course-grid');
  if (!container || !Array.isArray(data.courses)) return;
  const courses = data.courses.filter((c) => c.published).sort((a, b) => a.order - b.order);
  container.innerHTML = courses.map((course) => `<article class="course reveal">
    <div class="course-no">${String(course.order).padStart(2, '0')}</div><div><span class="course-type">${escapeHtml(course.type)}</span><h3>${escapeHtml(course.title)}</h3><p>${escapeHtml(course.description)}</p></div><span class="course-arrow">↗</span>
  </article>`).join('');
  observeReveals(container);
}

async function hydratePortfolio() {
  const results = await Promise.allSettled([
    loadJson('./data/projects.json'),
    loadJson('./data/publications.json'),
    loadJson('./data/teaching.json')
  ]);
  if (results[0].status === 'fulfilled') renderProjects(results[0].value);
  if (results[1].status === 'fulfilled') renderPublications(results[1].value);
  if (results[2].status === 'fulfilled') renderTeaching(results[2].value);
  results.filter((r) => r.status === 'rejected').forEach((r) => console.warn(r.reason));
}

hydratePortfolio();
