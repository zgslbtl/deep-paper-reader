/* Original PDF rendering. No fetch, CDN, page screenshots, or persistent server. */
'use strict';
(() => {
  const host = document.querySelector('#pdf-pages');
  const status = document.querySelector('#pdf-status');
  const pageInput = document.querySelector('#page-number');
  const decode = value => Uint8Array.from(atob(value), c => c.charCodeAt(0));
  const pages = [];
  let doc, zoom = 1, active = 1, scheduled = false, resizing;

  function fail(error) {
    const box = document.querySelector('#pdf-error');
    box.hidden = false;
    box.querySelector('details p').textContent = error.message || String(error);
    status.textContent = 'PDF 加载未完成 · 请使用上方备用打开方式';
    document.body.dataset.pdfError = 'true';
    console.error(error);
  }
  class LocalBinaryDataFactory {
    async fetch({ filename }) {
      const value = window.PDF_RESOURCES[filename];
      if (!value) throw new Error('Missing bundled PDF resource: ' + filename);
      return decode(value);
    }
  }
  function fitScale(record) {
    return Math.max(180, host.clientWidth - 36) / record.base.width * zoom;
  }
  function layout() {
    for (const r of pages) {
      const viewport = r.page.getViewport({scale:fitScale(r)});
      r.element.style.width = viewport.width + 'px';
      r.element.style.height = viewport.height + 'px';
    }
  }
  async function render(r) {
    const scale = fitScale(r), density = window.devicePixelRatio || 1;
    const signature = scale.toFixed(4) + ':' + density;
    if (r.signature === signature) return;
    r.signature = signature;
    r.task?.cancel(); r.textLayer?.cancel();
    const viewport = r.page.getViewport({scale});
    const canvas = document.createElement('canvas');
    canvas.setAttribute('aria-label', 'Original PDF page ' + r.number);
    canvas.width = Math.floor(viewport.width * density);
    canvas.height = Math.floor(viewport.height * density);
    canvas.style.width = viewport.width + 'px';
    canvas.style.height = viewport.height + 'px';
    const text = document.createElement('div'); text.className = 'textLayer';
    const stamp = document.createElement('span'); stamp.className = 'page-stamp'; stamp.textContent = r.number;
    r.element.style.setProperty('--total-scale-factor', scale);
    r.element.replaceChildren(canvas, text, stamp);
    const task = r.page.render({canvasContext:canvas.getContext('2d'),viewport,transform:[density,0,0,density,0,0]});
    r.task = task;
    try {
      await task.promise;
      if (r.signature !== signature) return;
      r.textLayer = new pdfjsLib.TextLayer({textContentSource:r.page.streamTextContent(),container:text,viewport});
      await r.textLayer.render();
      r.element.dataset.rendered = 'true';
    } catch (e) {
      if (e.name !== 'RenderingCancelledException' && e.name !== 'AbortException') {
        r.signature = null; fail(e);
      }
    }
  }
  function update() {
    scheduled = false;
    const rect = host.getBoundingClientRect();
    let nearest = 1;
    for (const r of pages) {
      const box = r.element.getBoundingClientRect();
      if (box.top <= rect.top + host.clientHeight * .25) nearest = r.number;
      if (box.bottom > rect.top - 250 && box.top < rect.bottom + 250) render(r);
      // Release distant canvases; large PDFs do not keep every page at high DPI.
      else if (r.signature && Math.abs(r.number - active) > 3) {
        r.task?.cancel(); r.textLayer?.cancel(); r.signature = null;
        r.element.replaceChildren(); delete r.element.dataset.rendered;
      }
    }
    active = nearest;
    if (document.activeElement !== pageInput) pageInput.value = active;
  }
  function schedule() { if (!scheduled) { scheduled = true; requestAnimationFrame(update); } }
  window.jumpToPage = async number => {
    if (!doc) return;
    number = Math.max(1,Math.min(pages.length,Math.floor(Number(number)||1)));
    const r = pages[number-1];
    host.scrollTop += r.element.getBoundingClientRect().top - host.getBoundingClientRect().top - 18;
    active = number; pageInput.value = number;
    document.querySelectorAll('.pdf-page.target').forEach(p => p.classList.remove('target'));
    r.element.classList.add('target');
    status.textContent = 'Page ' + number + ' / ' + pages.length + ' · Original PDF';
    await render(r); schedule();
  };
  async function init() {
    const workerURL = URL.createObjectURL(new Blob([window.PDF_WORKER_SOURCE], {type:'text/javascript'}));
    pdfjsLib.GlobalWorkerOptions.workerPort = new Worker(workerURL);
    window.addEventListener('pagehide',()=>{pdfjsLib.GlobalWorkerOptions.workerPort?.terminate();URL.revokeObjectURL(workerURL);},{once:true});
    const bytes = decode(window.PDF_BASE64); delete window.PDF_BASE64; delete window.PDF_WORKER_SOURCE;
    doc = await pdfjsLib.getDocument({data:bytes,BinaryDataFactory:LocalBinaryDataFactory,useWorkerFetch:false,isEvalSupported:false}).promise;
    host.replaceChildren();
    for (let number=1;number<=doc.numPages;number++) {
      const page=await doc.getPage(number), element=document.createElement('div');
      element.className='pdf-page';element.id='pdf-page-'+number;
      element.dataset.page=number;
      pages.push({number,page,base:page.getViewport({scale:1}),element});host.append(element);
    }
    pageInput.max=doc.numPages;document.querySelector('#page-count').textContent='/ '+doc.numPages;
    layout();await render(pages[0]);schedule();
    host.addEventListener('scroll',schedule,{passive:true});
    document.querySelector('#previous').onclick=()=>window.jumpToPage(active-1);
    document.querySelector('#next').onclick=()=>window.jumpToPage(active+1);
    pageInput.onchange=()=>window.jumpToPage(pageInput.value);
    pageInput.onkeydown=e=>{if(e.key==='Enter'){e.preventDefault();window.jumpToPage(pageInput.value);pageInput.blur();}};
    document.querySelector('#zoom').onchange=e=>{zoom=Number(e.target.value);const anchor=active;layout();window.jumpToPage(anchor);};
    new ResizeObserver(()=>{clearTimeout(resizing);resizing=setTimeout(()=>{const anchor=active;layout();window.jumpToPage(anchor);},100);}).observe(host);
    status.textContent='Original PDF · '+doc.numPages+' pages · 文本可选择';
    document.body.dataset.pdfReady='true';
  }
  init().catch(fail);
})();
