"""Current product navigation helpers. No legacy UI compatibility path in application."""
from playwright.sync_api import expect

def journal(p):
 p.get_by_role('button',name='Щоденник',exact=True).click()
 expect(p.get_by_role('heading',name='Ваш щоденник',exact=True)).to_be_visible()

def feature(p,name):
 if '/phone/' in p.url:
  p.get_by_role('button',name=name,exact=True).click();return
 button=p.get_by_role('button',name=name,exact=True)
 if button.count() and button.first.is_visible():button.first.click();return
 p.get_by_role('button',name='Більше',exact=True).click()
 p.get_by_role('dialog',name='Більше',exact=True).get_by_role('button',name=name,exact=True).click()

def card_actions(p):
 expect(p.locator('.entry-menu').first).to_be_visible()
 for details in p.locator('.entry-menu').all():
  if not details.evaluate('d=>d.open'):details.locator('summary').click()

def tools(p):
 details=p.locator('.journal-tools');
 if details.count() and not details.evaluate('d=>d.open'):details.locator('summary').click()
