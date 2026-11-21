'use strict';
(() => {
  const data = window.ELECTION_ARCHIVE;
  if (!data) { document.querySelector('#results-count').textContent = 'The collection could not load. Please refresh the page.'; return; }
  const $ = (id) => document.getElementById(id);
  const collections = new Map(data.collections.map(c => [c.id, c]));
  const imageURL = (m, key = 'image') => `${m[key]}?v=${m.source_sha256.slice(0, 12)}`;
  const filters = ['search', 'state', 'series', 'year'];
  const pageSize = 30;
  let category = '', limit = pageSize, filtered = [], current = null;
  const dialog = $('viewer');
  const params = new URLSearchParams(location.search);
  function option(parent, value, label) { const o = document.createElement('option'); o.value = value; o.textContent = label; parent.append(o); }
  [...new Set(data.images.map(m => m.state))].sort().forEach(s => option($('state'), s, s));
  [...data.collections].sort((a,b) => a.title.localeCompare(b.title)).forEach(c => option($('series'), c.id, c.title));
  [...new Set(data.images.flatMap(m => m.years))].sort().reverse().forEach(y => option($('year'), y, y));
  filters.forEach(id => { const key = id === 'search' ? 'q' : id; if (params.has(key)) $(id).value = params.get(key); });
  category = params.get('category') || '';
  if (![...document.querySelectorAll('.topic')].some(b => b.dataset.category === category)) category = '';
  if (['curated','newest','title'].includes(params.get('sort'))) $('sort').value = params.get('sort');
  $('archive-count').textContent = `${data.images.length.toLocaleString()} works in ${data.collections.length} collections`;
  const featured = data.images.find(m => m.collection === 'southern-nine-state-2026-midterm-clean');
  if (featured) {
    $('featured-image').src = imageURL(featured); $('featured-image').alt = 'Hypothetical nine-state Southern midterm scenario by precinct';
    $('featured-open').href = imageURL(featured); $('featured-caption').textContent = 'The South, precinct by precinct'; $('featured-tag').textContent = 'Hypothetical scenario';
    $('featured-open').addEventListener('click', e => { e.preventDefault(); openMap(featured); });
  }
  function syncURL() {
    const p = new URLSearchParams();
    filters.forEach(id => { if ($(id).value) p.set(id === 'search' ? 'q' : id, $(id).value); });
    if (category) p.set('category',category);
    if ($('sort').value !== 'curated') p.set('sort',$('sort').value);
    history.replaceState(null, '', location.pathname + (p.size ? '?' + p : '') + location.hash);
  }
  function makeCard(m) {
    const col = collections.get(m.collection), article = document.createElement('article'); article.className = 'map-card';
    const a = document.createElement('a'); a.className = 'map-link'; a.href = imageURL(m); a.setAttribute('aria-label', 'View '+m.title);
    const img = document.createElement('img'); img.src = imageURL(m, 'thumbnail'); img.alt = m.title; img.loading = 'lazy'; img.decoding = 'async'; img.width = m.width; img.height = m.height; a.append(img);
    a.addEventListener('click', e => { e.preventDefault(); openMap(m); });
    const meta = document.createElement('p'); meta.className = 'map-meta';
    const state = document.createElement('span'); state.textContent = m.state + (m.years.length ? ' / '+m.years.join('–') : '');
    const tag = document.createElement('span'); tag.textContent = m.category === 'Scenarios' ? 'Hypothetical scenario' : m.category;
    if (m.category === 'Scenarios') tag.className = 'scenario-label'; meta.append(state, tag);
    const title = document.createElement('h3'); title.textContent = m.title;
    const series = document.createElement('p'); series.className = 'series-name'; series.textContent = col.title + (m.variant ? ' / '+m.variant : '');
    article.append(a,meta,title,series);
    if (col.credit) { const credit = document.createElement('p'); credit.className = 'map-credit'; credit.textContent = col.credit; article.append(credit); }
    return article;
  }
  function render(reset = true) {
    if (reset) limit = pageSize;
    const words = $('search').value.toLowerCase().trim().split(/\s+/).filter(Boolean);
    filtered = data.images.filter(m => (!category || m.category === category) && (!$('state').value || m.state === $('state').value) && (!$('series').value || m.collection === $('series').value) && (!$('year').value || m.years.includes($('year').value)) && words.every(w => `${m.title} ${m.source_path} ${m.state} ${m.category} ${collections.get(m.collection).title} ${m.variant}`.toLowerCase().includes(w)));
    if ($('sort').value === 'newest') filtered.sort((a,b) => Math.max(0,...b.years.map(Number))-Math.max(0,...a.years.map(Number)) || a.title.localeCompare(b.title));
    if ($('sort').value === 'title') filtered.sort((a,b) => a.title.localeCompare(b.title));
    document.querySelectorAll('.topic').forEach(b => { const active = b.dataset.category === category; b.classList.toggle('active',active); b.setAttribute('aria-pressed',String(active)); });
    $('gallery').replaceChildren(...filtered.slice(0,limit).map(makeCard));
    $('results-count').textContent = `${filtered.length.toLocaleString()} ${filtered.length === 1 ? 'work' : 'works'}${filtered.length !== data.images.length ? ' found' : ''}`;
    $('empty').hidden = filtered.length > 0; $('load-more').hidden = filtered.length <= limit;
    $('page-count').textContent = filtered.length ? `Showing ${Math.min(limit,filtered.length)} of ${filtered.length.toLocaleString()}` : '';
    syncURL();
  }
  function clear() { filters.forEach(id => { $(id).value = ''; }); category = ''; $('sort').value = 'curated'; render(); }
  $('filters').addEventListener('submit',e => e.preventDefault());
  filters.forEach(id => $(id).addEventListener(id === 'search' ? 'input' : 'change',() => render()));
  $('sort').addEventListener('change',() => render());
  document.querySelectorAll('.topic').forEach(b => b.addEventListener('click',() => { category = b.dataset.category; render(); }));
  $('reset').addEventListener('click',clear); $('empty-reset').addEventListener('click',clear);
  $('load-more').addEventListener('click',() => { const oldLimit = limit; limit += pageSize; render(false); $('gallery').children[oldLimit]?.querySelector('a').focus({preventScroll:true}); });
  function openMap(m) {
    current = m; const col = collections.get(m.collection);
    $('viewer-title').textContent = m.title; $('viewer-category').textContent = m.category + ' / '+m.state;
    $('viewer-image').src = imageURL(m); $('viewer-image').alt = m.title; $('full-image').href = imageURL(m);
    $('viewer-collection').textContent = col.title + (m.variant ? ' / '+m.variant : '');
    $('viewer-caveat').textContent = m.category === 'Scenarios' ? 'Hypothetical scenario. Conditional model assumptions; not observed results or a forecast.' : col.claim;
    $('viewer-credit').replaceChildren();
    if (col.credit) { const link = document.createElement('a'); link.href = 'https://redistrictingdatahub.org/terms-and-conditions/'; link.textContent = 'RDH terms'; link.target = '_blank'; link.rel = 'noopener'; $('viewer-credit').append(col.credit+' ',link); }
    $('viewer-notes').textContent = col.notes || 'Source notes were not present in this output collection. Sources embedded in the original render are preserved in this web copy.';
    $('viewer-source').textContent = `Original render: ${m.source_path}. SHA-256: ${m.source_sha256}. Web copy resized from ${m.original_width} × ${m.original_height} to ${m.width} × ${m.height} pixels.`;
    const index = filtered.findIndex(x => x.id === m.id); $('previous').disabled = index <= 0; $('next').disabled = index < 0 || index >= filtered.length-1;
    if (!dialog.open) { dialog.querySelector('details').open = false; dialog.showModal(); $('close-viewer').focus(); }
    history.replaceState(null,'',location.pathname+location.search+'#map='+m.id);
    dialog.scrollTop = 0;
  }
  function close() { dialog.close(); }
  $('close-viewer').addEventListener('click',close);
  dialog.addEventListener('click',e => { if (e.target === dialog) { const r = dialog.getBoundingClientRect(); if (e.clientX < r.left || e.clientX > r.right || e.clientY < r.top || e.clientY > r.bottom) close(); } });
  dialog.addEventListener('close',() => { history.replaceState(null,'',location.pathname+location.search+'#collection'); });
  function step(delta) { const i = filtered.findIndex(x => x.id === current?.id); if (i >= 0 && filtered[i+delta]) openMap(filtered[i+delta]); }
  $('previous').addEventListener('click',() => step(-1)); $('next').addEventListener('click',() => step(1));
  dialog.addEventListener('keydown',e => { if (e.target.closest('summary, a, button') && e.key !== 'ArrowLeft' && e.key !== 'ArrowRight') return; if (e.key === 'ArrowLeft') {e.preventDefault();step(-1);} if (e.key === 'ArrowRight') {e.preventDefault();step(1);} });
  const initialMap = location.hash.startsWith('#map=') ? data.images.find(m => m.id === location.hash.slice(5)) : null;
  render(); if (initialMap) openMap(initialMap);
})();
