// Run with Node, a locally installed playwright-core, and Chrome (or CHROMIUM_PATH).
// Launch uses a local browser pipe; no server, browser download, or package install.
const assert = require('node:assert/strict');
const path = require('node:path');
const { pathToFileURL } = require('node:url');
const { chromium } = require('playwright-core');

const entry = pathToFileURL(path.resolve(__dirname, '../variant-b/index.html')).href;

async function check(page, withhold) {
  await page.goto(entry);
  const key = k => page.keyboard.press(k);
  const state = () => page.locator('#state').innerText();
  const focus = () => page.evaluate(() => document.activeElement.id || document.activeElement.tagName);
  const ack = page.getByRole('button', { name: 'Deliver acknowledgment' });
  // Freeze page timers only; all input uses Chromium's native keyboard handling.
  await page.clock.install({ time: new Date('2020-01-01T00:00:00Z') });
  await page.clock.pauseAt(new Date('2020-01-01T00:01:00Z'));
  await key('Tab');
  await key('Tab');
  if (withhold) {
    await key('Tab'); await key('Tab'); await key('Enter');
    await key('Tab'); await key('Space');
    assert.equal(await page.locator('#silent').isChecked(), true);
    await key('Shift+Tab'); await key('Enter');
    await key('Shift+Tab'); await key('Shift+Tab');
  }
  assert.equal(await page.locator('details').evaluate(d => d.open), false);
  assert.equal(await focus(), 'run');
  await key('Enter');
  await page.clock.runFor(700);
  assert.equal(await state(), 'Waiting');
  assert.equal(await focus(), 'stop');
  await key('Escape');
  const blocked = ['Done', 'Blocked', 'Blocked', 'Blocked'];
  const rows = () => page.locator('#rows em').allTextContents();
  assert.equal(await state(), 'Stop requested');
  assert.match(await page.locator('#msg').innerText(), /unconfirmed/i);
  assert.deepEqual(await rows(), blocked);
  assert.equal(await page.locator('#run').isDisabled(), true);
  if (withhold) {
    assert.equal(await focus(), 'ack', 'Esc must focus the acknowledgment action');
    assert.equal(await ack.isVisible(), true, 'action must be visible and exposed by role/name');
    await page.clock.runFor(4000); // beyond the original 3-second wait and auto-ack delay
    assert.equal(await state(), 'Stop requested');
    assert.deepEqual(await rows(), blocked);
    assert.equal(await focus(), 'ack');
    await key('Enter');
  } else {
    assert.equal(await ack.count(), 0);
    assert.equal(await page.locator('details').evaluate(d => d.open), false);
    await page.clock.runFor(850); // default simulated acknowledgment
  }
  assert.equal(await state(), 'Stopped');
  assert.equal(await focus(), 'run');
  assert.equal(await page.locator('#run').isEnabled(), true);
  assert.equal(await ack.count(), 0);
  console.log(`PASS: ${withhold ? 'withheld' : 'automatic'} acknowledgment; focus restored to Play sequence`);
}

(async () => {
  const browser = await chromium.launch({
    ...(process.env.CHROMIUM_PATH ? { executablePath: process.env.CHROMIUM_PATH } : { channel: 'chrome' }),
    args: ['--disable-background-networking', '--host-resolver-rules=MAP * ~NOTFOUND'],
  });
  try {
    console.log(`Chromium ${browser.version()} | offline file fixture`);
    const context = await browser.newContext({ offline: true, viewport: { width: 1280, height: 800 } });
    for (const withhold of [true, false]) {
      const page = await context.newPage();
      await check(page, withhold);
      await page.close();
    }
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
