/* Academic Review integrity boundary.
 * Decision history is authoritative UI state. If it cannot be fetched,
 * review.js must enter its existing unavailable/read-only error path rather
 * than treating the history as empty.
 */
(function installAcademicReviewIntegrity(global) {
  'use strict';

  const DECISIONS_PATH = '/data/academic-decisions.json';
  const nativeFetch = global.fetch.bind(global);

  function isDecisionHistoryRequest(input) {
    const raw = typeof input === 'string' ? input : (input && input.url) || '';
    try {
      const url = new URL(raw, global.location.href);
      return url.pathname.endsWith(DECISIONS_PATH);
    } catch (_) {
      return String(raw).includes('academic-decisions.json');
    }
  }

  function requireDecisionHistoryResponse(response) {
    if (!response || !response.ok) {
      const status = response && response.status ? ` HTTP ${response.status}` : '';
      throw new Error(`decision history unavailable${status}`);
    }
    return response;
  }

  global.AcademicReviewIntegrity = Object.freeze({
    isDecisionHistoryRequest,
    requireDecisionHistoryResponse,
  });

  global.fetch = async function failClosedAcademicFetch(input, init) {
    const response = await nativeFetch(input, init);
    return isDecisionHistoryRequest(input)
      ? requireDecisionHistoryResponse(response)
      : response;
  };
})(window);
