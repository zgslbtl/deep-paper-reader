"""Phase 4/5: validate, export Markdown, and build a standalone offline reader."""
import argparse
import hashlib
import shutil
import tempfile
from pathlib import Path
from common import ROOT, read_json, write_json
from validate_evidence import validate_files, walk

def markdown(analysis):
    lines=['# Deep Paper Reader','',analysis['metadata']['title']['summary_zh'],
           analysis['metadata']['title']['summary_en'],'','Source: paper evidence only.','']
    for key,value in analysis.items():
        lines.extend(['## '+key.replace('_',' ').title(),''])
        for path,item in walk(value,key):
            if {'summary_zh','summary_en','status','evidence'}<=item.keys():
                lines.extend(['### '+path,'',f'**{item["status"]}**',item['summary_zh'],item['summary_en'],''])
                for e in item['evidence']:
                    lines.extend([f'> {e["quote"].replace(chr(10), " ")}',f'— p.{e["page"]} · {e["section"]} · {e["block_id"]}',''])
    return '\n'.join(lines)

def safe_asset(folder, rel):
    p=(folder/rel).resolve()
    if not p.is_relative_to(folder.resolve()) or not p.is_file():
        raise ValueError(f'Invalid/missing local asset: {rel}')
    return p

def build(folder,out,allow_warnings=False):
    folder,out=Path(folder).resolve(),Path(out).resolve()
    if folder==out or folder.is_relative_to(out):
        raise ValueError('Build output must not contain or replace the source folder.')
    r=validate_files(folder)
    if r['status']=='ERROR' or (r['status']=='WARN' and not allow_warnings):
        raise ValueError('Evidence validation did not pass. Inspect validation_report.json; manually review warnings before --allow-warnings.')
    index=read_json(folder/'document_index.json');analysis=read_json(folder/'paper_analysis.json')
    if hashlib.sha256((folder/'paper.pdf').read_bytes()).hexdigest()!=index['source_sha256']:
        raise ValueError('PDF hash does not match indexed source.')
    if out.exists() and not (out/'.deep-paper-reader-build').exists():
        raise ValueError('Refusing to replace an unmarked directory; select a fresh build output.')
    out.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(dir=out.parent,prefix='.dpr-build-') as tmp:
        stage=Path(tmp)/'site';shutil.copytree(ROOT/'ui',stage)
        assets={p['image_path'] for p in index['pages']}
        assets|={v['image_path'] for k in ('figures','tables') for v in analysis[k] if v['image_path']}
        for rel in assets|{'paper.pdf'}:
            src=safe_asset(folder,rel);dst=stage/rel
            dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
        for name in ('document_index','paper_analysis','knowledge_cards','field_context','validation_report'):
            shutil.copy2(folder/f'{name}.json',stage/f'{name}.json')
        (stage/'analysis.md').write_text(markdown(analysis),encoding='utf-8')
        (stage/'.deep-paper-reader-build').write_text('v0.1\n')
        if out.exists():shutil.rmtree(out)
        shutil.move(str(stage),str(out))
    return out

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('folder');p.add_argument('--out',required=True);p.add_argument('--allow-warnings',action='store_true')
    args=p.parse_args()
    try:print('PASS: built',build(args.folder,args.out,args.allow_warnings))
    except (ValueError,OSError) as e:p.exit(1,f'ERROR: {e}\n')
