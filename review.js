const escapeHtml = (value = '') => String(value).replace(/[&<>'"]/g, (char) => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[char]));
let candidates = [];
let pendingDecision = null;
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
function candidateByDoi(doi){ return candidates.find(c => c.doi === doi) || {}; }
function closeDecisionDialog(){
  document.querySelector('.decision-confirm-overlay')?.remove();
  pendingDecision = null;
}
function openDecisionDialog(doi, action){
  const candidate = candidateByDoi(doi);
  pendingDecision = {doi, action};
  const approving = action === 'approve';
  const label = approving ? 'Confirm as my article' : 'Mark as not mine';
  const explanation = approving
    ? 'This does not publish the article immediately. The authenticated workflow will still require identity and bibliographic checks to pass.'
    : 'This will submit an authenticated decision that this candidate is not your article.';
  document.body.insertAdjacentHTML('beforeend', `<div class="decision-confirm-overlay" role="presentation">
    <section class="decision-confirm-dialog" role="dialog" aria-modal="true" aria-labelledby="decisionDialogTitle">
      <span class="decision-dialog-kicker">ACADEMIC REVIEW · CONFIRM DECISION</span>
      <h2 id="decisionDialogTitle">${escapeHtml(label)}</h2>
      <div class="decision-dialog-record"><span>Article</span><strong>${escapeHtml(candidate.title || 'Untitled candidate')}</strong><span>DOI</span><code>${escapeHtml(doi)}</code></div>
      <p>${escapeHtml(explanation)}</p>
      <div class="decision-dialog-security"><strong>Authenticated step required</strong><span>GitHub Actions remains the trusted execution layer. No GitHub credential or token is exposed to this page.</span></div>
      <div class="decision-dialog-actions"><button class="btn ghost" type="button" data-dialog-cancel>Cancel</button><button class="btn ${approving ? 'decision approve' : 'decision reject'}" type="button" data-dialog-continue>${approving ? 'Continue: confirm mine' : 'Continue: not mine'} →</button></div>
    </section></div>`);
  document.querySelector('[data-dialog-continue]')?.focus();
}
async function continueDecision(){
  if(!pendingDecision) return;
  const {doi, action} = pendingDecision;
  const text = `action=${action}\ndoi=${doi}`;
  try { await navigator.clipboard.writeText(text); } catch (_) {}
  closeDecisionDialog();
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
  openDecisionDialog(doi, action);
});
document.addEventListener('click', (event) => {
  if(event.target.closest('[data-dialog-cancel]') || (event.target.classList.contains('decision-confirm-overlay'))) closeDecisionDialog();
  if(event.target.closest('[data-dialog-continue]')) continueDecision();
});
document.addEventListener('keydown', (event) => { if(event.key === 'Escape' && pendingDecision) closeDecisionDialog(); });
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