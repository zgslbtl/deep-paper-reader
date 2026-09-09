"""Phase 1: text blocks, heuristic section/caption index, offline page images.

Coordinates are in unrotated PyMuPDF page space (top-left points). Rendered
images are deliberately unrotated too, so evidence overlays use one frame.
Vector figures and ambiguous crops retain an explicit full-page fallback.
"""
import argparse
import re
from pathlib import Path
import fitz
from common import ROOT, read_json, write_json, require_schema
from ingest_pdf import ingest
CAPTION = re.compile(r'^\s*(Fig(?:ure)?\.?|Table)\s*([A-Za-z]?\d+[A-Za-z]?)(?:\s|[.:])', re.I)
SECTION = re.compile(r'^(?:\d+(?:\.\d+)*[.\s]+)?(?:abstract|introduction|background|related work|methods?|methodology|study(?: design| \d+)?|participants|procedure|data analysis|results?|discussion|limitations|conclusions?|references|bibliography|ethics|materials)(?:\s*[:.].*)?$', re.I)

def build_index(pdf, out):
    out = Path(out)
    manifest = ingest(pdf, out)
    dpi = read_json(ROOT / 'config/default.json')['render_dpi']
    (out / 'pages').mkdir(exist_ok=True)
    index = {'paper_id': manifest['paper_id'], 'source_sha256': manifest['sha256'],
             'metadata': {'title': '', 'authors': [], 'year': None, 'doi': '', 'venue': '',
                          'source': 'pdf_metadata_unverified'},
             'pages': [], 'sections': [], 'blocks': [], 'figures': [], 'tables': [],
             'references': [], 'warnings': []}
    in_refs = False
    with fitz.open(out / 'paper.pdf') as doc:
        index['metadata']['title'] = doc.metadata.get('title') or ''
        author = doc.metadata.get('author') or ''
        index['metadata']['authors'] = [author] if author else []
        for number, page in enumerate(doc, 1):
            rotation = page.rotation
            page.set_rotation(0)
            path = f'pages/page-{number:04}.png'
            page.get_pixmap(dpi=dpi, alpha=False).save(out / path)
            text = page.get_text('text', sort=True)
            index['pages'].append({'page': number, 'width': page.rect.width,
                                   'height': page.rect.height, 'rotation': rotation,
                                   'text': text, 'image_path': path})
            if not text.strip():
                index['warnings'].append(f'Page {number}: no extractable text; OCR/manual transcription required before analysis.')
            page_blocks = []
            for raw in page.get_text('blocks', sort=True):
                if raw[6] != 0 or not raw[4].strip():
                    continue
                block = {'block_id': f'B{len(index["blocks"])+1:05}', 'page': number,
                         'text': raw[4].strip(), 'bbox': list(raw[:4])}
                page_blocks.append(block)
                index['blocks'].append(block)
                first = block['text'].splitlines()[0].strip()
                if len(first) < 100 and SECTION.match(first):
                    index['sections'].append({'section_id': f'S{len(index["sections"])+1:03}',
                        'title': first, 'page': number, 'block_id': block['block_id'], 'detection': 'heuristic'})
                    if re.search(r'\b(references|bibliography)\b', first, re.I):
                        in_refs = True
                    elif in_refs:
                        in_refs = False
                if in_refs:
                    index['references'].append({'page': number, 'block_id': block['block_id'],
                                               'text': block['text'], 'detection': 'heuristic'})
            for pos, block in enumerate(page_blocks):
                match = CAPTION.match(block['text'])
                if not match:
                    continue
                key = 'tables' if match[1].lower() == 'table' else 'figures'
                prefix = 'T' if key == 'tables' else 'F'
                index[key].append({'id': f'{prefix}{len(index[key])+1:02}', 'number': match[2],
                    'page': number, 'caption': block['text'], 'block_id': block['block_id'],
                    'bbox': block['bbox'], 'nearby_block_ids': [b['block_id'] for b in page_blocks[max(0,pos-2):pos+3] if b != block],
                    'image_path': path, 'extraction_status': 'page_reference',
                    'warning': 'Full-page preview: complete figure/table boundaries cannot be guaranteed by text parsing.'})
            # Embedded images are extraction candidates only, never silently labelled as full figures.
            for n, img in enumerate(page.get_images(full=True), 1):
                try:
                    blob = doc.extract_image(img[0])
                    assets = out / 'embedded_images'; assets.mkdir(exist_ok=True)
                    (assets / f'p{number}-{n}.{blob["ext"]}').write_bytes(blob['image'])
                except (RuntimeError, ValueError) as e:
                    index['warnings'].append(f'Embedded image p.{number}/{n} extraction failed: {e}')
    index['warnings'].append('Section, caption and reference detection is heuristic; Codex must review every page, including multi-column and vector content. Page references are the visual fallback.')
    require_schema(index, 'document_index')
    write_json(out / 'document_index.json', index)
    for name, empty in [('knowledge_cards', {'generation_status':'not_generated','cards':[]}),
                        ('field_context', {'generation_status':'not_generated','context':[]})]:
        if not (out / f'{name}.json').exists():
            write_json(out / f'{name}.json', empty)
    return index

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('pdf'); p.add_argument('--out', required=True)
    args = p.parse_args()
    try:
        result = build_index(args.pdf, args.out)
        print(f'PASS: {len(result["pages"])} pages, {len(result["blocks"])} blocks, {len(result["figures"])} figures, {len(result["tables"])} tables')
        for warning in result['warnings']:
            print('WARN:', warning)
    except (ValueError, OSError) as e:
        p.exit(1, f'ERROR: {e}\n')
