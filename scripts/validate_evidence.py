"""Validate structural provenance and typed references. Does not prove entailment."""
import argparse
import difflib
import re
import unicodedata
from pathlib import Path
from common import read_json, write_json, schema_errors

def normalize(s):
    s = unicodedata.normalize('NFKC', s).replace('\u00ad', '')
    s = re.sub(r'-\s*\n\s*', '', s)
    return ' '.join(s.split()).casefold()

def walk(value, path=''):
    if isinstance(value, dict):
        yield path, value
        for key, child in value.items():
            yield from walk(child, f'{path}/{key}')
    elif isinstance(value, list):
        for n, child in enumerate(value):
            yield from walk(child, f'{path}/{n}')

def validate(index, analysis, extra_claims=None):
    issues = []
    def issue(level, path, message):
        issues.append({'level': level, 'path': path, 'message': message})
    for name, value in [('document_index',index),('paper_analysis',analysis)]:
        for error in schema_errors(value, name):
            issue('ERROR', f'{name}/{error["path"]}', error['message'])
    # Reject malformed structures before following references; never crash on invalid JSON shapes.
    if issues:
        return report(issues)
    pages = {p['page']:p for p in index['pages']}
    blocks = {b['block_id']:b for b in index['blocks']}
    if len(pages) != len(index['pages']) or sorted(pages) != list(range(1,len(pages)+1)):
        issue('ERROR','pages','Page numbers must be unique and contiguous from 1.')
    if len(blocks) != len(index['blocks']):
        issue('ERROR','blocks','Duplicate block ID.')
    for block in blocks.values():
        p = pages.get(block['page'])
        if not p:
            issue('ERROR',block['block_id'],'Block page does not exist.')
            continue
        x0,y0,x1,y1 = block['bbox']
        if not (0 <= x0 < x1 <= p['width']+1 and 0 <= y0 < y1 <= p['height']+1):
            issue('ERROR',block['block_id'],'Block bbox outside page or reversed.')
    section_at = {}
    current = ''
    starts = {s['block_id']:s for s in index['sections']}
    for section in index['sections']:
        b = blocks.get(section['block_id'])
        if not b or b['page'] != section['page']:
            issue('ERROR','sections','Section block/page mismatch.')
    for b in index['blocks']:
        if b['block_id'] in starts:
            current = starts[b['block_id']]['title']
        section_at[b['block_id']] = current
    if analysis['metadata']['paper_id'] != index['paper_id']:
        issue('ERROR','metadata/paper_id','Analysis belongs to a different paper.')
    for path, item in walk({'paper_analysis': analysis, 'extensions': extra_claims or []}):
        if item.get('status') == 'supported_synthesis':
            if len({e['block_id'] for e in item['evidence']}) < 2:
                issue('ERROR',path,'Synthesis requires at least two distinct evidence blocks.')
        if {'quote','block_id','page'} <= item.keys():
            block = blocks.get(item['block_id'])
            if item['page'] not in pages:
                issue('ERROR',path,'Referenced page does not exist.')
            if not block:
                issue('ERROR',path,'Referenced block_id does not exist.'); continue
            if block['page'] != item['page']:
                issue('ERROR',path,'Evidence page does not match block page.')
            if any(abs(a-b)>1 for a,b in zip(item['bbox'],block['bbox'])):
                issue('ERROR',path,'Evidence bbox must match indexed block bbox (1 point tolerance).')
            if item['section'] != section_at.get(item['block_id'],''):
                issue('ERROR',path,'Section must match the indexed section; use empty string when unknown.')
            quote, source = normalize(item['quote']), normalize(block['text'])
            if not quote:
                issue('ERROR',path,'Quote must not be whitespace only.')
            elif quote not in source:
                ratio = max((difflib.SequenceMatcher(None,quote,source[max(0,m.b-m.a):max(0,m.b-m.a)+len(quote)]).ratio()
                             for m in difflib.SequenceMatcher(None,quote,source).get_matching_blocks()),default=0)
                if ratio >= .88:
                    issue('WARN',path,f'Quote only approximately matches block ({ratio:.2f}); manually verify transcription.')
                else:
                    issue('ERROR',path,'Quote not found in referenced block.')
    groups = {'data_items':'data_id','analysis_steps':'analysis_id','figures':'figure_id','tables':'table_id',
              'results':'result_id','findings':'finding_id','interpretations':'interpretation_id','contributions':'contribution_id'}
    ids={key:{x[idkey] for x in analysis[key]} for key,idkey in groups.items()}
    all_ids=set()
    for key,idkey in groups.items():
        if len(ids[key]) != len(analysis[key]) or all_ids & ids[key]:
            issue('ERROR',key,'Duplicate entity ID (IDs must be globally unique).')
        all_ids |= ids[key]
    refmap={'input_data':'data_items','output_data':'data_items','derived_from':'data_items','used_in':'analysis_steps',
            'depends_on':'analysis_steps','analysis_ids':'analysis_steps','related_figures':'figures','related_tables':'tables',
            'related_results':'results','result_ids':'results','finding_ids':'findings','linked_findings':'findings'}
    for path,item in walk(analysis):
        for key,target in refmap.items():
            if key in item:
                for ref in item[key]:
                    if ref not in ids[target]:
                        issue('ERROR',f'{path}/{key}',f'Invalid {target} reference: {ref}')
    for item in analysis['data_items']:
        if item['kind']=='collected' and item['derived_from']:
            issue('ERROR',item['data_id'],'Collected data cannot have derived_from; classify as derived.')
        if item['kind']=='derived' and not item['derived_from']:
            issue('ERROR',item['data_id'],'Derived metrics must reference their input data.')
        if item['data_id'] in item['derived_from']:
            issue('ERROR',item['data_id'],'Data cannot derive from itself.')
    nodes=analysis['research_logic']['nodes']; node_ids={n['node_id'] for n in nodes}
    if len(node_ids)!=len(nodes):
        issue('ERROR','research_logic/nodes','Duplicate node ID.')
    typed={'data':'data_items','metric':'data_items','processing':'analysis_steps','analysis':'analysis_steps',
           'result':'results','finding':'findings','interpretation':'interpretations','contribution':'contributions'}
    for n in nodes:
        ref=n['entity_ref']
        if ref and ref not in (ids[typed[n['type']]] if n['type'] in typed else all_ids):
            issue('ERROR',n['node_id'],'Invalid or incorrectly typed entity_ref.')
        if n['type']=='research_question' and analysis['paper_map']['research_questions']['status']=='not_reported':
            issue('ERROR',n['node_id'],'Do not invent a research-question node when no RQ is reported.')
    for edge in analysis['research_logic']['edges']:
        if edge['source'] not in node_ids or edge['target'] not in node_ids:
            issue('ERROR','research_logic/edges','Edge references nonexistent node.')
    for key in ('figures','tables'):
        indexed={x['id']:x for x in index[key]}
        present=ids[key]
        for missing in indexed.keys()-present:
            issue('ERROR',key,f'Detected {missing} omitted from analysis; retain it with not_reported fields if needed.')
        for visual in analysis[key]:
            if visual['page'] not in pages:
                issue('ERROR',key,'Figure/table page does not exist.')
            if visual['extraction_status']=='extracted' and not visual['image_path']:
                issue('ERROR',key,'Extracted visual requires image_path.')
    expected=set(read_json(Path(__file__).resolve().parents[1]/'schemas/paper_analysis.schema.json')['properties']['reproducibility']['items']['properties']['item']['enum'])
    actual=[r['item'] for r in analysis['reproducibility']]
    if set(actual)!=expected or len(actual)!=len(expected):
        issue('ERROR','reproducibility','Include every checklist item exactly once.')
    for check in analysis['reproducibility']:
        status=check['assessment']['status']
        if (check['status']=='not_reported') != (status=='not_reported'):
            issue('ERROR','reproducibility/'+check['item'],'Checklist status contradicts assessment provenance.')
    return report(issues)

def report(issues):
    return {'status':'ERROR' if any(x['level']=='ERROR' for x in issues) else 'WARN' if issues else 'PASS',
            'issues':issues,'scope':'Schema, source anchoring and reference integrity only. Codex must review semantic entailment, omissions, and synthesis.'}

def validate_files(folder):
    folder=Path(folder)
    extension_issues=[];extra_claims=[]
    for name in ('knowledge_cards','field_context'):
        path=folder/f'{name}.json'
        if not path.exists():
            extension_issues.append({'level':'ERROR','path':name,'message':'Required independent extension JSON is missing.'})
            continue
        value=read_json(path);errors=schema_errors(value,name)
        for e in errors:
            extension_issues.append({'level':'ERROR','path':name+'/'+e['path'],'message':e['message']})
        if errors or name!='knowledge_cards':continue
        cards=value['cards'];card_ids={c['card_id'] for c in cards}
        if len(card_ids)!=len(cards):
            extension_issues.append({'level':'ERROR','path':name,'message':'Duplicate card IDs.'})
        for c in cards:
            extra_claims.extend([c['paper_usage'],c['how_defined'],c['how_derived']])
            if any(ref not in card_ids for ref in c['related_cards']):
                extension_issues.append({'level':'ERROR','path':c['card_id'],'message':'Unknown related card ID.'})
            if c['derivation_status']!=c['how_derived']['status']:
                extension_issues.append({'level':'ERROR','path':c['card_id'],'message':'Derivation status contradicts paper evidence.'})
    result=validate(read_json(folder/'document_index.json'),read_json(folder/'paper_analysis.json'),extra_claims)
    result=report(result['issues']+extension_issues)
    write_json(folder/'validation_report.json',result)
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('folder');p.add_argument('--strict',action='store_true')
    args=p.parse_args()
    try:
        r=validate_files(args.folder)
        print(r['status'],f'({len(r["issues"])} issues)')
        for x in r['issues']:print(x['level'],x['path'],x['message'])
        print(r['scope'])
        raise SystemExit(1 if r['status']=='ERROR' or (args.strict and r['status']=='WARN') else 0)
    except (ValueError,OSError) as e:p.exit(1,f'ERROR: {e}\n')
