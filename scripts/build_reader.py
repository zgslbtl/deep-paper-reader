"""Build a self-contained reading folder: index.html, original PDF and local assets."""
import argparse
import base64
import html
import json
import re
import shutil
import tempfile
import warnings
from pathlib import Path
from urllib.parse import urlsplit
import fitz

ROOT = Path(__file__).resolve().parents[1]

def esc(value):
    return html.escape(str(value), quote=True)

def local_file(root, name):
    path = (root / name).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_file():
        raise ValueError(f'Missing or invalid local resource: {name}')
    return path

def walk(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)

def check_content(content, pdf, folder):
    if not isinstance(content, dict) or not content.get('paper', {}).get('title'):
        raise ValueError('Content needs paper.title.')
    if not isinstance(content.get('sections'), list) or not content['sections']:
        raise ValueError('Content needs a nonempty sections list.')
    for section in content['sections']:
        if not isinstance(section, dict) or not section.get('title'):
            raise ValueError('Each section needs a title.')
        for figure in section.get('figures', []):
            if not all(figure.get(k) for k in ('title', 'image', 'caption', 'blocks')):
                raise ValueError('Each figure needs a title, image, caption and explanation blocks.')
    with fitz.open(pdf) as doc:
        if doc.needs_pass or not doc.is_pdf or not len(doc):
            raise ValueError('Use a nonempty, unlocked PDF.')
        texts = [p.get_text() for p in doc]
    cards = content.get('knowledge_cards', [])
    keys = [c.get('id') for c in cards]
    if any(not isinstance(k, str) or not re.fullmatch(r'[a-z][a-z0-9-]*', k) for k in keys) or len(set(keys)) != len(keys):
        raise ValueError('Knowledge cards need unique lowercase ids.')
    for c in cards:
        if not c.get('title') or not c.get('summary') or not c.get('sources'):
            raise ValueError('Each knowledge card needs title, summary and external sources.')
    normalize = lambda s: re.sub(r'\s+', '', s).replace('\u00ad', '').casefold()
    for item in walk(content):
        if 'image' in item:
            local_file(folder, item['image'])
        if item.get('kind') == 'EXTERNAL' and not item.get('sources'):
            raise ValueError('EXTERNAL explanations need source links.')
        for source in item.get('sources', []):
            url = urlsplit(source.get('url', ''))
            if url.scheme not in ('https', 'http') or not url.netloc or not source.get('title'):
                raise ValueError('Sources need a title and an http(s) URL.')
        for evidence in item.get('evidence', []):
            page, quote = evidence.get('page'), evidence.get('quote')
            if type(page) is not int or not 1 <= page <= len(texts) or not isinstance(quote, str) or not quote.strip():
                raise ValueError('Evidence needs an existing page and a nonempty quote.')
            if normalize(quote) not in normalize(texts[page - 1]):
                warnings.warn(f'Check original quote on page {page}; PDF extraction may differ (especially figure labels).')
        for key in item.get('cards', []):
            if key not in keys:
                raise ValueError(f'Unknown knowledge card link: {key}')
    return len(texts)

def paragraphs(text, cls=''):
    return ''.join(f'<p class="{cls}">{esc(p)}</p>' for p in str(text or '').split('\n') if p.strip())

def sources(items):
    if not items:
        return ''
    return '<ul class="sources">'+''.join(f'<li><a href="{esc(s["url"])}" target="_blank" rel="noopener noreferrer">{esc(s["title"])}</a></li>' for s in items)+'</ul>'

def evidence(items):
    if not items:
        return ''
    return '<details class="evidence"><summary>View original evidence · 原文</summary>'+''.join(f'<blockquote>{esc(e["quote"])}</blockquote><button class="page-link" data-page="{e["page"]}">Page {e["page"]} ↗</button>' for e in items)+'</details>'

def block(b, level=3):
    kind = b.get('kind', 'PAPER')
    if kind not in ('PAPER', 'EXTERNAL', 'NOT REPORTED'):
        raise ValueError(f'Unknown label: {kind}')
    title = f'<h{level}>{esc(b["title"])}</h{level}>' if b.get('title') else ''
    badge = '' if kind == 'PAPER' else f'<span class="badge {"external" if kind == "EXTERNAL" else "unknown"}">{kind}</span>'
    parts = [f'<div class="reading-block">{title}{badge}', paragraphs(b.get('zh')), paragraphs(b.get('en'), 'english')]
    if b.get('formula'):
        parts.append(f'<pre class="formula">{esc(b["formula"])}</pre>')
    if b.get('table'):
        t = b['table']
        parts.append('<div class="table-wrap" tabindex="0"><table><thead><tr>'+''.join(f'<th scope="col">{esc(x)}</th>' for x in t['headers'])+'</tr></thead><tbody>'+''.join('<tr>'+''.join(f'<td>{esc(x)}</td>' for x in row)+'</tr>' for row in t['rows'])+'</tbody></table></div>')
    if b.get('flow'):
        parts.append('<ol class="flow">'+''.join(f'<li>{esc(x)}</li>' for x in b['flow'])+'</ol>')
    parts.append(evidence(b.get('evidence', [])))
    if b.get('cards'):
        parts.append('<div class="related">理解方法：'+''.join(f'<button class="term-link" data-card="{esc(k)}">{esc(CARD_TITLES[k])} ↗</button>' for k in b['cards'])+'</div>')
    parts.append(sources(b.get('sources', [])))
    if b.get('details'):
        parts.append('<details class="more"><summary>'+esc(b.get('detail_label','展开细节'))+'</summary>'+''.join(block(x, min(level+1,6)) for x in b['details'])+'</details>')
    parts.append('</div>')
    return ''.join(parts)

CARD_TITLES = {}

def render(content):
    global CARD_TITLES
    CARD_TITLES = {c['id']:c['title'] for c in content.get('knowledge_cards', [])}
    sections = []
    for i, s in enumerate(content['sections'], 1):
        sections.append(f'<section class="chapter" id="section-{i}"><div class="chapter-number">{i:02} / PAPER</div><h2>{esc(s["title"])}</h2>')
        sections.extend(block(b) for b in s.get('blocks', []))
        for f in s.get('figures', []):
            sections.append(f'<article class="figure"><h3>{esc(f["title"])}</h3><a class="figure-image" href="{esc(f["image"])}" target="_blank" rel="noopener" aria-label="放大 {esc(f["title"])}"><img src="{esc(f["image"])}" alt="{esc(f["title"])}" loading="lazy"></a><p class="caption">{esc(f["caption"])}</p>')
            sections.extend(block(b, 4) for b in f['blocks'])
            sections.append('</article>')
        sections.append('</section>')
    cards, dialogs = [], []
    for c in content.get('knowledge_cards', []):
        cards.append(f'<button class="knowledge-card" data-card="{esc(c["id"])}"><span class="card-type">{esc(c.get("type",""))}</span><strong>{esc(c["title"])}</strong><span>{esc(c["summary"])}</span><span class="view-details">View details ↗</span></button>')
        dialogs.append(f'<dialog id="card-{esc(c["id"])}" aria-labelledby="title-{esc(c["id"])}"><div class="dialog-top"><span class="badge external">EXTERNAL</span><button class="close-dialog" aria-label="关闭知识卡片">关闭 ×</button></div><div class="dialog-content"><h2 id="title-{esc(c["id"])}">{esc(c["title"])}</h2><p class="lead">{esc(c["summary"])}</p>')
        dialogs.extend(block(b) for b in c.get('blocks', []))
        if c.get('paper_usage'):
            dialogs.append('<section class="paper-usage"><span class="badge">PAPER</span><h3>How it is used in this paper</h3>'+block(c['paper_usage'])+'</section>')
        dialogs.append('<h3>Sources / 延伸阅读</h3>'+sources(c['sources'])+'</div></dialog>')
    field = content.get('field_position')
    field_html = '<section class="field"><h3>Field Position</h3>'+block(field)+'</section>' if field else ''
    template = (ROOT/'ui/index.html').read_text()
    for token,value in {'TITLE':esc(content['paper']['title']),'META':esc(content['paper'].get('meta','')),'SECTIONS':''.join(sections),'CARDS':''.join(cards)+field_html,'DIALOGS':''.join(dialogs)}.items():
        template = template.replace('{{'+token+'}}',value)
    return template

def build(pdf, content_path, out):
    pdf, content_path, out = Path(pdf).resolve(), Path(content_path).resolve(), Path(out).resolve()
    folder = content_path.parent
    if out == folder or pdf.is_relative_to(out) or content_path.is_relative_to(out):
        raise ValueError('Choose an output directory separate from source data.')
    if out.exists() and not (out/'assets/.reader-build').exists():
        raise ValueError('Output already exists and is not a new Reader build.')
    content = json.loads(content_path.read_text(encoding='utf-8'))
    check_content(content, pdf, folder)
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=out.parent) as temp:
        stage = Path(temp)/'reader';assets=stage/'assets';assets.mkdir(parents=True)
        shutil.copytree(ROOT/'ui/vendor',assets/'vendor')
        for name in ('app.js','styles.css','pdf-reader.js'):
            shutil.copy2(ROOT/'ui'/name,assets/name)
        assets.joinpath('paper-data.js').write_text('window.PDF_BASE64="'+base64.b64encode(pdf.read_bytes()).decode()+'";\n')
        # Copy visual assets with generated names, so paths cannot collide with application files.
        for n,item in enumerate(walk(content)):
            if 'image' in item:
                src=local_file(folder,item['image']);name=f'figure-{n}{src.suffix.lower()}'
                shutil.copy2(src,assets/name);item['image']='assets/'+name
        shutil.copy2(pdf,stage/'paper.pdf')
        shutil.copy2(ROOT/'scripts/open_reader.py',assets/'open_reader.py')
        launcher=assets/'打开阅读器.command'
        launcher.write_text('#!/bin/sh\ncd "$(dirname "$0")" || exit 1\nexec python3 open_reader.py\n')
        launcher.chmod(0o755)
        (assets/'.reader-build').write_text('simple-reader-v0.2\n')
        (stage/'index.html').write_text(render(content),encoding='utf-8')
        if out.exists():shutil.rmtree(out)
        shutil.move(str(stage),str(out))
    return out/'index.html'

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('pdf');p.add_argument('content');p.add_argument('--out',required=True)
    args=p.parse_args()
    try:print('Open in your browser:',build(args.pdf,args.content,args.out))
    except (ValueError,OSError,KeyError,TypeError) as e:p.exit(1,f'ERROR: {e}\n')
