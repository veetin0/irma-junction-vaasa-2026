"""Capture the demo-step screenshots used in pitch-slides.html.
Start the app first: cd app && PORT=8772 DEMO_TODAY=2026-10-03 AGENT_MODE=replay IRMA_BACKGROUND=0 IRMA_RUNTIME_DIR=/tmp/irma-slides ./run.sh
Only the demo-*.png files referenced by the deck are kept; the others are written but unused.
"""
from playwright.sync_api import sync_playwright

OUT = '/Users/veetinurmikoski/Desktop/Junction-Vaasa-v2/docs/pitch-assets/'
BASE = 'http://localhost:8772/'


def shot(pg, name):
    pg.wait_for_timeout(500)
    pg.screenshot(path=OUT + name)
    print('saved', name)


def scroll_to(pg, locator, offset=90):
    locator.first.evaluate("e=>e.scrollIntoView({block:'start'})")
    pg.evaluate("(o)=>window.scrollBy(0,-o)", offset)
    pg.wait_for_timeout(300)


import json, urllib.request
def post(path, body=None):
    req = urllib.request.Request(BASE.rstrip('/') + path, json.dumps(body or {}).encode(), {'Content-Type': 'application/json'}, method='POST')
    urllib.request.urlopen(req).read()
post('/api/world', {'world': 1})
post('/api/reset')

with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={'width': 1440, 'height': 810})
    pg.goto(BASE)
    pg.wait_for_selector('text=Recommended move')
    pg.wait_for_timeout(1200)

    # 1. Overview, then the move card with the trigger disclosure open
    shot(pg, 'demo-1a-overview.png')
    pg.locator('summary', has_text='Trigger · cost if wrong').first.click()
    scroll_to(pg, pg.locator('text=Recommended move'), 90)
    shot(pg, 'demo-1b-move-trigger.png')
    pg.evaluate("()=>{const e=[...document.querySelectorAll('*')].find(x=>x.children.length==0&&/^Next action$/i.test(x.textContent.trim()));if(e){e.scrollIntoView();window.scrollBy(0,-130)}}")
    shot(pg, 'demo-1c-next-action.png')

    # 2. Horizon 3 y
    pg.evaluate("window.scrollTo(0,0)")
    pg.locator('button.chip', has_text='3 y').first.click()
    pg.wait_for_timeout(600)
    shot(pg, 'demo-2-horizon-3y.png')
    pg.locator('button.chip', has_text='1 y').first.click()

    # 3. A signal: SIG-003
    pg.goto(BASE + '#/signals')
    pg.wait_for_selector('h2:has-text("Strong signals")')
    pg.locator('a', has_text='Google FI investment EUR 13 bn').first.click()
    pg.wait_for_selector('h1:has-text("Google")')
    pg.wait_for_timeout(800)
    shot(pg, 'demo-3a-signal-top.png')
    pg.locator('summary', has_text='How the weight is calculated').first.evaluate("e=>{e.parentElement.open=true}")
    scroll_to(pg, pg.locator('summary', has_text='How the weight is calculated'), 80)
    shot(pg, 'demo-3b-weight.png')
    pg.evaluate("window.scrollBy(0, 640)")
    shot(pg, 'demo-3c-weight-band-horizon.png')

    # 4. The other side
    pg.goto(BASE + '#/signals')
    pg.wait_for_selector('h2:has-text("Negative signals")')
    scroll_to(pg, pg.locator('h2', has_text='Negative signals'), 90)
    shot(pg, 'demo-4a-negative-signals.png')
    pg.evaluate("window.scrollTo(0,0)")
    pg.locator('button.dd-btn', has_text='Region').first.click()
    pg.locator('button.dd-opt', has_text='Nordics').first.click()
    pg.wait_for_timeout(700)
    scroll_to(pg, pg.locator('h2', has_text='Negative signals'), 90)
    shot(pg, 'demo-4b-region-nordics.png')
    pg.evaluate("window.scrollTo(0,0)")
    pg.locator('button.dd-btn', has_text='Region').first.click()
    pg.locator('button.dd-opt', has_text='All regions').first.click()

    # 5. New data
    pg.goto(BASE + '#/import')
    pg.wait_for_timeout(1000)
    shot(pg, 'demo-5a-import-page.png')
    pg.locator('button', has_text='Import demonstration item').first.click()
    pg.wait_for_selector('text=Processing steps', timeout=30000)
    pg.wait_for_timeout(1200)
    pg.evaluate("window.scrollTo(0,0)")
    shot(pg, 'demo-5b-import-result.png')
    pg.evaluate("window.scrollBy(0, 700)")
    shot(pg, 'demo-5c-import-result-lower.png')
    pg.locator('summary', has_text='Processing steps').first.evaluate("e=>{e.parentElement.open=true}")
    scroll_to(pg, pg.locator('summary', has_text='Processing steps'), 80)
    shot(pg, 'demo-5d-processing-steps.png')

    # 6. The planner decides
    pg.goto(BASE + '#/signal/SIG-001')
    pg.wait_for_selector('summary:has-text("Your assessment")')
    pg.wait_for_timeout(600)
    pg.locator('summary', has_text='Your assessment').first.evaluate("e=>{e.parentElement.open=true}")
    pg.locator('input[placeholder^="Reason"]').fill('GW is not relays for our mix')
    scroll_to(pg, pg.locator('summary', has_text='Your assessment'), 120)
    shot(pg, 'demo-6a-dispute-typed.png')
    pg.get_by_role('button', name='Dispute').first.click()
    pg.wait_for_timeout(1200)
    pg.evaluate("window.scrollTo(0,0)")
    shot(pg, 'demo-6b-disputed-top.png')
    pg.evaluate("()=>{const e=[...document.querySelectorAll('summary,h2,h3')].find(x=>/Earlier versions/i.test(x.textContent));if(e){e.scrollIntoView();window.scrollBy(0,-90)}}")
    shot(pg, 'demo-6c-earlier-versions.png')

    # Optional: World situation 2
    pg.goto(BASE)
    pg.wait_for_selector('text=Recommended move')
    pg.locator('button', has_text='World situation 2').first.click()
    pg.wait_for_timeout(1500)
    pg.evaluate("window.scrollTo(0,0)")
    shot(pg, 'demo-7-world-2.png')
    b.close()
