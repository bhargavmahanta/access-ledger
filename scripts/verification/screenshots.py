#!/usr/bin/env python3
"""Capture genuine interface screens against the running local demo."""
from pathlib import Path
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[2];out=root/'docs/evidence/current'
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True)
    page=browser.new_page(viewport={'width':1440,'height':1050},device_scale_factor=1)
    page.set_default_timeout(60000)
    errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    for route,name in [('/','dashboard'),('/users','users'),('/roles','roles'),('/resources','resources'),('/audit','audit')]:
        page.goto('http://127.0.0.1:5173'+route);page.wait_for_load_state('networkidle')
        assert page.locator('h1').is_visible()
        assert not page.get_by_role('alert').count()
        page.screenshot(path=str(out/(name+'.png')),full_page=True)
    page.goto('http://127.0.0.1:5173/access');page.wait_for_load_state('networkidle')
    page.get_by_label('Employee',exact=True).select_option(label='Priya Sharma')
    page.get_by_label('Resource',exact=True).select_option(label='Reporting Database')
    page.get_by_label('Action',exact=True).select_option(label='READ')
    page.get_by_role('button',name='Evaluate access',exact=True).click()
    page.get_by_test_id('decision').wait_for()
    assert page.get_by_test_id('decision').inner_text()=='ALLOW'
    page.screenshot(path=str(out/'access-allow.png'),full_page=True)
    page.get_by_label('Employee',exact=True).select_option(label='Aisha Bello')
    page.get_by_role('button',name='Evaluate access',exact=True).click()
    page.get_by_test_id('decision').wait_for()
    assert page.get_by_test_id('decision').inner_text()=='DENY'
    page.screenshot(path=str(out/'access-deny.png'),full_page=True)
    page.set_viewport_size({'width':390,'height':844})
    page.goto('http://127.0.0.1:5173/');page.wait_for_load_state('networkidle')
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    page.screenshot(path=str(out/'mobile.png'),full_page=True)
    page.set_viewport_size({'width':1120,'height':1000})
    page.set_content('<style>body{margin:0}</style>'+(root/'docs/er-diagram.svg').read_text());page.screenshot(path=str(root/'docs/er-diagram.png'),full_page=True)
    assert not errors,errors
    browser.close()
print('Captured six pages, ALLOW/DENY results, mobile layout and ER diagram. No browser page errors.')
