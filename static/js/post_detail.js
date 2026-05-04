/* ═══════════════════════════════════════════════════════════════
   ছাত্রকন্ঠ — Post Detail JS
   post_detail.js
═══════════════════════════════════════════════════════════════ */
(() => {
  'use strict';

  /* ── Reading progress bar ── */
  const bar = document.getElementById('ckReadingProgress');
  if (bar) {
    const updateProgress = () => {
      const doc = document.documentElement;
      const scrollable = doc.scrollHeight - doc.clientHeight;
      if (scrollable <= 0) { bar.style.width = '100%'; return; }
      const pct = Math.min(100, (doc.scrollTop / scrollable) * 100);
      bar.style.width = pct + '%';
    };
    window.addEventListener('scroll', updateProgress, { passive: true });
    updateProgress(); // run once on load
  }

  /* ── Copy link button ── */
  const copyBtn = document.getElementById('ckCopyLink');
  if (copyBtn) {
    copyBtn.addEventListener('click', function () {
      navigator.clipboard.writeText(window.location.href).then(() => {
        const label = this.querySelector('.ck-share-btn__label');
        const origText = label ? label.textContent : null;
        this.classList.add('is-copied');
        if (label) label.textContent = 'কপি হয়েছে!';
        setTimeout(() => {
          this.classList.remove('is-copied');
          if (label && origText) label.textContent = origText;
        }, 2200);
      }).catch(() => {
        /* Fallback for older browsers */
        const ta = document.createElement('textarea');
        ta.value = window.location.href;
        ta.style.cssText = 'position:fixed;opacity:0;pointer-events:none';
        document.body.appendChild(ta);
        ta.select();
        document.execCommand('copy');
        document.body.removeChild(ta);
      });
    });
  }

  /* ── Animate "more posts" cards on scroll ── */
  const cards = document.querySelectorAll('.ck-post-card');
  if (cards.length && 'IntersectionObserver' in window) {
    const io = new IntersectionObserver((entries) => {
      entries.forEach((entry, i) => {
        if (entry.isIntersecting) {
          entry.target.style.animationDelay = (i * 60) + 'ms';
          entry.target.classList.add('ck-post-card--visible');
          io.unobserve(entry.target);
        }
      });
    }, { threshold: 0.1 });
    cards.forEach(card => io.observe(card));
  }

})();
