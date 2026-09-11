"""Extract page-numbered text, caption candidates and review previews. No analysis."""
import argparse
import hashlib
import re
import shutil
from pathlib import Path
import fitz

CAPTION = re.compile(r'^\s*(?:Fig(?:ure)?\.?|Table)\s*\d+[A-Za-z]?(?:\s|[.:])', re.I)

def extract(pdf, out, dpi=120):
    pdf, out = Path(pdf).resolve(), Path(out).resolve()
    if not 72 <= dpi <= 300:
        raise ValueError('Preview DPI must be between 72 and 300.')
    with fitz.open(pdf) as doc:
        if doc.needs_pass or not doc.is_pdf or len(doc) == 0:
            raise ValueError('Provide a nonempty, unlocked PDF.')
        digest = hashlib.sha256(pdf.read_bytes()).hexdigest()
        if out.exists() and (not (out/'.source-sha256').is_file() or (out/'.source-sha256').read_text().strip() != digest):
            raise ValueError('Choose a new work directory; existing source data will not be overwritten.')
        out.mkdir(parents=True, exist_ok=True)
        (out/'previews').mkdir(exist_ok=True)
        if pdf != out/'paper.pdf':
            shutil.copy2(pdf, out/'paper.pdf')
        (out/'.source-sha256').write_text(digest+'\n')
        text, captions, notes = [], [], []
        for n,page in enumerate(doc,1):
            body = page.get_text('text', sort=True)
            text.append(f'## PDF page {n}\n\n{body}\n')
            page.get_pixmap(dpi=dpi, alpha=False).save(out/f'previews/page-{n:03}.png')
            if not body.strip():
                notes.append(f'Page {n}: no extractable text. Inspect preview; OCR or manual transcription is needed.')
            for item in page.get_text('blocks', sort=True):
                if len(item)>6 and item[6]==0 and CAPTION.match(item[4]):
                    captions.append(f'### PDF page {n}\n\n{item[4].strip()}\n')
        (out/'fulltext.md').write_text('\n'.join(text),encoding='utf-8')
        (out/'captions.md').write_text('# Caption candidates — verify visually\n\n'+'\n'.join(captions),encoding='utf-8')
        (out/'extraction-notes.md').write_text('# Extraction notes\n\nText order and captions are heuristic. Previews are for author review, not the Reader PDF pane.\n\n'+'\n'.join(notes),encoding='utf-8')
        return {'pages':len(doc),'textless_pages':len(notes),'folder':str(out)}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('pdf');p.add_argument('--out',required=True);p.add_argument('--dpi',type=int,default=120)
    a=p.parse_args()
    try:print(extract(a.pdf,a.out,a.dpi))
    except (ValueError,OSError) as e:p.exit(1,f'ERROR: {e}\n')
