// Development only. Readers use the checked-in bundles; no npm is required.
import { build } from 'esbuild';
import { fileURLToPath } from 'node:url';
import { readFile, writeFile, mkdir, readdir, copyFile } from 'node:fs/promises';
const root = new URL('../', import.meta.url);
const path = s => fileURLToPath(new URL(s, root));
await mkdir(path('ui/vendor'), {recursive:true});
await build({entryPoints:[path('node_modules/pdfjs-dist/legacy/build/pdf.mjs')],bundle:true,format:'iife',globalName:'pdfjsLib',platform:'browser',target:'es2022',minify:true,outfile:path('ui/vendor/pdf.js')});
const worker = await build({entryPoints:[path('node_modules/pdfjs-dist/legacy/build/pdf.worker.mjs')],bundle:true,format:'iife',platform:'browser',target:'es2022',minify:true,write:false});
await writeFile(path('ui/vendor/worker.js'),'window.PDF_WORKER_SOURCE='+JSON.stringify(worker.outputFiles[0].text)+';\n');
const resources={};
for (const dir of ['cmaps','standard_fonts','wasm']) {
 for(const name of await readdir(path('node_modules/pdfjs-dist/'+dir))){
  if(name.endsWith('.bcmap')||name.endsWith('.pfb')||name.endsWith('.ttf')||name.endsWith('.wasm'))resources[name]=(await readFile(path('node_modules/pdfjs-dist/'+dir+'/'+name))).toString('base64');
 }
}
await writeFile(path('ui/vendor/resources.js'),'window.PDF_RESOURCES='+JSON.stringify(resources)+';\n');
await copyFile(path('node_modules/pdfjs-dist/LICENSE'),path('ui/vendor/LICENSE.pdfjs'));
for (const dir of ['cmaps','standard_fonts','wasm']) {
 for(const name of await readdir(path('node_modules/pdfjs-dist/'+dir)))if(name.startsWith('LICENSE'))await copyFile(path('node_modules/pdfjs-dist/'+dir+'/'+name),path('ui/vendor/'+dir+'-'+name));
}

const css = await readFile(path('node_modules/pdfjs-dist/web/pdf_viewer.css'),'utf8');
await writeFile(path('ui/vendor/text-layer.css'), '/* PDF.js text layer, Apache-2.0; see LICENSE.pdfjs */\n'+css.slice(css.indexOf('.textLayer{'),css.indexOf('.textLayerImages{')));
