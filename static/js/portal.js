/* portal.js — Tab switching logic */
(function () {
  const tabs   = document.querySelectorAll('.pt-tab');
  const panels = document.querySelectorAll('.pt-panel');

  function activate(tabId) {
    tabs.forEach(t => t.classList.toggle('pt-tab--active', t.dataset.tab === tabId));
    panels.forEach(p => p.classList.toggle('pt-panel--active', p.id === 'panel-' + tabId));
  }

  tabs.forEach(tab => {
    tab.addEventListener('click', () => activate(tab.dataset.tab));
  });

  // Auto-open correct panel if URL has hash (#panel-rep)
  const hash = window.location.hash;
  if (hash === '#panel-rep') activate('rep');

  // File input: show chosen filename
  const fileInput = document.getElementById('rep_cv');
  const fileText  = document.querySelector('.pt-file-label__text');
  if (fileInput && fileText) {
    fileInput.addEventListener('change', () => {
      const name = fileInput.files[0]?.name;
      if (name) fileText.innerHTML = `<strong>${name}</strong><small>ফাইল নির্বাচিত হয়েছে</small>`;
    });
  }
})();
