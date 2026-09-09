"""Phase 0: copy a PDF and record its identity, without inferring content."""
import argparse
import hashlib
import shutil
from pathlib import Path
import fitz
from common import write_json

def ingest(pdf, out):
    pdf, out = Path(pdf).resolve(), Path(out).resolve()
    if not pdf.is_file():
        raise ValueError(f'PDF does not exist: {pdf}')
    with fitz.open(pdf) as doc:
        if doc.needs_pass:
            raise ValueError('Encrypted PDF requires an unlocked local copy.')
        if not doc.is_pdf or len(doc) == 0:
            raise ValueError('Expected a non-empty PDF.')
        count = len(doc)
    digest = hashlib.sha256(pdf.read_bytes()).hexdigest()
    out.mkdir(parents=True, exist_ok=True)
    target = out / 'paper.pdf'
    if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest() != digest:
        raise ValueError('Output contains a different paper. Use a new output directory.')
    if pdf != target:
        shutil.copy2(pdf, target)
    manifest = {'paper_id': 'P' + digest[:16], 'sha256': digest, 'pages': count,
                'source_name': pdf.name, 'pdf': 'paper.pdf'}
    write_json(out / 'ingest.json', manifest)
    return manifest

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('pdf'); p.add_argument('--out', required=True)
    args = p.parse_args()
    try:
        print(ingest(args.pdf, args.out))
    except (ValueError, OSError) as e:
        p.exit(1, f'ERROR: {e}\n')
