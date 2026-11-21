"""Browse selected work and the complete static archive, including shared links."""
import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / '.browser-artifacts'
ARTIFACTS.mkdir(exist_ok=True)
data = json.loads((ROOT / 'data/gallery.json').read_text())
base = os.environ.get('PORTFOLIO_URL', 'http://127.0.0.1:8765').rstrip('/') + '/'
errors = []


def open_filters(page):
    if not page.locator('#more-filters').evaluate('(e) => e.open'):
        page.locator('#more-filters > summary').click()


with sync_playwright() as p:
    args = {'headless': True}
    if os.environ.get('PORTFOLIO_BROWSER'):
        args['executable_path'] = os.environ['PORTFOLIO_BROWSER']
    browser = p.chromium.launch(**args)
    page = browser.new_page(viewport={'width': 1440, 'height': 1050}, device_scale_factor=1)
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.on('response', lambda r: errors.append(f'HTTP {r.status}: {r.url}') if r.status >= 400 else None)
    page.goto(base, wait_until='networkidle')
    expect(page.locator('.map-card')).to_have_count(8)
    expect(page.locator('#browse-controls')).not_to_be_visible()
    expect(page.locator('.map-card').first).to_contain_text('Alabama Senate special election, 2017')
    assert page.locator('.map-link').first.bounding_box()['y'] < 200, 'Maps should begin immediately after the compact header'
    assert len(page.locator('.map-card h3').all_text_contents()) == len(set(page.locator('.map-card h3').all_text_contents()))
    assert not page.locator('.intro, .about, .topics, .series-name').count()
    page.screenshot(path=str(ARTIFACTS / 'desktop.png'), full_page=False)
    page.screenshot(path=str(ARTIFACTS / 'selected-full.png'), full_page=True)
    page.locator('#archive-view').click()
    expect(page.locator('.map-card')).to_have_count(30)
    assert str(len(data['images'])) in page.locator('#results-count').inner_text().replace(',', '')
    expect(page.locator('#year')).not_to_be_visible()
    page.locator('#load-more').click()
    expect(page.locator('.map-card')).to_have_count(60)
    page.locator('#state').select_option('Kansas')
    expect(page.locator('.map-card')).to_have_count(1)
    expect(page.locator('.map-card')).to_contain_text('Kansas')
    open_filters(page)
    page.locator('#year').select_option('2016')
    expect(page.locator('#more-filter-label')).to_have_text('More filters (1)')
    expect(page.locator('.map-card')).to_have_count(1)
    page.locator('#search').fill('nonexistent-election-fixture')
    expect(page.locator('#empty')).to_be_visible()
    expect(page.locator('.map-card')).to_have_count(0)
    page.locator('#empty-reset').click()
    expect(page.locator('.map-card')).to_have_count(30)
    open_filters(page)
    page.locator('#category').select_option('Scenarios')
    assert page.locator('.map-card').count() > 0
    for card in page.locator('.map-card').all():
        assert 'Hypothetical scenario' in card.inner_text()
    page.locator('#more-filters > summary').click()
    page.locator('.map-link').first.click()
    expect(page.locator('#viewer')).to_be_visible()
    expect(page.locator('#viewer-caveat')).to_contain_text('Hypothetical')
    expect(page.locator('#viewer-source')).not_to_be_visible()
    page.wait_for_function('document.querySelector("#viewer-image").complete && document.querySelector("#viewer-image").naturalWidth > 0')
    assert page.locator('#close-viewer').evaluate('(e) => e === document.activeElement')
    title = page.locator('#viewer-title').inner_text()
    page.keyboard.press('ArrowRight')
    assert page.locator('#viewer-title').inner_text() != title
    page.reload(wait_until='networkidle')
    expect(page.locator('#viewer')).to_be_visible()
    expect(page.locator('#viewer-caveat')).to_contain_text('Hypothetical')
    page.locator('#map-details > summary').click()
    expect(page.locator('#viewer-notes')).to_be_visible()
    expect(page.locator('#viewer-source')).to_contain_text('SHA-256')
    page.keyboard.press('Escape')
    expect(page.locator('#viewer')).not_to_be_visible()
    page.locator('#reset').click()
    open_filters(page)
    page.locator('#series').select_option('alabama-2024-to-2026-legislative-district-swing')
    assert 'series=' in page.url
    page.reload(wait_until='networkidle')
    expect(page.locator('#series')).to_have_value('alabama-2024-to-2026-legislative-district-swing')
    expect(page.locator('.map-card')).to_have_count(30)
    page.locator('#selected-view').click()
    expect(page.locator('.map-card')).to_have_count(8)
    expect(page.locator('#browse-controls')).not_to_be_visible()
    page.goto(base + '?q=Tennessee', wait_until='networkidle')
    expect(page.locator('.map-card')).to_have_count(1)
    # Old direct links without a view parameter must still open unfeatured maps.
    updated = next(m for m in data['images'] if m['source_path'].endswith('alabama-2026-jackson-meeting-revised/maps/hd10.png'))
    page.goto(base + '#map=' + updated['id'], wait_until='networkidle')
    expect(page.locator('#viewer')).to_be_visible()
    expect(page.locator('#viewer-caveat')).to_contain_text('estimated 2024 whole-precinct benchmarks')
    page.keyboard.press('Escape')
    for viewport in [{'width': 390, 'height': 844}, {'width': 320, 'height': 700}, {'width': 768, 'height': 1024}]:
        page.set_viewport_size(viewport)
        page.goto(base, wait_until='networkidle')
        expect(page.locator('.map-card')).to_have_count(8)
        assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth'), f'Horizontal overflow at {viewport}'
        assert page.locator('.map-link').first.bounding_box()['y'] < 200
        page.screenshot(path=str(ARTIFACTS / f"viewport-{viewport['width']}.png"), full_page=False)
        page.locator('#archive-view').click()
        open_filters(page)
        box = page.locator('.extra-filters').bounding_box()
        assert box['x'] >= 0 and box['x'] + box['width'] <= viewport['width'], 'Filter panel overflow'
        page.locator('#more-filters > summary').click()
        page.locator('#search').fill('Tennessee')
        expect(page.locator('.map-card')).to_have_count(1)
        page.locator('.map-link').click()
        expect(page.locator('#viewer')).to_be_visible()
        assert page.locator('#viewer').evaluate('(e) => e.scrollWidth <= e.clientWidth'), 'Dialog horizontal overflow'
        page.locator('#close-viewer').click()
    assert not errors, errors
    browser.close()
print('Browser checks passed: eight selected highlights, early map visibility, complete archive, progressive filters, pagination, combined filtering, reset, scenario/estimate caveats, keyboard viewer, old/direct URLs, sources disclosure, 320/390/768/1440px layouts, no JS or HTTP errors.')
