from pathlib import Path
from playwright.sync_api import sync_playwright

root = Path(__file__).parent
with sync_playwright() as p:
    browser = p.chromium.launch(channel='chrome', headless=True)
    page = browser.new_page(viewport={'width': 1440, 'height': 1260}, device_scale_factor=1)
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.goto((root / 'index.html').as_uri())
    page.locator('text=RUN 001').wait_for()
    assert page.locator('svg circle').count() >= 241
    assert page.locator('svg path').count() == 4
    assert page.locator('svg text').filter(has_text='σ = 1.67').count() == 1
    before = page.locator('svg circle').first.get_attribute('cx')
    page.get_by_role('button', name='New run').click()
    assert page.locator('#run-label').inner_text() == 'RUN 002'
    assert page.locator('svg circle').first.get_attribute('cx') != before
    assert not errors, errors
    page.reload()
    page.locator('text=RUN 001').wait_for()
    page.screenshot(path=str(root / 'field-note.png'), full_page=True)
    print('PASS: 241+ marks, 3 density curves, sigma label, rerun changes click, no JS errors; still exported')
    browser.close()
