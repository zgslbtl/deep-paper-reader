import sys
from pathlib import Path
import fitz
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from common import ROOT
from build_document_index import build_index
from ingest_pdf import ingest
import pytest

def test_actual_pdf_pipeline(tmp_path):
    idx=build_index(ROOT/'examples/demo/paper.pdf',tmp_path/'paper')
    assert len(idx['pages'])==3
    assert len(idx['figures'])==1 and len(idx['tables'])==1
    assert all(len(b['bbox'])==4 for b in idx['blocks'])
    assert any('Mann-Whitney' in b['text'] for b in idx['blocks'])
    assert idx['figures'][0]['extraction_status']=='page_reference'

def test_scan_is_warned(tmp_path):
    doc=fitz.open();doc.new_page();pdf=tmp_path/'blank.pdf';doc.save(pdf);doc.close()
    idx=build_index(pdf,tmp_path/'work')
    assert any('OCR' in w for w in idx['warnings'])
    assert not idx['blocks']

def test_rotation_coordinate_frame(tmp_path):
    doc=fitz.open();p=doc.new_page(width=300,height=500);p.insert_text((40,80),'Visible rotation evidence');p.set_rotation(90);pdf=tmp_path/'rotated.pdf';doc.save(pdf);doc.close()
    idx=build_index(pdf,tmp_path/'work')
    assert idx['pages'][0]['rotation']==90
    assert idx['pages'][0]['width']==300
    assert idx['pages'][0]['height']==500
    pix=fitz.Pixmap(str(tmp_path/'work/pages/page-0001.png'))
    assert pix.width<pix.height
    assert idx['blocks'][0]['bbox'][0]==40

def test_different_pdf_does_not_overwrite(tmp_path):
    out=tmp_path/'work';ingest(ROOT/'examples/demo/paper.pdf',out)
    doc=fitz.open();doc.new_page();pdf=tmp_path/'other.pdf';doc.save(pdf);doc.close()
    with pytest.raises(ValueError,match='different paper'):ingest(pdf,out)
