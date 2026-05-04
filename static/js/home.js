/* ═══════════════════════════════════════════════════════════════
   দৈনিক অভ্যুত্থান — Home JS
   home.js  — zero dependencies, ~3 KB minified
   All selectors scoped to .dao-* — zero collision risk
═══════════════════════════════════════════════════════════════ */

(function () {
  'use strict';

  /* ── 1. Ticker: duplicate content for seamless loop ────────── */
  function initTicker() {
    var track = document.querySelector('.dao-ticker__track');
    if (!track) return;
    // Clone so we get continuous loop without gap
    var clone = track.cloneNode(true);
    track.parentNode.appendChild(clone);
  }

  /* ── 2. Scroll-to-top button ───────────────────────────────── */
  function initScrollTop() {
    var btn = document.querySelector('.dao-scroll-top');
    if (!btn) return;

    var threshold = 400;
    var ticking = false;

    function onScroll() {
      if (!ticking) {
        requestAnimationFrame(function () {
          if (window.scrollY > threshold) {
            btn.classList.add('is-visible');
          } else {
            btn.classList.remove('is-visible');
          }
          ticking = false;
        });
        ticking = true;
      }
    }

    window.addEventListener('scroll', onScroll, { passive: true });
    btn.addEventListener('click', function () {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
  }

  /* ── 3. Lazy-load images with native loading + shimmer ─────── */
  function initLazyImages() {
    // Add loading shimmer class while images load
    var wraps = document.querySelectorAll('.dao-card__img-wrap, .dao-hero__img-link');
    wraps.forEach(function (wrap) {
      var img = wrap.querySelector('img');
      if (!img) return;
      if (!img.complete) {
        wrap.classList.add('is-loading');
        img.addEventListener('load', function () {
          wrap.classList.remove('is-loading');
        });
        img.addEventListener('error', function () {
          wrap.classList.remove('is-loading');
        });
      }
    });

    // IntersectionObserver for below-fold cards — fade in on scroll
    if (!window.IntersectionObserver) return;
    var cards = document.querySelectorAll('.dao-card');
    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.style.opacity = '1';
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.08 });

    cards.forEach(function (card, i) {
      // Only observe cards below the fold (rough heuristic: index > 5)
      if (i > 5) {
        card.style.opacity = '0';
        observer.observe(card);
      }
    });
  }

  /* ── 4. Inline ad click tracking (optional NoOp) ──────────── */
  function initAdTracking() {
    var ads = document.querySelectorAll('.dao-ad-inline a, .dao-ad-banner a, .dao-sidebar-ad a');
    ads.forEach(function (a) {
      a.addEventListener('click', function () {
        // Placeholder for analytics; extend as needed
        if (typeof gtag === 'function') {
          gtag('event', 'ad_click', {
            event_category: 'Advertisement',
            event_label: a.href
          });
        }
      });
    });
  }

  /* ── 5. Smooth anchor for pagination ──────────────────────── */
  function initPaginationScroll() {
    var paginationLinks = document.querySelectorAll('.dao-page-btn[href]');
    paginationLinks.forEach(function (link) {
      link.addEventListener('click', function () {
        // Scroll to top of content area on page change
        var content = document.querySelector('.dao-content');
        if (content) {
          setTimeout(function () {
            content.scrollIntoView({ behavior: 'smooth', block: 'start' });
          }, 50);
        }
      });
    });
  }

  /* ── 6. Active tag highlight in cloud ─────────────────────── */
  function initTagCloud() {
    var chips = document.querySelectorAll('.dao-tag-chip');
    var currentPath = window.location.pathname;
    chips.forEach(function (chip) {
      if (chip.getAttribute('href') === currentPath) {
        chip.classList.add('is-active');
      }
    });
  }

  /* ── 7. Reading progress bar (optional — thin top bar) ─────── */
  function initReadingProgress() {
    // Only relevant on post_detail; skip on home
    if (!document.querySelector('.dao-layout')) return;
    // No progress bar on listing pages — keep it clean
  }

  /* ── Init ─────────────────────────────────────────────────── */
  function init() {
    initTicker();
    initScrollTop();
    initLazyImages();
    initAdTracking();
    initPaginationScroll();
    initTagCloud();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

})();
