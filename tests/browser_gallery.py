"""End-to-end checks for browsing and sharing the static map collection.

Run with a static server on port 8765 and uv run --no-project --with playwright.
Set PORTFOLIO_BROWSER to an existing Chromium executable if needed.
"""
import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

ROOT=Path(__file__).resolve().parents[1]
ARTIFACTS=ROOT/'.browser-artifacts'
ARTIFACTS.mkdir(exist_ok=True)
data=json.loads((ROOT/'data/gallery.json').read_text())
base=os.environ.get('PORTFOLIO_URL','http://127.0.0.1:8765')
errors=[]
with sync_playwright() as p:
    args={'headless':True}
    if os.environ.get('PORTFOLIO_BROWSER'):args['executable_path']=os.environ['PORTFOLIO_BROWSER']
    browser=p.chromium.launch(**args)
    page=browser.new_page(viewport={'width':1440,'height':1050},device_scale_factor=1)
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.on('response',lambda r: errors.append(f'HTTP {r.status}: {r.url}') if r.status>=400 else None)
    page.goto(base,wait_until='networkidle')
    expect(page.locator('.map-card')).to_have_count(30)
    assert str(len(data['images'])) in page.locator('#results-count').inner_text().replace(',','')
    page.screenshot(path=str(ARTIFACTS/'desktop.png'),full_page=False)
    page.locator('#load-more').click()
    expect(page.locator('.map-card')).to_have_count(60)
    page.locator('#state').select_option('Kansas')
    expect(page.locator('.map-card')).to_have_count(1)
    expect(page.locator('.map-card')).to_contain_text('Kansas')
    page.locator('#year').select_option('2016')
    expect(page.locator('.map-card')).to_have_count(1)
    page.locator('#search').fill('nonexistent-election-fixture')
    expect(page.locator('#empty')).to_be_visible()
    expect(page.locator('.map-card')).to_have_count(0)
    page.locator('#empty-reset').click()
    expect(page.locator('.map-card')).to_have_count(30)
    page.locator('[data-category="Scenarios"]').click()
    cards=page.locator('.map-card')
    assert cards.count()>0
    for card in cards.all():assert 'Hypothetical scenario' in card.inner_text()
    page.locator('.map-link').first.click()
    expect(page.locator('#viewer')).to_be_visible()
    expect(page.locator('#viewer-caveat')).to_contain_text('Hypothetical')
    page.wait_for_function('document.querySelector("#viewer-image").complete && document.querySelector("#viewer-image").naturalWidth > 0')
    assert page.locator('#close-viewer').evaluate('(e)=>e===document.activeElement')
    title=page.locator('#viewer-title').inner_text()
    page.keyboard.press('ArrowRight')
    assert page.locator('#viewer-title').inner_text()!=title
    shared=page.url
    page.reload(wait_until='networkidle')
    expect(page.locator('#viewer')).to_be_visible()
    expect(page.locator('#viewer-caveat')).to_contain_text('Hypothetical')
    page.locator('summary').click()
    expect(page.locator('#viewer-notes')).to_be_visible()
    page.keyboard.press('Escape')
    expect(page.locator('#viewer')).not_to_be_visible()
    page.locator('#reset').click()
    page.locator('#series').select_option('alabama-2024-to-2026-legislative-district-swing')
    assert 'series=' in page.url
    page.reload(wait_until='networkidle')
    expect(page.locator('#series')).to_have_value('alabama-2024-to-2026-legislative-district-swing')
    expect(page.locator('.map-card')).to_have_count(30)
    for viewport in [{'width':390,'height':844},{'width':320,'height':700},{'width':768,'height':1024}]:
        page.set_viewport_size(viewport)
        page.goto(base,wait_until='networkidle')
        assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth'), f'Horizontal overflow at {viewport}'
        page.locator('#search').fill('Tennessee')
        expect(page.locator('.map-card')).to_have_count(1)
        page.locator('.map-link').click()
        expect(page.locator('#viewer')).to_be_visible()
        assert page.locator('#viewer').evaluate('(e)=>e.scrollWidth<=e.clientWidth'), 'Dialog horizontal overflow'
        page.locator('#close-viewer').click()
        page.locator('#reset').click()
        page.evaluate('window.scrollTo(0,0)')
        page.screenshot(path=str(ARTIFACTS/f"viewport-{viewport['width']}.png"),full_page=False)
    assert not errors, errors
    browser.close()
print('Browser checks passed: pagination, combined filters, empty/reset, scenario labels, keyboard viewer, deep links, collection persistence, 320/390/768/1440px layouts, no JS or HTTP errors.')
