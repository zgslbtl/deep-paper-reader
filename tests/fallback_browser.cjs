// Force a local Worker restriction in an isolated test context; verify the real fallback.
const { chromium } = require('playwright');
const { spawn } = require('node:child_process');
const { pathToFileURL } = require('node:url');
const path=require('node:path');
const assert=require('node:assert/strict');
(async()=>{
 const root=path.resolve(process.argv[2]||'output/bridging-reader-simple');
 const browser=await chromium.launch({channel:'chrome',headless:true});
 let proc;
 try {
  const restricted=await browser.newPage();
  await restricted.addInitScript(()=>{window.Worker=class{constructor(){throw new Error('Simulated local Worker restriction')}}});
  await restricted.goto(pathToFileURL(path.join(root,'index.html')).href);
  await restricted.waitForSelector('#pdf-error',{state:'visible'});
  assert.ok((await restricted.locator('#pdf-error').textContent()).includes('打开阅读器.command'));
  // Command is invoked with the same cwd as a double-click launcher, without auto-opening a tab.
  proc=spawn('python3',[path.join(root,'assets/open_reader.py'),'--no-open'],{stdio:['ignore','pipe','ignore']});
  const url=await new Promise((resolve,reject)=>{let data='';const timer=setTimeout(()=>reject(new Error('Fallback start timed out')),5000);proc.stdout.on('data',chunk=>{data+=chunk;if(data.includes('\n')){clearTimeout(timer);resolve(data.split('\n')[0])}});proc.on('error',reject)});
  const fallback=await browser.newPage();
  await fallback.goto(url);await fallback.waitForFunction(()=>document.body.dataset.pdfReady==='true');
  assert.equal(await fallback.locator('.pdf-page').count(),10);
  console.log('PASS: simulated restriction shows opening instructions; actual free-port fallback renders 10-page PDF.');
 } finally {proc?.kill();await browser.close()}
})().catch(e=>{console.error(e);process.exit(1)});
