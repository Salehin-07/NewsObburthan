/* ═══════════════════════════════════════════════════════════════
   ছাত্রকন্ঠ — Post Detail JS
   post_detail.js
═══════════════════════════════════════════════════════════════ */
(() => {
  'use strict';

  /* ── Reading progress bar ── */
  const bar = document.getElementById('ckReadingProgress');
  if (bar) {
    window.addEventListener('scroll', () => {
      const doc = document.documentElement;
      const scrolled = doc.scrollTop / (doc.scrollHeight - doc.clientHeight);
      bar.style.width = Math.min(100, scrolled * 100) + '%';
    }, { passive: true });
  }

  /* ── Copy link button ── */
  document.getElementById('ckCopyLink')?.addEventListener('click', function() {
    navigator.clipboard.writeText(window.location.href).then(() => {
      this.classList.add('is-copied');
      const txt = this.querySelector('.ck-share-btn__label');
      if (txt) { const orig = txt.textContent; txt.textContent = 'কপি হয়েছে!'; setTimeout(() => { txt.textContent = orig; this.classList.remove('is-copied'); }, 2000); }
    });
  });
})();
