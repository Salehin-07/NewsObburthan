/* ═══════════════════════════════════════════════════════════════
   ছাত্রকন্ঠ — Search Overlay
   search.js
═══════════════════════════════════════════════════════════════ */
(() => {
  'use strict';

  const overlay   = document.getElementById('ckSearchOverlay');
  const input     = document.getElementById('ckSearchInput');
  const resultBox = document.getElementById('ckSearchResults');
  const closeBtn  = document.getElementById('ckSearchClose');

  if (!overlay || !input || !resultBox) return;

  /* ── Collect posts from data attrs on page ── */
  function collectPosts() {
    return Array.from(document.querySelectorAll('[data-ck-post-title]')).map(el => ({
      title : el.dataset.ckPostTitle,
      url   : el.dataset.ckPostUrl || '#',
      tags  : el.dataset.ckPostTags || '',
    }));
  }

  let posts = [];

  /* ── Open / Close ── */
  function openSearch() {
    posts = collectPosts();
    overlay.classList.add('is-open');
    input.value = '';
    renderHint();
    requestAnimationFrame(() => input.focus());
    document.body.style.overflow = 'hidden';
  }
  function closeSearch() {
    overlay.classList.remove('is-open');
    document.body.style.overflow = '';
    input.blur();
  }

  document.querySelectorAll('[data-ck-search-open]').forEach(btn =>
    btn.addEventListener('click', openSearch)
  );
  if (closeBtn) closeBtn.addEventListener('click', closeSearch);
  overlay.addEventListener('click', e => { if (e.target === overlay) closeSearch(); });

  /* ── Keyboard ── */
  document.addEventListener('keydown', e => {
    const inText = ['INPUT','TEXTAREA','SELECT'].includes(document.activeElement.tagName);
    if ((e.ctrlKey && e.key === 'k') || (e.key === '/' && !inText)) {
      e.preventDefault();
      overlay.classList.contains('is-open') ? closeSearch() : openSearch();
    }
    if (e.key === 'Escape') closeSearch();

    if (!overlay.classList.contains('is-open')) return;
    const items = resultBox.querySelectorAll('.ck-search-result');
    if (!items.length) return;
    const focused = resultBox.querySelector('.ck-search-result.is-focused');
    let idx = Array.from(items).indexOf(focused);

    if (e.key === 'ArrowDown') {
      e.preventDefault();
      idx = (idx + 1) % items.length;
      setFocus(items, idx);
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      idx = (idx - 1 + items.length) % items.length;
      setFocus(items, idx);
    } else if (e.key === 'Enter' && focused) {
      e.preventDefault();
      focused.click();
    }
  });

  function setFocus(items, idx) {
    items.forEach(i => i.classList.remove('is-focused'));
    items[idx].classList.add('is-focused');
    items[idx].scrollIntoView({ block: 'nearest' });
  }

  /* ── Search logic ── */
  function normalize(str) { return str.trim().toLowerCase(); }

  function search(query) {
    const q = normalize(query);
    if (!q) return [];
    const tokens = q.split(/\s+/).filter(Boolean);
    return posts
      .map(post => {
        const t = normalize(post.title);
        let score = 0;
        if (t.includes(q)) score = 100;
        else if (tokens.every(tk => t.includes(tk))) score = 60;
        else {
          const matched = tokens.filter(tk => t.includes(tk)).length;
          score = (matched / tokens.length) * 40;
        }
        return { post, score, tokens };
      })
      .filter(r => r.score > 0)
      .sort((a, b) => b.score - a.score)
      .slice(0, 10);
  }

  function highlight(title, tokens) {
    let esc = title.replace(/[<>&"]/g, c =>
      ({ '<':'&lt;', '>':'&gt;', '&':'&amp;', '"':'&quot;' }[c])
    );
    tokens.forEach(t => {
      const re = new RegExp(`(${t.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
      esc = esc.replace(re, '<mark>$1</mark>');
    });
    return esc;
  }

  /* ── Render ── */
  function renderHint() {
    resultBox.innerHTML = `
      <div class="ck-search-box__hint">
        এই পৃষ্ঠার সংবাদ শিরোনামে অনুসন্ধান করুন
      </div>
      <div class="ck-search-box__footer">
        <span class="ck-search-box__footer-tip"><kbd>↑</kbd><kbd>↓</kbd> নেভিগেট</span>
        <span class="ck-search-box__footer-tip"><kbd>Enter</kbd> খুলুন</span>
        <span class="ck-search-box__footer-tip"><kbd>Esc</kbd> বন্ধ</span>
      </div>`;
  }

  function renderEmpty(q) {
    resultBox.innerHTML = `
      <div class="ck-search-box__empty">"<strong>${q}</strong>" — কোনো সংবাদ পাওয়া যায়নি</div>
      <div class="ck-search-box__footer">
        <span class="ck-search-box__footer-tip"><kbd>Esc</kbd> বন্ধ</span>
      </div>`;
  }

  function renderResults(results, tokens) {
    const items = results.map((r, i) => `
      <div class="ck-search-result" data-url="${r.post.url}" role="option" tabindex="-1">
        <span class="ck-search-result__num">${String(i+1).padStart(2,'0')}</span>
        <div class="ck-search-result__body">
          <div class="ck-search-result__title">${highlight(r.post.title, tokens)}</div>
          ${r.post.tags ? `<div class="ck-search-result__tag">${r.post.tags.split(',')[0]}</div>` : ''}
        </div>
        <svg class="ck-search-result__arrow" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" width="14" height="14"><path d="M3 8h10M9 4l4 4-4 4"/></svg>
      </div>
    `).join('');

    resultBox.innerHTML = items + `
      <div class="ck-search-box__footer">
        <span class="ck-search-box__footer-tip"><kbd>↑</kbd><kbd>↓</kbd> নেভিগেট</span>
        <span class="ck-search-box__footer-tip"><kbd>Enter</kbd> খুলুন</span>
        <span class="ck-search-box__footer-tip"><kbd>Esc</kbd> বন্ধ</span>
      </div>`;

    resultBox.querySelectorAll('.ck-search-result').forEach(item => {
      item.addEventListener('click', () => {
        const url = item.dataset.url;
        if (url && url !== '#') { closeSearch(); window.location.href = url; }
      });
    });
  }

  /* ── Debounced input ── */
  let timer;
  input.addEventListener('input', () => {
    clearTimeout(timer);
    timer = setTimeout(() => {
      const q = input.value.trim();
      if (!q) { renderHint(); return; }
      const results = search(q);
      if (!results.length) renderEmpty(q);
      else renderResults(results, normalize(q).split(/\s+/));
    }, 100);
  });
})();
