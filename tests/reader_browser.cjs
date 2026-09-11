const {chromium} = require('playwright');
const assert = require('node:assert/strict');
const path = require('node:path');
const {pathToFileURL} = require('node:url');
(async()=>{
 const browser=await chromium.launch({channel:'chrome',headless:true});
 const page=await browser.newPage({viewport:{width:1500,height:1050},deviceScaleFactor:2});
 const remote=[],errors=[];
 page.on('request',r=>{if(/^https?:/.test(r.url())) remote.push(r.url())});
 page.on('pageerror',e=>errors.push(e.message));
 await page.goto(pathToFileURL(path.resolve(process.argv[2]||'output/bridging-reader-simple/index.html')).href);
 await page.waitForFunction(()=>document.body.dataset.pdfReady==='true',null,{timeout:30000});
 assert.equal(await page.locator('.pdf-page').count(),10);
 assert.equal(await page.locator('.chapter').count(),12);
 assert.equal(await page.locator('.knowledge-card').count(),10);
 assert.equal(await page.locator('.figure img').count(),8);
 assert.ok(await page.locator('#pdf-page-1 .textLayer span').count()>100);
 const initial=await page.locator('#pdf-page-1 canvas').evaluate(c=>({pixels:c.width,css:parseFloat(c.style.width)}));
 assert.ok(Math.abs(initial.pixels/initial.css-2)<.01);
 await page.screenshot({path:'output/bridging-reading/reader-desktop.png'});
 await page.locator('#zoom').selectOption('2');
 await page.waitForFunction(n=>document.querySelector('#pdf-page-1 canvas').width>n*1.9,initial.pixels);
 await page.locator('#page-number').fill('7');await page.locator('#page-number').press('Enter');
 await page.locator('#page-number').blur();
 await page.waitForFunction(()=>document.querySelector('#pdf-page-7').dataset.rendered==='true');
 await page.locator('#zoom').selectOption('1');
 // Independent scrolling and no horizontal page overflow.
 await page.locator('#reading').evaluate(el=>el.scrollTop=1200);
 const before=await page.evaluate(()=>[document.querySelector('#reading').scrollTop,document.querySelector('#pdf-pages').scrollTop]);
 await page.locator('.knowledge-card').first().click();
 assert.equal(await page.locator('dialog[open]').count(),1);
 await page.screenshot({path:'output/bridging-reading/card-modal.png'});
 await page.keyboard.press('Escape');
 await page.waitForFunction(()=>!document.querySelector('dialog[open]'));
 assert.equal(await page.evaluate(()=>document.activeElement.dataset.card),'clip');
 const after=await page.evaluate(()=>[document.querySelector('#reading').scrollTop,document.querySelector('#pdf-pages').scrollTop]);
 assert.ok(Math.abs(after[0]-before[0])<2);
 assert.ok(Math.abs(after[1]-before[1])<2);
 // Every modal opens and closes.
 for(let i=0;i<10;i++){await page.locator('.knowledge-card').nth(i).click();await page.locator('dialog[open] .close-dialog').click()}
 await page.locator('#reading').evaluate(el=>el.scrollTop=0);
 await page.locator('.evidence summary').first().click();
 const link=page.locator('.evidence .page-link').first();const target=await link.getAttribute('data-page');
 await link.click(); await page.waitForFunction(n=>document.querySelector('#page-number').value===n,target);
 // All figures load; screenshot each one at its original dimension separately if needed.
 for(const img of await page.locator('.figure img').all()) {await img.scrollIntoViewIfNeeded();await img.evaluate(i=>i.decode());assert.ok(await img.evaluate(i=>i.naturalWidth>800))}
 assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
 for(let n=1;n<=10;n++){
  await page.evaluate(n=>window.jumpToPage(n),n);
  await page.waitForFunction(n=>document.querySelector('#pdf-page-'+n).dataset.rendered==='true',n);
 }
 assert.equal(await page.evaluate(()=>document.body.dataset.pdfError),undefined);
 assert.deepEqual(remote,[]);assert.deepEqual(errors,[]);
 console.log('PASS: file://, 10 PDF pages, high-DPI zoom, text layer, navigation/evidence, 12 chapters, 8 images, 10 modal cards, Escape/focus/scroll, zero remote requests.');
 await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});
