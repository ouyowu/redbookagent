import { chromium } from '/opt/node22/lib/node_modules/playwright/index.mjs';
import { fileURLToPath } from 'url';
import path from 'path';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const browser = await chromium.launch({
  executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome',
  args: ['--no-sandbox', '--disable-dev-shm-usage', '--font-render-hinting=none'],
});
const page = await browser.newPage();
await page.setViewportSize({ width: 960, height: 960 });
await page.goto(`file://${path.join(__dirname, 'font-compare.html')}`);
// Wait for Google Fonts to load
await page.waitForTimeout(4000);
await page.screenshot({
  path: path.join(__dirname, 'screenshots/font-compare.png'),
  fullPage: true,
});
console.log('Done');
await browser.close();
