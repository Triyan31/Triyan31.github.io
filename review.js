const escapeHtml = (value = '') => String(value).replace(/[&<>'"]/g, (char) => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[char]));
let candidates = [];
const queue = document.getElementById('reviewQueue');
const notice = document.getElementById('reviewNotice');
const stats = document.getElementById('reviewStats');
const search = document.getElementById('reviewSearch');
const filter = document.getElementById('reviewFilter');
const workflowUrl = 'https://github.com/Triyan31/Triyan31.github.io/actions/workflows/academic-review-decision.yml';

function doiUrl(doi){ return doi ? `https://doi.org/${encodeURIComponent(doi)}` : ''; }
function confidence(candidate){
  const score = Number(candidate.author_similarity || 0);
  if (candidate.identity_name_match && score >= .9) return ['HIGHER','higher'];
  if (candidate.identity_name_match && score >= .78) return ['AMBIGUOUS','ambiguous'];
  return ['WEAK','weak'];
}
function renderStats(report){
  const summary = report.verification_summary || {};
  const stronger = candidates.filter(c => c.identity_name_match).length;
  stats.innerHTML = `<article><strong>${summary.total_public_records || 0}</strong><span>Public records checked</span></article><article><strong>${summary.machine_verified || 0}</strong><span>Machine verified</span></article><article><strong>${summary.manual_verified || 0}</strong><span>Manual-source verified</span></article><article><strong>${candidates.length}</strong><span>Discovery candidates</span></article><article><strong>${stronger}</strong><span>Name-match candidates</span></article>`;
}
function decisionControls(candidate){
  const doi = candidate.doi || '';
  if(!doi) return `<span class="review-decision-note">No DOI: keep for manual review.</span>`;
  return `<div class="decision-panel" data-doi="${escapeHtml(doi)}">
    <button class="btn decision approve" type="button" data-decision="approve" data-doi="${escapeHtml(doi)}">✓ Confirm mine</button>
    <button class="btn decision reject" type="button" data-decision="reject" data-doi="${escapeHtml(doi)}">✕ Not mine</button>
    <button class="btn decision pending" type="button" data-decision="pending" data-doi="${escapeHtml(doi)}">? Keep for review</button>
    <span class="review-decision-note">Approve/reject is completed through authenticated GitHub Actions. Approval remains fail-closed until identity and bibliographic checks pass.</span>
  </div>`;
}
function card(candidate, index){
  const [label, cls] = confidence(candidate);
  const authors = (candidate.authors || []).join(' · ');
  const url = doiUrl(candidate.doi);
  const score = candidate.author_similarity ? `${Math.round(candidate.author_similarity * 100)}%` : '—';
  return `<article class="review-card" data-match="${candidate.identity_name_match ? 'strong' : 'weak'}">
    <div class="review-card-index">${String(index + 1).padStart(2,'0')}</div>
    <div class="review-card-main"><div class="review-card-meta"><span>${escapeHtml(candidate.year || 'YEAR ?')}</span><span>${escapeHtml(candidate.venue || candidate.publisher || 'Source metadata')}</span><span class="confidence ${cls}">${label}</span></div>
      <h3>${url ? `<a href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(candidate.title || 'Untitled candidate')} ↗</a>` : escapeHtml(candidate.title || 'Untitled candidate')}</h3>
      <p class="candidate-authors">${escapeHtml(authors || 'Authors unavailable')}</p>
      <div class="evidence-grid"><div><span>DOI</span><strong>${escapeHtml(candidate.doi || '—')}</strong></div><div><span>Name similarity</span><strong>${score}</strong></div><div><span>Matched author</span><strong>${escapeHtml(candidate.matched_author || 'No confident match')}</strong></div><div><span>Discovery source</span><strong>${escapeHtml(candidate.source || '—')}</strong></div></div>
      <p class="review-reason">${escapeHtml(candidate.reason || '')}</p>
      <div class="review-actions">${url ? `<a class="btn primary" href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer">Open DOI / source ↗</a>` : ''}<a class="btn ghost" href="https://github.com/Triyan31/Triyan31.github.io/blob/main/data/academic-review.json" target="_blank" rel="noreferrer">Inspect evidence JSON ↗</a></div>
      ${decisionControls(candidate)}
    </div></article>`;
}
function render(){
  const term = (search.value || '').toLowerCase().trim();
  const mode = filter.value;
  const visible = candidates.filter(c => {
    const haystack = [c.title,c.doi,c.venue,c.publisher,...(c.authors || [])].join(' ').toLowerCase();
    const matchFilter = mode === 'all' || (mode === 'strong' ? c.identity_name_match : !c.identity_name_match);
    return matchFilter && (!term || haystack.includes(term));
  });
  queue.innerHTML = visible.length ? visible.map(card).join('') : `<div class="review-empty">No candidates match this view.</div>`;
  notice.textContent = `${visible.length} of ${candidates.length} candidates shown. A name match is only a discovery signal, never proof of authorship.`;
}
async function copyDecision(doi, action){
  const text = `action=${action}\ndoi=${doi}`;
  try { await navigator.clipboard.writeText(text); } catch (_) {}
  window.open(workflowUrl, '_blank', 'noopener,noreferrer');
}
queue.addEventListener('click', (event) => {
  const button = event.target.closest('[data-decision]');
  if(!button) return;
  const action = button.dataset.decision;
  const doi = button.dataset.doi;
  if(action === 'pending'){
    button.textContent = '✓ Kept for review';
    button.disabled = true;
    return;
  }
  copyDecision(doi, action);
});
async function init(){
  try{
    const response = await fetch('./data/academic-review.json', {cache:'no-cache'});
    if(!response.ok) throw new Error(`HTTP ${response.status}`);
    const report = await response.json();
    candidates = (report.discovered_candidates || []).filter(c => c.verification === 'needs_review');
    renderStats(report); render();
  }catch(error){ notice.textContent = `Unable to load review data: ${error.message}`; queue.innerHTML = '<div class="review-empty">Review queue unavailable.</div>'; }
}
search.addEventListener('input', render); filter.addEventListener('change', render);
const spotlight = document.getElementById('spotlight'); if(spotlight && !matchMedia('(prefers-reduced-motion: reduce)').matches){addEventListener('pointermove',e=>{spotlight.style.left=`${e.clientX}px`;spotlight.style.top=`${e.clientY}px`},{passive:true});}
init();