'use strict';
(() => {
  const data = window.ELECTION_ARCHIVE;
  const $ = id => document.getElementById(id);
  if (!data) {
    $('gallery').textContent = 'The maps could not load. Please refresh the page.';
    return;
  }

  // A small editorial selection; the complete catalog remains in All maps.
  const selection = [
    ['f7962bde494e35ce', 'Alabama Senate special election, 2017'],
    ['788f48d5539d90a5', 'Tennessee presidential shift, 2016–2024'],
    ['10a0813ae31009b7', 'Kansas swing relative to the nation, 2016–2024'],
    ['b89efb9d39d46625', 'Alabama county realignment, 1992–2024'],
    ['ee0db2435452f4e8', 'Alabama Amendment 2, 2000'],
    ['a2f5aea4dc0a0a87', 'Huntsville City Council District 2, 2026'],
    ['b2b44ccef3ad3f21', 'Florida special elections, 2026'],
    ['209dddc318b9935a', 'Southern midterm scenario, 2026'],
  ];
  const captions = new Map(selection);
  const byId = new Map(data.images.map(m => [m.id, m]));
  const selected = selection.map(([id]) => byId.get(id)).filter(Boolean);
  const collections = new Map(data.collections.map(c => [c.id, c]));
  const imageURL = (m, key = 'image') => `${m[key]}?v=${m.source_sha256.slice(0, 12)}`;
  const filterIds = ['search', 'state', 'series', 'year', 'category'];
  const pageSize = 30;
  const dialog = $('viewer');
  const params = new URLSearchParams(location.search);
  const estimatedDistricts = new Set(['hd2', 'hd4', 'hd5', 'hd8', 'hd10', 'hd19', 'hd20', 'hd21', 'hd25', 'sd2', 'sd3', 'sd6', 'sd7', 'sd8']);
  let view = params.get('view') === 'all' || ['q', 'state', 'series', 'year', 'category', 'sort'].some(k => params.has(k)) ? 'all' : 'selected';
  let limit = pageSize;
  let filtered = [];
  let current = null;

  function addOption(parent, value, label) {
    const option = document.createElement('option');
    option.value = value;
    option.textContent = label;
    parent.append(option);
  }
  [...new Set(data.images.map(m => m.state))].sort().forEach(s => addOption($('state'), s, s));
  [...data.collections].sort((a, b) => a.title.localeCompare(b.title)).forEach(c => addOption($('series'), c.id, c.title));
  [...new Set(data.images.flatMap(m => m.years))].sort().reverse().forEach(y => addOption($('year'), y, y));
  filterIds.forEach(id => {
    const key = id === 'search' ? 'q' : id;
    if (params.has(key)) $(id).value = params.get(key);
  });
  if (['curated', 'newest', 'title'].includes(params.get('sort'))) $('sort').value = params.get('sort');

  function isEstimated(m) {
    const name = m.source_path.split('/').pop().replace(/\.png$/, '');
    return m.collection === 'alabama-2026-jackson-meeting-revised' && estimatedDistricts.has(name);
  }

  function mapTitle(m) {
    if (captions.has(m.id)) return captions.get(m.id);
    const col = collections.get(m.collection);
    const leaf = m.source_path.split('/').pop().replace(/\.[^.]+$/, '');
    const district = leaf.match(/^alabama-(house|senate)-district-(\d+)-/);
    if (district) {
      const office = district[1] === 'house' ? 'House' : 'Senate';
      const type = m.collection.includes('presidential-legislative') ? '2024 presidential result'
        : m.collection.includes('primary-turnout') ? '2026 primary turnout' : '2024–2026 primary margin change';
      return `Alabama ${office} ${Number(district[2])}, ${type}`;
    }
    if (m.collection === 'alabama-2026-jackson-meeting-revised') {
      const short = leaf.match(/^(hd|sd|cd)(\d+)$/);
      if (short) return `Alabama ${({hd: 'House', sd: 'Senate', cd: 'Congressional District'})[short[1]]} ${Number(short[2])}, 2026`;
    }
    let title = m.title.split(' · ' + col.title)[0].replace(/\s+/g, ' ').trim();
    title = title.replace(/^\d{2} /, '').replace(/^Dem /, 'Democratic ').replace(/^Rep /, 'Republican ');
    if (m.collection === 'alabama-2026-jackson-meeting-revised' && !m.source_path.includes('--')) {
      title = `Alabama ${title[0].toLowerCase() + title.slice(1)}, 2026`;
    }
    if (m.variant.startsWith('Design alternatives / ')) title += ` (${m.variant.slice(22)})`;
    return title;
  }

  function syncURL() {
    const p = new URLSearchParams();
    if (view === 'all') {
      p.set('view', 'all');
      filterIds.forEach(id => { if ($(id).value) p.set(id === 'search' ? 'q' : id, $(id).value); });
      if ($('sort').value !== 'curated') p.set('sort', $('sort').value);
    }
    history.replaceState(null, '', location.pathname + (p.size ? '?' + p : '') + location.hash);
  }

  function openLink(link, m) {
    link.href = imageURL(m);
    link.addEventListener('click', e => { e.preventDefault(); openMap(m); });
  }

  function makeCard(m) {
    const col = collections.get(m.collection);
    const title = mapTitle(m);
    const article = document.createElement('article');
    article.className = 'map-card';
    article.dataset.mapId = m.id;
    const a = document.createElement('a');
    a.className = 'map-link';
    a.setAttribute('aria-label', 'View ' + title);
    openLink(a, m);
    const img = document.createElement('img');
    img.src = imageURL(m, 'thumbnail');
    img.alt = title;
    img.loading = 'lazy';
    img.decoding = 'async';
    img.width = m.width;
    img.height = m.height;
    a.append(img);
    const heading = document.createElement('h3');
    const textLink = document.createElement('a');
    textLink.textContent = title;
    openLink(textLink, m);
    heading.append(textLink);
    article.append(a, heading);
    if (m.category === 'Scenarios' || isEstimated(m)) {
      const note = document.createElement('p');
      note.className = 'map-note';
      note.textContent = m.category === 'Scenarios' ? 'Hypothetical scenario' : 'Estimated split-precinct comparisons';
      article.append(note);
    }
    if (col.credit) {
      const credit = document.createElement('p');
      credit.className = 'map-credit';
      const link = document.createElement('a');
      link.href = 'https://redistrictingdatahub.org/terms-and-conditions/';
      link.textContent = 'Data: Redistricting Data Hub';
      link.title = col.credit;
      credit.append(link);
      article.append(credit);
    }
    return article;
  }

  function render(reset = true) {
    if (reset) limit = pageSize;
    const archive = view === 'all';
    $('browse-controls').hidden = !archive;
    $('selected-view').setAttribute('aria-pressed', String(!archive));
    $('archive-view').setAttribute('aria-pressed', String(archive));
    const words = $('search').value.toLowerCase().trim().split(/\s+/).filter(Boolean);
    if (archive) {
      filtered = data.images.filter(m =>
        (!$('category').value || m.category === $('category').value) &&
        (!$('state').value || m.state === $('state').value) &&
        (!$('series').value || m.collection === $('series').value) &&
        (!$('year').value || m.years.includes($('year').value)) &&
        words.every(w => `${mapTitle(m)} ${m.title} ${m.source_path} ${m.state} ${m.category} ${collections.get(m.collection).title} ${m.variant}`.toLowerCase().includes(w)));
      if ($('sort').value === 'newest') filtered.sort((a, b) => Math.max(0, ...b.years.map(Number)) - Math.max(0, ...a.years.map(Number)) || mapTitle(a).localeCompare(mapTitle(b)));
      else if ($('sort').value === 'title') filtered.sort((a, b) => mapTitle(a).localeCompare(mapTitle(b)));
      else filtered.sort((a, b) => {
        const ai = selection.findIndex(([id]) => id === a.id);
        const bi = selection.findIndex(([id]) => id === b.id);
        return (ai < 0 ? selection.length : ai) - (bi < 0 ? selection.length : bi);
      });
    } else filtered = selected;
    $('gallery').replaceChildren(...filtered.slice(0, archive ? limit : selected.length).map(makeCard));
    $('results-count').textContent = `${filtered.length.toLocaleString()} ${filtered.length === 1 ? 'result' : 'results'}`;
    const extraCount = ['series', 'year', 'category'].filter(id => $(id).value).length + Number($('sort').value !== 'curated');
    $('more-filter-label').textContent = extraCount ? `More filters (${extraCount})` : 'More filters';
    $('reset').hidden = !filterIds.some(id => $(id).value) && $('sort').value === 'curated';
    $('empty').hidden = filtered.length > 0;
    $('load-area').hidden = !archive || filtered.length <= limit;
    syncURL();
  }

  function clear() {
    filterIds.forEach(id => { $(id).value = ''; });
    $('sort').value = 'curated';
    render();
  }
  function changeView(next) {
    view = next;
    $('more-filters').open = false;
    render();
  }
  $('selected-view').addEventListener('click', () => changeView('selected'));
  $('archive-view').addEventListener('click', () => changeView('all'));
  $('filters').addEventListener('submit', e => e.preventDefault());
  filterIds.forEach(id => $(id).addEventListener(id === 'search' ? 'input' : 'change', () => render()));
  $('sort').addEventListener('change', () => render());
  $('reset').addEventListener('click', clear);
  $('empty-reset').addEventListener('click', clear);
  $('load-more').addEventListener('click', () => {
    const oldLimit = limit;
    limit += pageSize;
    render(false);
    $('gallery').children[oldLimit]?.querySelector('a').focus({preventScroll: true});
  });

  function openMap(m) {
    current = m;
    const col = collections.get(m.collection);
    $('more-filters').open = false;
    $('viewer-title').textContent = mapTitle(m);
    $('viewer-image').src = imageURL(m);
    $('viewer-image').alt = mapTitle(m);
    $('full-image').href = imageURL(m);
    $('viewer-collection').textContent = col.title + (m.variant ? ' / ' + m.variant : '');
    $('viewer-claim').textContent = col.claim;
    $('viewer-claim').hidden = !col.claim;
    $('viewer-caveat').textContent = m.category === 'Scenarios' ? 'Hypothetical scenario.'
      : isEstimated(m) ? 'Split precincts use estimated 2024 whole-precinct benchmarks.' : '';
    $('viewer-caveat').hidden = !$('viewer-caveat').textContent;
    $('viewer-credit').replaceChildren();
    $('viewer-credit').hidden = !col.credit;
    if (col.credit) {
      const link = document.createElement('a');
      link.href = 'https://redistrictingdatahub.org/terms-and-conditions/';
      link.textContent = 'RDH terms';
      $('viewer-credit').append(col.credit + ' ', link);
    }
    $('viewer-notes').textContent = col.notes || 'No separate source notes are available. See the credits in the map.';
    $('viewer-source').textContent = `Original: ${m.source_path}\nSHA-256: ${m.source_sha256}\nImage: ${m.original_width} × ${m.original_height}; web copy: ${m.width} × ${m.height}.`;
    const index = filtered.findIndex(x => x.id === m.id);
    $('previous').disabled = index <= 0;
    $('next').disabled = index < 0 || index >= filtered.length - 1;
    if (!dialog.open) {
      $('map-details').open = false;
      dialog.showModal();
      $('close-viewer').focus();
    }
    history.replaceState(null, '', location.pathname + location.search + '#map=' + m.id);
    dialog.scrollTop = 0;
  }
  $('close-viewer').addEventListener('click', () => dialog.close());
  dialog.addEventListener('click', e => {
    if (e.target !== dialog) return;
    const r = dialog.getBoundingClientRect();
    if (e.clientX < r.left || e.clientX > r.right || e.clientY < r.top || e.clientY > r.bottom) dialog.close();
  });
  dialog.addEventListener('close', () => history.replaceState(null, '', location.pathname + location.search + '#collection'));
  function step(delta) {
    const i = filtered.findIndex(x => x.id === current?.id);
    if (i >= 0 && filtered[i + delta]) openMap(filtered[i + delta]);
  }
  $('previous').addEventListener('click', () => step(-1));
  $('next').addEventListener('click', () => step(1));
  dialog.addEventListener('keydown', e => {
    if (e.key === 'ArrowLeft') { e.preventDefault(); step(-1); }
    if (e.key === 'ArrowRight') { e.preventDefault(); step(1); }
  });
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape' && !dialog.open) $('more-filters').open = false;
  });

  const initialMap = location.hash.startsWith('#map=') ? byId.get(location.hash.slice(5)) : null;
  if (initialMap && !captions.has(initialMap.id)) view = 'all';
  render();
  if (initialMap) openMap(initialMap);
})();
