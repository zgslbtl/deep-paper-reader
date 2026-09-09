import copy
import sys
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from common import ROOT,read_json,schema_errors
from validate_evidence import validate,normalize
from build_reader import build

@pytest.fixture
def pair():
    return (read_json(ROOT/'examples/demo/document_index.json'),read_json(ROOT/'examples/demo/paper_analysis.json'))

def test_valid_demo(pair):assert validate(*pair)['status']=='PASS'

@pytest.mark.parametrize('mutation',[
    lambda a:a['paper_map']['purpose']['evidence'][0].pop('page'),
    lambda a:a['paper_map']['purpose'].update(status='probably'),
    lambda a:a['paper_map']['purpose'].update(evidence=[]),
    lambda a:a['paper_map']['purpose']['evidence'][0].update(page=999),
    lambda a:a['paper_map']['purpose']['evidence'][0].update(block_id='B99999'),
    lambda a:a['paper_map']['purpose']['evidence'][0].update(quote='A completely fabricated quotation absent from this paper.'),
    lambda a:a['paper_map']['purpose']['evidence'][0].update(bbox=[0,0,1,1]),
    lambda a:a['paper_map']['purpose']['evidence'][0].update(section='Invented Section'),
    lambda a:a['paper_map']['hypotheses'].update(evidence=a['paper_map']['purpose']['evidence']),
    lambda a:a['paper_map']['hypotheses'].update(summary_en='Probably not tested.'),
    lambda a:a['analysis_steps'][0].update(input_data=['D404']),
    lambda a:a['analysis_steps'][0].update(related_figures=['F404']),
    lambda a:a['analysis_steps'][0].update(related_results=['R404']),
    lambda a:a['research_logic']['edges'][0].update(target='N404'),
    lambda a:a['research_logic']['nodes'][0].update(entity_ref='R404'),
    lambda a:a['research_logic']['nodes'][6].update(entity_ref='D01'),
    lambda a:a['paper_map']['data'].update(evidence=[a['paper_map']['data']['evidence'][0]]*2),
    lambda a:a['data_items'][2].update(derived_from=[]),
    lambda a:a['data_items'][0].update(derived_from=['D02']),
    lambda a:a['reproducibility'].pop(),
    lambda a:a['figures'].clear(),
    lambda a:a['metadata'].update(paper_id='Pother'),
])
def test_invalid_cases(pair,mutation):
    index,analysis=pair;mutation(analysis)
    assert validate(index,analysis)['status']=='ERROR'

def test_approximate_quote_warns(pair):
    index,a=pair;a['paper_map']['purpose']['evidence'][0]['quote']=a['paper_map']['purpose']['evidence'][0]['quote'].replace('compare','comparx')
    assert validate(index,a)['status']=='WARN'

def test_malformed_input_reports_not_crashes(pair):
    index,a=pair;a['analysis_steps']=42
    assert validate(index,a)['status']=='ERROR'

def test_quote_normalization():
    assert normalize('analy-\nsis  A\tB')=='analysis a b'

def test_external_provenance():
    assert schema_errors({'generation_status':'generated','context':[{'provenance':'explicit','text_zh':'x','text_en':'x','references':[]}]},'field_context')

def test_build_and_exports(tmp_path):
    out=build(ROOT/'examples/demo',tmp_path/'reader')
    for name in ['index.html','app.js','styles.css','paper.pdf','paper_analysis.json','knowledge_cards.json','field_context.json','analysis.md']:
        assert (out/name).is_file()
    assert 'not_reported' in (out/'analysis.md').read_text()
    assert (out/'pages/page-0003.png').is_file()

def test_build_rejects_bad_analysis(tmp_path,pair):
    import shutil
    source=tmp_path/'source';shutil.copytree(ROOT/'examples/demo',source)
    a=read_json(source/'paper_analysis.json');a['analysis_steps'][0]['input_data']=['D404']
    from common import write_json
    write_json(source/'paper_analysis.json',a)
    with pytest.raises(ValueError,match='validation'):build(source,tmp_path/'reader')
    assert not (tmp_path/'reader').exists()

def test_build_preserves_unrelated_directory(tmp_path):
    out=tmp_path/'existing';out.mkdir();(out/'important.txt').write_text('preserve')
    with pytest.raises(ValueError,match='unmarked'):build(ROOT/'examples/demo',out)
    assert (out/'important.txt').read_text()=='preserve'

def test_whitespace_quote_rejected(pair):
    index,a=pair;a['paper_map']['purpose']['evidence'][0]['quote']='   '
    assert validate(index,a)['status']=='ERROR'

def test_empty_document_rejected(pair):
    index,a=pair;index['pages']=[]
    assert validate(index,a)['status']=='ERROR'

def test_external_requires_sources():
    assert schema_errors({'generation_status':'generated','context':[{'provenance':'external_knowledge','text_zh':'测试','text_en':'Test','references':[]}]},'field_context')

def test_missing_knowledge_file_blocks_build(tmp_path):
    import shutil
    source=tmp_path/'source';shutil.copytree(ROOT/'examples/demo',source);(source/'knowledge_cards.json').unlink()
    with pytest.raises(ValueError,match='validation'):build(source,tmp_path/'reader')
