/**
 * firebase_auth.js — Firebase Auth gate for AI Security Labs.
 *
 * Call initFirebaseAuth() at the top of DOMContentLoaded. Resolves once
 * the user is authenticated (showing a sign-in overlay if needed) or
 * immediately with null when auth is disabled (no FIREBASE_API_KEY).
 *
 * Supported sign-in methods:
 *   Email magic link · Google OAuth · GitHub OAuth · Phone / SMS OTP
 *
 * Security note: innerHTML is used only for developer-authored static markup.
 * User-supplied values (email, phone) are set via .value / textContent only.
 */

import { initializeApp, getApps }
  from 'https://www.gstatic.com/firebasejs/10.12.0/firebase-app.js';
import {
  getAuth, onAuthStateChanged,
  isSignInWithEmailLink, sendSignInLinkToEmail, signInWithEmailLink,
  GoogleAuthProvider, GithubAuthProvider, signInWithPopup,
  signInWithPhoneNumber, RecaptchaVerifier,
  signOut as _fbSignOut,
} from 'https://www.gstatic.com/firebasejs/10.12.0/firebase-auth.js';

// Module state
let _auth = null;
let _currentUser = null;

// ─── Public API ───────────────────────────────────────────────────────────────

export async function initFirebaseAuth() {
  const config = await _fetchConfig();
  if (!config) return null;

  _auth = _initApp(config);

  if (isSignInWithEmailLink(_auth, window.location.href)) {
    return _completeEmailLinkSignIn();
  }

  const existing = await _getAuthState();
  if (existing) { _currentUser = existing; return existing; }

  return _showSignInOverlay();
}

export async function getIdToken() {
  if (!_currentUser) return null;
  try { return await _currentUser.getIdToken(); }
  catch { return null; }
}

export function getCurrentUser() { return _currentUser; }

export async function signOut() {
  if (_auth) await _fbSignOut(_auth);
  _currentUser = null;
  window.location.reload();
}

// ─── Config ───────────────────────────────────────────────────────────────────

async function _fetchConfig() {
  try {
    const r = await fetch('/api/firebase-config');
    if (!r.ok) return null;
    const cfg = await r.json();
    return cfg.enabled ? cfg : null;
  } catch { return null; }
}

function _initApp(config) {
  const app = getApps().length ? getApps()[0] : initializeApp(config);
  return getAuth(app);
}

function _getAuthState() {
  return new Promise(resolve => {
    const unsub = onAuthStateChanged(_auth, user => { unsub(); resolve(user); });
  });
}

// ─── Email link completion ────────────────────────────────────────────────────

async function _completeEmailLinkSignIn() {
  let email = window.localStorage.getItem('fba_email');
  if (!email) {
    email = window.prompt('Enter the email address you used to request the sign-in link:');
  }
  if (!email) return null;
  try {
    const result = await signInWithEmailLink(_auth, email, window.location.href);
    window.localStorage.removeItem('fba_email');
    window.history.replaceState({}, '', window.location.pathname);
    _currentUser = result.user;
    return result.user;
  } catch (e) {
    console.error('Email link sign-in failed:', e.message);
    window.history.replaceState({}, '', window.location.pathname);
    // Link expired/used — fall through to sign-in overlay so user can retry
    return await _showSignInOverlay();
  }
}

// ─── Sign-in overlay ──────────────────────────────────────────────────────────

function _showSignInOverlay() {
  _injectStyles();
  return new Promise(resolve => {
    const overlay = _buildOverlay(user => {
      _currentUser = user;
      overlay.remove();
      resolve(user);
    });
    document.body.appendChild(overlay);
  });
}

function _buildOverlay(onAuth) {
  const wrap = document.createElement('div');
  wrap.id = 'fba-overlay';

  // Backdrop + panel
  const bd = document.createElement('div'); bd.className = 'fba-backdrop';
  const panel = document.createElement('div');
  panel.className = 'fba-panel';
  panel.setAttribute('role', 'dialog');
  panel.setAttribute('aria-modal', 'true');
  panel.setAttribute('aria-labelledby', 'fba-title');

  // Brand block
  const brand = document.createElement('div'); brand.className = 'fba-brand';
  const owl = document.createElement('img');
  owl.src = '/static/owl.svg'; owl.alt = ''; owl.className = 'fba-owl owl-gold';
  owl.setAttribute('aria-hidden', 'true');
  owl.onerror = () => { owl.style.display = 'none'; };
  const bt = document.createElement('div'); bt.className = 'fba-brand-text';
  const wm = document.createElement('span'); wm.className = 'fba-wordmark'; wm.textContent = 'Luminex Learning';
  const pn = document.createElement('span'); pn.className = 'fba-product'; pn.textContent = 'AI Security Labs';
  bt.append(wm, pn); brand.append(owl, bt);

  // Title
  const title = document.createElement('h1'); title.id = 'fba-title'; title.className = 'fba-title'; title.textContent = 'Sign in to continue';

  // Steps
  const stepMain = _buildStepMain();
  const stepEmailSent = _buildStepEmailSent();
  const stepSms = _buildStepSms();

  // Error
  const errEl = document.createElement('div'); errEl.id = 'fba-error'; errEl.className = 'fba-error'; errEl.setAttribute('aria-live', 'polite');

  panel.append(brand, title, stepMain, stepEmailSent, stepSms, errEl);
  bd.appendChild(panel); wrap.appendChild(bd);

  _wireOverlay(wrap, stepMain, stepEmailSent, stepSms, errEl, onAuth);
  return wrap;
}

function _buildStepMain() {
  const s = document.createElement('div'); s.id = 'fba-step-main'; s.className = 'fba-step fba-step--active';

  // Email section
  const emailSec = document.createElement('div'); emailSec.className = 'fba-section';
  const emailLbl = document.createElement('label'); emailLbl.htmlFor = 'fba-email'; emailLbl.className = 'fba-label'; emailLbl.textContent = 'Email magic link';
  const emailRow = document.createElement('div'); emailRow.className = 'fba-row';
  const emailInput = document.createElement('input');
  emailInput.type = 'email'; emailInput.id = 'fba-email'; emailInput.className = 'fba-input';
  emailInput.placeholder = 'you@university.edu'; emailInput.autocomplete = 'email';
  const magicBtn = document.createElement('button'); magicBtn.id = 'fba-magic-btn'; magicBtn.className = 'fba-btn fba-btn--primary'; magicBtn.textContent = 'Send link';
  emailRow.append(emailInput, magicBtn); emailSec.append(emailLbl, emailRow);

  // Divider 1
  const div1 = _divider('or');

  // Social buttons
  const socialRow = document.createElement('div'); socialRow.className = 'fba-social-row';
  const gBtn = document.createElement('button'); gBtn.id = 'fba-google-btn'; gBtn.className = 'fba-btn fba-btn--social';
  gBtn.innerHTML = '<svg class="fba-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/><path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/><path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/><path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/></svg>';
  gBtn.append(document.createTextNode(' Google'));
  const ghBtn = document.createElement('button'); ghBtn.id = 'fba-github-btn'; ghBtn.className = 'fba-btn fba-btn--social';
  ghBtn.innerHTML = '<svg class="fba-icon" viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61C4.422 18.07 3.633 17.7 3.633 17.7c-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.606-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 22.092 24 17.592 24 12.297c0-6.627-5.373-12-12-12"/></svg>';
  ghBtn.append(document.createTextNode(' GitHub'));
  socialRow.append(gBtn, ghBtn);

  // Divider 2
  const div2 = _divider('or SMS');

  // Phone section
  const phoneSec = document.createElement('div'); phoneSec.className = 'fba-section';
  const phoneLbl = document.createElement('label'); phoneLbl.htmlFor = 'fba-phone'; phoneLbl.className = 'fba-label'; phoneLbl.textContent = 'Phone number';
  const phoneRow = document.createElement('div'); phoneRow.className = 'fba-row';
  const phoneInput = document.createElement('input');
  phoneInput.type = 'tel'; phoneInput.id = 'fba-phone'; phoneInput.className = 'fba-input';
  phoneInput.placeholder = '+1 555 000 0000'; phoneInput.autocomplete = 'tel';
  const phoneBtn = document.createElement('button'); phoneBtn.id = 'fba-phone-btn'; phoneBtn.className = 'fba-btn fba-btn--secondary'; phoneBtn.textContent = 'Send code';
  phoneRow.append(phoneInput, phoneBtn);
  const rcDiv = document.createElement('div'); rcDiv.id = 'fba-recaptcha';
  phoneSec.append(phoneLbl, phoneRow, rcDiv);

  s.append(emailSec, div1, socialRow, div2, phoneSec);
  return s;
}

function _buildStepEmailSent() {
  const s = document.createElement('div'); s.id = 'fba-step-email-sent'; s.className = 'fba-step';
  const icon = document.createElement('div'); icon.className = 'fba-check'; icon.textContent = '✉';
  const msg = document.createElement('p'); msg.className = 'fba-msg'; msg.textContent = 'Magic link sent — check your inbox and click the link to sign in.';
  const back = document.createElement('button'); back.id = 'fba-back-btn'; back.className = 'fba-btn fba-btn--ghost'; back.textContent = 'Use a different method';
  s.append(icon, msg, back);
  return s;
}

function _buildStepSms() {
  const s = document.createElement('div'); s.id = 'fba-step-sms'; s.className = 'fba-step';
  const msg = document.createElement('p'); msg.className = 'fba-msg';
  const msgText = document.createTextNode('Code sent to ');
  const strong = document.createElement('strong'); strong.id = 'fba-phone-display';
  msg.append(msgText, strong);
  const lbl = document.createElement('label'); lbl.htmlFor = 'fba-otp'; lbl.className = 'fba-label'; lbl.textContent = '6-digit code';
  const otp = document.createElement('input');
  otp.type = 'text'; otp.id = 'fba-otp'; otp.className = 'fba-input fba-otp-input';
  otp.placeholder = '000000'; otp.setAttribute('inputmode', 'numeric');
  otp.maxLength = 6; otp.autocomplete = 'one-time-code';
  const verify = document.createElement('button'); verify.id = 'fba-otp-btn'; verify.className = 'fba-btn fba-btn--primary'; verify.textContent = 'Verify';
  const back = document.createElement('button'); back.id = 'fba-sms-back-btn'; back.className = 'fba-btn fba-btn--ghost'; back.textContent = 'Back';
  s.append(msg, lbl, otp, verify, back);
  return s;
}

function _divider(text) {
  const d = document.createElement('div'); d.className = 'fba-divider';
  const span = document.createElement('span'); span.textContent = text;
  d.appendChild(span); return d;
}

let _smsConfirmation = null;

function _wireOverlay(wrap, stepMain, stepEmailSent, stepSms, errEl, onAuth) {
  const show = step => {
    [stepMain, stepEmailSent, stepSms].forEach(s => s.classList.remove('fba-step--active'));
    step.classList.add('fba-step--active');
  };
  const err = msg => { errEl.textContent = msg || ''; };

  wrap.querySelector('#fba-magic-btn').addEventListener('click', async () => {
    const email = wrap.querySelector('#fba-email').value.trim();
    if (!email) { err('Enter your email address.'); return; }
    err();
    try {
      await sendSignInLinkToEmail(_auth, email, { url: window.location.href, handleCodeInApp: true });
      window.localStorage.setItem('fba_email', email);
      show(stepEmailSent);
    } catch (e) { err(e.message); }
  });

  wrap.querySelector('#fba-back-btn').addEventListener('click', () => { show(stepMain); err(); });

  wrap.querySelector('#fba-google-btn').addEventListener('click', async () => {
    err();
    try { const r = await signInWithPopup(_auth, new GoogleAuthProvider()); onAuth(r.user); }
    catch (e) { if (e.code !== 'auth/popup-closed-by-user') err(e.message); }
  });

  wrap.querySelector('#fba-github-btn').addEventListener('click', async () => {
    err();
    try { const r = await signInWithPopup(_auth, new GithubAuthProvider()); onAuth(r.user); }
    catch (e) { if (e.code !== 'auth/popup-closed-by-user') err(e.message); }
  });

  wrap.querySelector('#fba-phone-btn').addEventListener('click', async () => {
    const phone = wrap.querySelector('#fba-phone').value.trim();
    if (!phone) { err('Enter a phone number in E.164 format (e.g. +15550001234).'); return; }
    err();
    try {
      if (!window._fbRecaptcha) {
        window._fbRecaptcha = new RecaptchaVerifier(_auth, 'fba-recaptcha', { size: 'invisible' });
      }
      _smsConfirmation = await signInWithPhoneNumber(_auth, phone, window._fbRecaptcha);
      wrap.querySelector('#fba-phone-display').textContent = phone;
      show(stepSms);
    } catch (e) {
      if (window._fbRecaptcha) { window._fbRecaptcha.clear(); window._fbRecaptcha = null; }
      err(e.message);
    }
  });

  wrap.querySelector('#fba-otp-btn').addEventListener('click', async () => {
    const code = wrap.querySelector('#fba-otp').value.trim();
    if (!code) { err('Enter the 6-digit code.'); return; }
    err();
    try { const r = await _smsConfirmation.confirm(code); onAuth(r.user); }
    catch (e) { err(e.message); }
  });

  wrap.querySelector('#fba-sms-back-btn').addEventListener('click', () => { show(stepMain); err(); });
}

// ─── Injected styles ──────────────────────────────────────────────────────────

function _injectStyles() {
  if (document.getElementById('fba-styles')) return;
  const s = document.createElement('style');
  s.id = 'fba-styles';
  s.textContent = [
    '#fba-overlay{position:fixed;inset:0;z-index:9999;display:flex;align-items:center;justify-content:center;background:var(--color-bg-base,#09090f);font-family:var(--font-sans,"Inter",system-ui,sans-serif)}',
    '.fba-backdrop{width:100%;display:flex;align-items:center;justify-content:center;padding:24px}',
    '.fba-panel{background:var(--color-surface-1,#141416);border:1px solid var(--color-border,#27272a);border-radius:12px;padding:32px 28px;width:100%;max-width:420px;box-shadow:0 24px 60px rgba(0,0,0,.6)}',
    '.fba-brand{display:flex;align-items:center;gap:10px;margin-bottom:24px}',
    '.fba-owl{height:36px;width:auto;flex-shrink:0}',
    '.fba-wordmark{display:block;font-size:12px;font-weight:700;color:var(--color-text-primary,#f4f4f5);letter-spacing:-.02em}',
    '.fba-product{display:block;font-size:10px;font-weight:500;color:var(--color-text-secondary,#a1a1aa);letter-spacing:.04em;margin-top:2px}',
    '.fba-title{font-size:20px;font-weight:600;color:var(--color-text-primary,#f4f4f5);margin:0 0 20px;letter-spacing:-.02em}',
    '.fba-step{display:none;flex-direction:column;gap:12px}',
    '.fba-step--active{display:flex}',
    '.fba-section{display:flex;flex-direction:column;gap:6px}',
    '.fba-label{font-size:12px;font-weight:500;color:var(--color-text-secondary,#a1a1aa)}',
    '.fba-row{display:flex;gap:8px}',
    '.fba-input{flex:1;background:var(--color-bg-base,#09090f);border:1px solid var(--color-border,#27272a);border-radius:6px;color:var(--color-text-primary,#f4f4f5);font-family:inherit;font-size:14px;padding:8px 12px;outline:none;transition:border-color .15s}',
    '.fba-input:focus{border-color:var(--color-accent-aisl-highlight,#a78bfa)}',
    '.fba-otp-input{letter-spacing:.3em;font-family:var(--font-mono,"JetBrains Mono",monospace);font-size:18px;text-align:center;max-width:160px;align-self:center}',
    '.fba-btn{border:none;border-radius:6px;cursor:pointer;font-family:inherit;font-size:13px;font-weight:600;padding:8px 16px;transition:opacity .15s;white-space:nowrap}',
    '.fba-btn:disabled{opacity:.5;cursor:not-allowed}',
    '.fba-btn--primary{background:var(--color-accent-aisl-highlight,#a78bfa);color:#09090f}',
    '.fba-btn--primary:hover:not(:disabled){opacity:.88}',
    '.fba-btn--secondary{background:var(--color-surface-2,#1c1c1f);color:var(--color-text-primary,#f4f4f5);border:1px solid var(--color-border,#27272a)}',
    '.fba-btn--ghost{background:transparent;color:var(--color-text-secondary,#a1a1aa);font-weight:400;font-size:12px;padding:6px 0;text-decoration:underline}',
    '.fba-btn--ghost:hover{color:var(--color-text-primary,#f4f4f5)}',
    '.fba-social-row{display:flex;gap:8px}',
    '.fba-btn--social{flex:1;display:flex;align-items:center;justify-content:center;gap:8px;background:var(--color-surface-2,#1c1c1f);border:1px solid var(--color-border,#27272a);color:var(--color-text-primary,#f4f4f5)}',
    '.fba-btn--social:hover:not(:disabled){border-color:var(--color-border-strong,#3f3f46)}',
    '.fba-icon{width:16px;height:16px;flex-shrink:0}',
    '.fba-divider{display:flex;align-items:center;gap:10px;font-size:11px;color:var(--color-text-secondary,#a1a1aa)}',
    '.fba-divider::before,.fba-divider::after{content:"";flex:1;height:1px;background:var(--color-border,#27272a)}',
    '.fba-check{font-size:36px;text-align:center}',
    '.fba-msg{font-size:14px;color:var(--color-text-secondary,#a1a1aa);text-align:center;margin:0}',
    '.fba-error{min-height:18px;font-size:12px;color:#f87171;margin-top:4px}',
    '@media(max-width:480px){.fba-panel{padding:24px 20px}.fba-social-row{flex-direction:column}}',
  ].join('');
  document.head.appendChild(s);
}
