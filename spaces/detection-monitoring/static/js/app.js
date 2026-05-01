import { $, renderTabs, renderInfoPage, renderLeaderboard, renderKnowledgeCheck, wireKnowledgeCheck, fetchJSON, renderPreviewBanner } from './core.js';
import { renderLogAnalysisTab } from './log_viewer.js';
import { renderAnomalyTab } from './anomaly_dashboard.js';
import { renderOutputSanitizerTab } from './output_sanitizer.js';
import { detectPreviewToken } from './exam_mode.js';
import { initFirebaseAuth, getIdToken } from './firebase_auth.js';

const TABS = [
  { id: 'info',     label: 'Info' },
  { id: 'logs',     label: 'Log Analysis' },
  { id: 'anomaly',  label: 'Anomaly Detection' },
  { id: 'outputs',  label: 'Output Sanitization' },
  { id: 'scores',   label: 'Leaderboard' },
];

async function init() {
  // Firebase auth gate — resolves immediately if auth is disabled
  const fbUser = await initFirebaseAuth();
  if (fbUser) {
    const _fbFetch = window.fetch;
    window.fetch = async (url, opts = {}) => {
      const headers = { ...(opts.headers || {}) };
      const token = await getIdToken().catch(() => null);
      if (token) headers['Authorization'] = `Bearer ${token}`;
      return _fbFetch(url, { ...opts, headers });
    };
  }

  const previewToken = detectPreviewToken();
  if (previewToken) {
    renderPreviewBanner();
    const _origFetch = window.fetch;
    window.fetch = (url, opts = {}) => {
      opts.headers = { ...(opts.headers || {}), 'X-Preview-Token': previewToken };
      return _origFetch(url, opts);
    };
  }

  // Cold-start health probe
  try {
    const health = await fetchJSON('/health');
    if (health.status !== 'ok') throw new Error();
  } catch {
    const banner = document.getElementById('cold-start-banner');
    if (banner) banner.style.display = '';
    await waitForHealth();
    const banner2 = document.getElementById('cold-start-banner');
    if (banner2) banner2.style.display = 'none';
  }

  renderTabs(TABS, 'info', renderTab);
}

async function waitForHealth(retries = 20, delay = 1500) {
  for (let i = 0; i < retries; i++) {
    await new Promise(r => setTimeout(r, delay));
    try {
      const h = await fetchJSON('/health');
      if (h.status === 'ok') return;
    } catch {}
  }
}

function renderTab(tabId) {
  const container = document.getElementById('tab-content');
  if (!container) return;

  switch (tabId) {
    case 'info':     renderInfoTab(container); break;
    case 'logs':     renderLogAnalysisTab(container); break;
    case 'anomaly':  renderAnomalyTab(container); break;
    case 'outputs':  renderOutputSanitizerTab(container); break;
    case 'scores':   renderLeaderboard(container, '/api/leaderboard', ['D1', 'D2', 'D3']); break;
  }
}

function renderInfoTab(container) {
  const INFO_DATA = {
    eyebrow: 'NexaCore AI Operations Center',
    title: 'Detection & Monitoring Lab',
    subtitle: 'Practice detecting AI attacks in realistic production telemetry across three detection surfaces.',
    learningObjectives: [
      'Identify prompt injection, PII exfiltration, and jailbreak attempts in production AI logs',
      'Configure behavioral alerting thresholds to detect anomalous LLM activity',
      'Write output sanitization rules that block sensitive content without false-positiving on legitimate responses',
      'Explain the tradeoff between recall (catching all attacks) and precision (avoiding false alarms)',
      'Distinguish which monitoring layer — input log, behavioral baseline, or output filter — is best suited to detect each attack class',
    ],
    crossLabNav: {
      current: 'detection-monitoring',
      labs: [
        { id: 'red-team',    label: 'Red Team',           desc: 'Launch attacks' },
        { id: 'blue-team',   label: 'Blue Team',          desc: 'Build defenses' },
        { id: 'multimodal',  label: 'Multimodal',         desc: 'Vision attacks' },
        { id: 'data-poison', label: 'Data Poisoning',     desc: 'RAG attacks' },
        { id: 'detection-monitoring', label: 'Detection & Monitoring', desc: 'You are here', current: true },
      ],
    },
    concepts: [
      {
        name: 'AI Telemetry',
        def: 'Recording model inputs, outputs, latency, and metadata for security audit.',
        analogy: 'Like web server access logs, but for every LLM call.',
      },
      {
        name: 'Behavioral Baselines',
        def: 'Statistical profiles of normal model behavior; deviations signal attacks.',
        analogy: 'Like a network anomaly detector that learns "normal" traffic first.',
      },
      {
        name: 'False Positive Rate',
        def: 'Fraction of legitimate queries incorrectly flagged as attacks.',
        analogy: 'The cost of a too-sensitive smoke alarm: users stop trusting it.',
      },
      {
        name: 'Output Sanitization',
        def: 'Post-processing model outputs to remove sensitive or dangerous content.',
        analogy: 'Like a DLP filter at the email gateway — blocks outbound sensitive data.',
      },
      {
        name: 'Defense-in-Depth',
        def: 'Layering detection at input, behavior, and output — no single layer is sufficient.',
        analogy: 'Like airport security: ticket check + metal detector + gate scan.',
      },
    ],
    architectureDiagram: buildArchDiagram(),
    guidedPractice: [
      { step: 1, title: 'Read a log entry', desc: 'Open Log Analysis. Each card shows a user query and model response from NexaCore\'s AI tools.' },
      { step: 2, title: 'Classify it', desc: 'Click ATTACK or LEGITIMATE. A WHY card reveals immediately — you don\'t need to submit all 20 first.' },
      { step: 3, title: 'Configure anomaly alerts', desc: 'In Anomaly Detection, set high/low thresholds for each metric. Try to catch all 3 attack windows without too many false alarms.' },
      { step: 4, title: 'Write output sanitization rules', desc: 'In Output Sanitization, write BLOCK regex rules to catch dangerous model outputs. Same DSL as the Blue Team WAF challenge.' },
      { step: 5, title: 'Check your score', desc: 'D1 and D3 use F1 scoring. D2 scores by attack window detection minus false alarm penalty. Max 300 pts total.' },
    ],
    assumedKnowledge: 'Familiarity with regex basics (same as the Blue Team WAF challenge); no ML expertise required. Knowledge of HTTP and JSON is helpful for understanding the attack context.',
    knowledgeCheck: [
      {
        question: 'Which metric best signals a data exfiltration attack where the model is producing verbose outputs?',
        options: ['Refusal rate drop', 'Response length spike', 'Query rate spike'],
        answer: 1,
        explanation: 'Data exfiltration via verbose outputs manifests as unusually long model responses. The model is being coaxed into producing structured data (CSV, JSON, encoded strings) that smuggles information out.',
      },
      {
        question: 'A rule that catches 100% of attacks but also flags 50% of legitimate outputs has:',
        options: ['High recall, low precision', 'Low recall, high precision', 'High F1 score'],
        answer: 0,
        explanation: 'Recall = fraction of attacks caught (100% = high recall). Precision = fraction of blocked outputs that were actual attacks (50% true, 50% false positive = low precision). High F1 requires both.',
      },
      {
        question: 'Output sanitization is:',
        options: ['A replacement for input filtering', 'A last line of defense', 'Sufficient on its own'],
        answer: 1,
        explanation: 'Output sanitization catches what other layers miss — it blocks sensitive content before it reaches the end user. But attackers who bypass input filters and cause the model to generate dangerous content need this final layer.',
      },
    ],
  };

  renderInfoPage(container, INFO_DATA);
  wireKnowledgeCheck(container);
}

function buildArchDiagram() {
  return `
  <div class="arch-diagram">
    <div class="arch-row">
      <div class="arch-box">User Query</div>
      <div class="arch-arrow">→</div>
      <span class="arch-tap">D1/D3: input monitor</span>
      <div class="arch-arrow">→</div>
      <div class="arch-box arch-box--llm">LLM</div>
      <div class="arch-arrow">→</div>
      <span class="arch-tap">D2: behavioral monitor</span>
      <div class="arch-arrow">→</div>
      <span class="arch-tap">D3: output sanitizer</span>
      <div class="arch-arrow">→</div>
      <div class="arch-box">Response</div>
    </div>
    <div style="font-size:var(--text-xs);color:var(--color-text-muted);text-align:center;margin-top:var(--space-2)">
      Three monitoring layers — input classification (D1), behavioral anomaly detection (D2), output filtering (D3)
    </div>
  </div>`;
}

init();
