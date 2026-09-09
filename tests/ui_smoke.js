async (page) => {
  const errors=[];
  page.on('pageerror',e=>errors.push(e.message));
  const remote=[];
  page.on('request',r=>{if(!r.url().startsWith('http://127.0.0.1:8765/')&&!r.url().startsWith('data:'))remote.push(r.url());});
  await page.reload();
  await page.waitForSelector('body[data-ready="true"]');
  const assert=(yes,msg)=>{if(!yes)throw new Error(msg);};
  const summary={};
  for(const [tab,heading]of [['Overview','Paper overview'],['Study','Study design'],['Data & Analysis','Data & analysis'],['Figures & Tables','Figures & tables'],['Logic','Research logic'],['Reproducibility','Reproducibility']]){
    await page.getByRole('tab',{name:tab,exact:true}).click();
    assert(await page.getByRole('heading',{name:heading,exact:true}).count()===1,'Tab failed: '+tab);
  }
  summary.tabs=6;
  await page.getByRole('tab',{name:'Overview',exact:true}).click();
  await page.locator('.evidence-details summary').first().click();
  assert(await page.locator('.evidence-details[open] blockquote').first().isVisible(),'Original evidence did not expand');
  summary.originalEvidence=true;
  await page.getByRole('tab',{name:'Overview',exact:true}).click();
  const evidence=page.getByRole('button',{name:'Evidence page 3, B00030',exact:true});
  assert((await evidence.getAttribute('title')).includes('checklist'),'Quote hover missing');
  await evidence.click();
  await page.waitForSelector('#pdf-page-3 .bbox-highlight');
  let state=await page.evaluate(()=>({page:document.querySelector('#page-number').value,scroll:document.querySelector('#pdf-pages').scrollTop,highlight:!!document.querySelector('#pdf-page-3.active-evidence .bbox-highlight')}));
  assert(state.page==='3'&&state.scroll>0&&state.highlight,'Evidence jump/highlight failed');summary.evidence=state;
  await page.getByLabel('PDF zoom',{exact:true}).selectOption('1.5');
  const align=await page.evaluate(async()=>{
    const idx=await (await fetch('document_index.json')).json();const block=idx.blocks.find(b=>b.block_id==='B00030');
    const p=document.querySelector('#pdf-page-3').getBoundingClientRect(),h=document.querySelector('#pdf-page-3 .bbox-highlight').getBoundingClientRect();
    return Math.abs((h.left-p.left)/p.width-block.bbox[0]/idx.pages[2].width)<.001;
  });assert(align,'Bbox misaligned after zoom');summary.zoomAlignment=true;
  await page.getByLabel('PDF zoom',{exact:true}).selectOption('1');
  await page.getByRole('button',{name:'Previous page',exact:true}).click();
  assert(await page.getByLabel('PDF page',{exact:true}).inputValue()==='2','Page nav failed');
  await page.getByRole('radio',{name:'Article + Background',exact:true}).check();
  assert(await page.getByText('External knowledge cards are not generated yet.',{exact:true}).count()===1,'Knowledge placeholder missing');
  await page.getByRole('radio',{name:'Article Only',exact:true}).check();
  await page.getByRole('searchbox',{name:'Search analysis',exact:true}).fill('Mann');
  assert(await page.getByRole('heading',{name:'Search results',exact:true}).count()===1,'Search failed');
  await page.getByRole('searchbox',{name:'Search analysis',exact:true}).fill('');
  await page.getByRole('tab',{name:'Figures & Tables',exact:true}).click();
  await page.getByRole('button',{name:'Table 1',exact:true}).click();
  assert(await page.getByRole('heading',{name:'Table 1',exact:true}).count()===1,'Table atlas failed');
  await page.getByRole('tab',{name:'Overview',exact:true}).click();
  await page.getByRole('button',{name:'Evidence page 3, B00030',exact:true}).click();
  const images=await page.evaluate(()=>[...document.querySelectorAll('#pdf-pages img')].map(i=>({loaded:i.complete&&i.naturalWidth>0})));
  assert(images.every(x=>x.loaded),'PDF page image failed');
  for(const file of ['paper.pdf','paper_analysis.json','analysis.md','knowledge_cards.json'])assert((await page.request.get('http://127.0.0.1:8765/'+file)).ok(),'Export/load failed '+file);
  assert(!errors.length,'Browser errors: '+errors.join(';'));
  assert(!remote.length,'Unexpected external requests: '+remote.join(';'));
  summary.consoleErrors=errors;summary.externalRequests=remote;summary.pdfPages=images.length;summary.search=true;summary.atlas=true;summary.knowledgeMode=true;summary.exports=true;
  await page.screenshot({path:'output/playwright/reader-evidence.png',fullPage:true});
  return summary;
}
