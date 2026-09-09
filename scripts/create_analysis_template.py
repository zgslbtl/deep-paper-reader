"""Create a schema-shaped draft only. Codex must replace it after reading the paper."""
import argparse
from pathlib import Path
from common import ROOT,read_json,write_json

def blank():
    return {'summary_zh':'文章未报告。','summary_en':'Not reported in the paper.','status':'not_reported','evidence':[]}

def template(paper_id):
    schema=read_json(ROOT/'schemas/paper_analysis.schema.json')
    def fill(s):
        if s.get('$ref')=='#/$defs/claim':return blank()
        if s.get('type')=='object':return {k:fill(v) for k,v in s['properties'].items()}
        if s.get('type')=='array':return []
        if 'enum' in s:return s['enum'][0]
        return ''
    result=fill(schema);result['metadata']['paper_id']=paper_id
    items=schema['properties']['reproducibility']['items']['properties']['item']['enum']
    result['reproducibility']=[{'item':k,'status':'not_reported','assessment':blank()} for k in items]
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('folder');args=p.parse_args();folder=Path(args.folder)
    target=folder/'paper_analysis.draft.json'
    if target.exists():p.exit(1,'ERROR: draft exists; refusing to overwrite.\n')
    write_json(target,template(read_json(folder/'document_index.json')['paper_id']))
    print('Draft created. These defaults are NOT findings of absence. Read every page, fill all applicable entities, then save paper_analysis.json.')
