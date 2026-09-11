import json
import sys
import subprocess
from pathlib import Path
from urllib.request import urlopen
import fitz
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from build_reader import build, check_content
from extract_pdf import extract

def fixture(tmp_path):
    pdf=tmp_path/'source.pdf'
    with fitz.open() as d:
        d.new_page().insert_text((30,40),'Original evidence.');d.new_page();d.save(pdf)
    content={'paper':{'title':'<script>alert(1)</script>'},'sections':[{'title':'Overview','blocks':[{'zh':'An explanation','evidence':[{'page':1,'quote':'Original evidence.'}]}]}],'knowledge_cards':[]}
    return pdf,content

def test_build_preserves_source_and_escapes(tmp_path):
    pdf,c=fixture(tmp_path);p=tmp_path/'content.json';p.write_text(json.dumps(c))
    index=build(pdf,p,tmp_path/'reader');s=index.read_text()
    assert '&lt;script&gt;alert(1)&lt;/script&gt;' in s
    assert (index.parent/'paper.pdf').read_bytes()==pdf.read_bytes()
    assert (index.parent/'assets/paper-data.js').read_text().startswith('window.PDF_BASE64=')
    assert not list(index.parent.glob('*.json'))
    assert build(pdf,p,index.parent)==index
    with pytest.raises(ValueError):build(pdf,p,tmp_path)

def test_invalid_page_resource_and_source(tmp_path):
    pdf,c=fixture(tmp_path)
    b=c['sections'][0]['blocks'][0]
    b['evidence'][0]['page']=3
    with pytest.raises(ValueError,match='existing page'):check_content(c,pdf,tmp_path)
    b['evidence'][0]['page']=1;b['image']='../outside.png'
    with pytest.raises(ValueError,match='resource'):check_content(c,pdf,tmp_path)
    del b['image'];b.update(kind='EXTERNAL',sources=[{'title':'unsafe','url':'javascript:alert(1)'}])
    with pytest.raises(ValueError,match='http'):check_content(c,pdf,tmp_path)
    b['sources']=[]
    with pytest.raises(ValueError,match='source links'):check_content(c,pdf,tmp_path)

def test_quote_doubt_is_warning(tmp_path):
    pdf,c=fixture(tmp_path)
    c['sections'][0]['blocks'][0]['evidence'][0]['quote']='Not a quote'
    with pytest.warns(UserWarning,match='Check original'):assert check_content(c,pdf,tmp_path)==2

def test_extraction_textless_and_identity(tmp_path):
    pdf,c=fixture(tmp_path);out=tmp_path/'work'
    assert extract(pdf,out)['textless_pages']==1
    assert 'PDF page 2' in (out/'fulltext.md').read_text()
    assert 'OCR or manual' in (out/'extraction-notes.md').read_text()
    assert len(list((out/'previews').glob('*.png')))==2
    other=tmp_path/'other.pdf'
    with fitz.open() as d:d.new_page().insert_text((30,40),'Different paper');d.save(other)
    with pytest.raises(ValueError):extract(other,out)
    assert (out/'paper.pdf').read_bytes()==pdf.read_bytes()

def test_fallback_uses_free_loopback_port(tmp_path):
    pdf,c=fixture(tmp_path);p=tmp_path/'content.json';p.write_text(json.dumps(c))
    root=build(pdf,p,tmp_path/'reader').parent
    proc=subprocess.Popen([sys.executable,str(root/'assets/open_reader.py'),'--no-open'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    try:
        url=proc.stdout.readline().strip()
        assert url.startswith('http://127.0.0.1:') and ':8766/' not in url
        assert urlopen(url,timeout=5).status==200
        assert urlopen(url+'paper.pdf',timeout=5).read()==pdf.read_bytes()
    finally:proc.terminate();proc.communicate(timeout=5)
