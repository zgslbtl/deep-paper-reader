'use strict';
// The article is static HTML; JavaScript only handles the PDF and reading interactions.
(() => {
  let opener = null;
  document.addEventListener('click', event => {
    const page = event.target.closest('button[data-page]');
    if (page) window.jumpToPage?.(page.dataset.page);
    const card = event.target.closest('[data-card]');
    if (card) {
      const dialog = document.getElementById('card-' + card.dataset.card);
      if (!dialog) return;
      opener = card; dialog.showModal(); dialog.scrollTop=0;
      dialog.querySelector('.close-dialog').focus({preventScroll:true});
    }
    if (event.target.closest('.close-dialog')) event.target.closest('dialog').close();
  });
  document.querySelectorAll('dialog').forEach(dialog => {
    dialog.addEventListener('close',()=>opener?.focus({preventScroll:true}));
    dialog.addEventListener('click',event=>{if(event.target===dialog){const r=dialog.getBoundingClientRect();if(event.clientX<r.left||event.clientX>r.right||event.clientY<r.top||event.clientY>r.bottom)dialog.close();}});
  });
  document.body.dataset.ready = 'true';
})();
