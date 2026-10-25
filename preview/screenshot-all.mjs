import { chromium } from '/opt/node22/lib/node_modules/playwright/index.mjs';
import { fileURLToPath } from 'url';
import path from 'path';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const browser = await chromium.launch({
  executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome',
  args: ['--no-sandbox', '--disable-dev-shm-usage', '--font-render-hinting=none'],
});

const pages = [
  { file: 'login-new.html',    out: 'login-new.png'    },
  { file: 'home-new.html',     out: 'home-new.png'     },
  { file: 'messages-new.html', out: 'messages-new.png' },
  { file: 'profile-new.html',  out: 'profile-new.png'  },
];

for (const p of pages) {
  const page = await browser.newPage();
  await page.setViewportSize({ width: 500, height: 900 });
  await page.goto(`file://${path.join(__dirname, p.file)}`);
  await page.waitForTimeout(3500);
  await page.locator('.phone').screenshot({ path: path.join(__dirname, 'screenshots', p.out) });
  console.log(`✓ ${p.out}`);
  await page.close();
}

await browser.close();
console.log('All done.');
