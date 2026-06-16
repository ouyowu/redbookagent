import { chromium } from '/opt/node22/lib/node_modules/playwright/index.mjs';
import { fileURLToPath } from 'url';
import path from 'path';
import fs from 'fs';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const htmlPath = path.join(__dirname, 'index.html');
const outDir = path.join(__dirname, 'screenshots');
fs.mkdirSync(outDir, { recursive: true });

const browser = await chromium.launch({
  executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome',
  args: ['--no-sandbox', '--disable-dev-shm-usage'],
});
const page = await browser.newPage();
await page.setViewportSize({ width: 2100, height: 900 });
await page.goto(`file://${htmlPath}`);
await page.waitForTimeout(500);

// Full overview
await page.screenshot({ path: path.join(outDir, 'overview.png'), fullPage: true });
console.log('Saved overview.png');

// Individual pages by frame index
const frames = await page.locator('.phone-frame').all();
const labels = ['home', 'games', 'friends', 'profile', 'membership'];

for (let i = 0; i < frames.length; i++) {
  const label = labels[i] || `page${i}`;
  await frames[i].screenshot({ path: path.join(outDir, `${label}.png`) });
  console.log(`Saved ${label}.png`);
}

await browser.close();
console.log('Done.');
