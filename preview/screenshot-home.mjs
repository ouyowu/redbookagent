import { chromium } from '/opt/node22/lib/node_modules/playwright/index.mjs';
import { fileURLToPath } from 'url';
import path from 'path';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const browser = await chromium.launch({
  executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome',
  args: ['--no-sandbox', '--disable-dev-shm-usage'],
});
const page = await browser.newPage();
await page.setViewportSize({ width: 500, height: 900 });
await page.goto(`file://${path.join(__dirname, 'home-new.html')}`);
await page.waitForTimeout(400);
await page.locator('.phone').screenshot({ path: path.join(__dirname, 'screenshots/home-new.png') });
console.log('Done');
await browser.close();
