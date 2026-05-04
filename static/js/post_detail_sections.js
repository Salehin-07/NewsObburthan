/* ═══════════════════════════════════════════════════════════════
   ছাত্রকন্ঠ — Bottom Sections JS  (dao__ scoped)
   Handles scroll-reveal for .dao__card elements only.
   Completely isolated — touches nothing outside dao__ namespace.
═══════════════════════════════════════════════════════════════ */
(function dao__init() {
  'use strict';

  /* ── Staggered card reveal on scroll ── */
  var cards = document.querySelectorAll('.dao__card');
  if (!cards.length) return;

  if (!('IntersectionObserver' in window)) {
    /* Fallback: show all immediately */
    cards.forEach(function(c) {
      c.style.opacity = '1';
      c.style.transform = 'none';
    });
    return;
  }

  var io = new IntersectionObserver(function(entries) {
    entries.forEach(function(entry) {
      if (!entry.isIntersecting) return;
      var card = entry.target;
      /* Get stagger index from data attribute set below */
      var idx = parseInt(card.getAttribute('data-dao-idx') || '0', 10);
      card.style.animationDelay = (idx * 70) + 'ms';
      card.classList.add('dao__card--in');
      io.unobserve(card);
    });
  }, { threshold: 0.08 });

  cards.forEach(function(card, i) {
    card.setAttribute('data-dao-idx', i);
    io.observe(card);
  });

})();
