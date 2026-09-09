"""Build an explicitly synthetic fixture. This is not a general paper analyzer."""
import argparse
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from common import write_json
from build_document_index import build_index
from create_analysis_template import template,blank

TEXT = {
 'title': 'A Synthetic Study of Checklist-Assisted Review',
 'notice': 'SYNTHETIC DEMO - invented study and numbers for software testing only.',
 'background': 'Reviewers inspect short reports to identify reporting omissions.',
 'gap': 'This demonstration examines whether a checklist improves omission detection.',
 'rq': 'RQ1: Does checklist access increase the number of omissions detected?',
 'purpose': 'The aim was to compare checklist-assisted review with unaided review.',
 'participants': 'Twelve volunteer graduate students were recruited through a campus email.',
 'assignment': 'Participants were randomly assigned to two groups of six in a between-subjects design.',
 'task': 'Both groups reviewed the same two-page report for 15 minutes and listed omissions.',
 'conditions': 'The checklist group received a printed checklist; the control group reviewed without it.',
 'procedure': 'Participants gave consent, received a two-minute tutorial, completed the task, then rated confidence.',
 'ethics': 'This synthetic demonstration involved no real human participants.',
 'logs': 'The interface recorded each submitted omission and its timestamp during the task.',
 'survey': 'After the task, participants rated confidence on a scale from 1 to 5.',
 'count': 'For each participant, duplicate omission labels were removed and remaining labels were counted.',
 'test': 'We compared omission counts between groups using a two-sided Mann-Whitney U test.',
 'result': 'Median omission counts were 8 for checklist and 5 for control; U = 5, p = 0.041.',
 'finding': 'The checklist group detected more omissions than the control group in this task.',
 'interpretation': 'The authors interpret this pattern as possible support for structured review aids.',
 'contribution': 'This demonstration illustrates a traceable workflow for evaluating a review checklist.',
 'limitation': 'The small sample and single report limit generalization.',
 'figure': 'Figure 1. Median omission counts by condition. Bars encode medians; no error bars are shown.',
 'table': 'Table 1. Data sources and collection times in the synthetic study.',
}

def make_pdf(path):
    c=canvas.Canvas(str(path),pagesize=(612,792));c.setTitle(TEXT['title']);c.setAuthor('Deep Paper Reader synthetic fixture')
    def header(n,section):
        c.setFillColor(HexColor('#45536a'));c.setFont('Helvetica',9)
        c.drawString(44,760,TEXT['notice']);c.drawRightString(568,26,f'{n} / 3')
        c.setFillColor(HexColor('#17212e'));c.setFont('Helvetica-Bold',15);c.drawString(44,720,section)
    def para(key,y):
        import textwrap
        c.setFont('Helvetica',11)
        for line in textwrap.wrap(TEXT[key],88):c.drawString(44,y,line);y-=16
        return y-18
    header(1,'Introduction');y=680
    c.setFont('Helvetica-Bold',16);c.drawString(44,y,TEXT['title']);y-=42
    for key in ['background','gap','rq','purpose']:y=para(key,y)
    c.setFont('Helvetica-Bold',15);c.drawString(44,y,'Study Design');y-=30
    for key in ['participants','assignment','task','conditions']:y=para(key,y)
    c.showPage();header(2,'Methods');y=680
    for key in ['procedure','ethics','logs','survey','count','test']:y=para(key,y)
    y=para('table',y-12)
    c.setFont('Helvetica-Bold',10)
    for x,t in [(44,'Data'),(260,'Collected when'),(430,'Unit')]:c.drawString(x,y,t)
    c.line(44,y-7,568,y-7)
    c.setFont('Helvetica',10)
    for yy,values in [(y-28,['Omission log','During task','Submission']), (y-52,['Confidence rating','After task','Participant'])]:
        for x,t in zip([44,260,430],values):c.drawString(x,yy,t)
    c.showPage();header(3,'Results');y=680
    for key in ['result','finding']:y=para(key,y)
    c.setFont('Helvetica',10);c.drawString(50,490,'Median omission count')
    c.line(90,310,90,475);c.line(90,310,420,310)
    for tick in range(0,9,2):c.drawRightString(82,307+tick*18,str(tick))
    c.setFillColor(HexColor('#607a99'));c.rect(140,310,70,144,fill=1,stroke=0);c.rect(290,310,70,90,fill=1,stroke=0)
    c.setFillColor(HexColor('#17212e'));c.drawString(149,290,'Checklist');c.drawString(305,290,'Control')
    para('figure',265)
    c.setFont('Helvetica-Bold',15);c.drawString(44,205,'Discussion');y=178
    for key in ['interpretation','contribution','limitation']:y=para(key,y)
    c.save()

def demo(out):
    out=Path(out);out.mkdir(parents=True,exist_ok=True);make_pdf(out/'paper.pdf')
    idx=build_index(out/'paper.pdf',out); a=template(idx['paper_id'])
    def evidence(key):
        target=TEXT[key]; norm=lambda s:' '.join(s.split())
        b=next(b for b in idx['blocks'] if norm(target) in norm(b['text']))
        section=''
        for block in idx['blocks']:
            for sec in idx['sections']:
                if sec['block_id']==block['block_id']:section=sec['title']
            if block['block_id']==b['block_id']:break
        return {'page':b['page'],'section':section,'block_id':b['block_id'],'quote':b['text'],'bbox':b['bbox'][:]}
    def claim(key,zh,en=None):return {'summary_zh':zh,'summary_en':en or TEXT[key],'status':'explicit','evidence':[evidence(key)]}
    def synth(keys,zh,en):return {'summary_zh':zh,'summary_en':en,'status':'supported_synthesis','evidence':[evidence(k) for k in keys]}
    a['metadata']['title']=claim('title','清单辅助审阅的合成研究（演示）')
    pm=a['paper_map']
    for field,key,zh in [('background','background','审阅者检查短报告，识别报告遗漏。'),('problem','gap','本演示考察清单能否改善遗漏识别。'),('purpose','purpose','比较清单辅助审阅和无辅助审阅。'),('research_questions','rq','RQ1：使用清单是否增加识别出的遗漏数量？'),('methodology','assignment','随机分为两个各六人的组间条件。'),('participants_or_dataset','participants','通过校园邮件招募十二名研究生志愿者。'),('findings','finding','清单组在此任务中发现更多遗漏。'),('contributions','contribution','展示评估审阅清单的可追溯流程。'),('limitations','limitation','小样本和单份报告限制了推广。')]:pm[field]=claim(key,zh)
    # No claimed literature gap or hypothesis is reported. The stated aim stays an aim.
    pm['data']=synth(['logs','survey'],'采集了任务中的遗漏日志和任务后的信心评分。','The study collected omission logs during the task and confidence ratings afterwards.')
    s=a['study_design']
    for field,key,zh in [('design_type','assignment','随机组间设计。'),('conditions','conditions','清单组与无清单对照组。'),('assignment','assignment','随机分组，每组六人。'),('tasks','task','阅读同一份两页报告，十五分钟内列出遗漏。'),('materials','conditions','清单组使用纸质清单。'),('procedure','procedure','同意参与、两分钟教程、任务、信心评分。'),('ethics','ethics','合成演示，没有真实人类参与者。'),('training','procedure','任务前有两分钟教程。'),('baseline','conditions','对照组在没有清单的情况下审阅。'),('duration','task','任务持续十五分钟。')]:s[field]=claim(key,zh)
    for field,zh in [('n','十二名。'),('population','研究生志愿者。'),('recruitment','通过校园邮件招募。')]:s['participants'][field]=claim('participants',zh)
    s['timeline']=[{'step_id':f'STEP{i}','description':claim(key,zh,en)} for i,(key,zh,en) in enumerate([('participants','邮件招募','Campus email recruitment'),('procedure','同意参与','Consent'),('procedure','两分钟教程','Two-minute tutorial'),('task','十五分钟审阅任务','15-minute review task'),('survey','任务后信心评分','Post-task confidence rating')],1)]
    def data(did,key,zh,kind='collected',derived=None,used=None):
        return {'data_id':did,'kind':kind,'name':claim(key,zh,{'D01':'Omission logs','D02':'Confidence ratings','D03':'Unique omission count'}[did]),'description':claim(key,zh),'unit_of_analysis':blank(),'source':blank(),'collection_method':claim(key,zh),'collection_time':blank(),'purpose':blank(),'derived_from':derived or [],'used_in':used or [],'evidence':[evidence(key)]}
    d1=data('D01','logs','遗漏提交日志',used=['A01']);d1['unit_of_analysis']=claim('logs','每次遗漏提交','Each omission submission');d1['collection_time']=claim('logs','任务过程中','During the task');d1['source']=claim('logs','任务界面','Task interface')
    d2=data('D02','survey','信心评分');d2['collection_time']=claim('survey','任务后','After the task');d2['unit_of_analysis']=claim('survey','参与者','Participant')
    d3=data('D03','count','每位参与者的去重遗漏计数','derived',['D01'],['A02']);d3['unit_of_analysis']=claim('count','参与者','Participant')
    a['data_items']=[d1,d2,d3]
    def step(aid,key,zh,inputs,outputs,depends):
        return {'analysis_id':aid,'name':claim(key,zh),'method':claim(key,zh),'operation':claim(key,zh),'metric':blank(),'analytical_method':blank(),'output':claim(key,zh),'paper_rationale':blank(),'parameters':[],'input_data':inputs,'output_data':outputs,'depends_on':depends,'used_for':blank(),'related_figures':[],'related_tables':[],'related_results':[],'evidence':[evidence(key)]}
    a1=step('A01','count','对每位参与者的遗漏标签去重并计数。',['D01'],['D03'],[]);a1['metric']=claim('count','去重遗漏数量','Unique omission count');a1['output']=claim('count','每位参与者的遗漏计数','Omission count per participant')
    a2=step('A02','test','使用双侧 Mann–Whitney U 比较两组遗漏计数。',['D03'],[],['A01']);a2['analytical_method']=claim('test','双侧 Mann–Whitney U 检验','Two-sided Mann-Whitney U test');a2['metric']=claim('count','去重遗漏数量','Unique omission count');a2['output']=claim('result','中位数、U 与 p 值','Medians, U and p values');a2['related_figures']=['F01'];a2['related_results']=['R01']
    a['analysis_steps']=[a1,a2]
    def ent(idkey,id,key,zh,links):return {idkey:id,'claim':claim(key,zh),**links,'evidence':[evidence(key)]}
    a['results']=[ent('result_id','R01','result','中位数：清单组 8，对照组 5；U = 5，p = 0.041。',{'analysis_ids':['A02']})]
    a['findings']=[ent('finding_id','FIND01','finding','清单组在本任务中发现更多遗漏。',{'result_ids':['R01']})]
    a['interpretations']=[ent('interpretation_id','I01','interpretation','作者认为该模式可能支持结构化审阅辅助工具。',{'finding_ids':['FIND01']})]
    a['contributions']=[ent('contribution_id','C01','contribution','展示评估审阅清单的可追溯流程。',{'finding_ids':['FIND01']})]
    for key,cap,idkey in [('figures','figure','figure_id'),('tables','table','table_id')]:
        v=idx[key][0]
        item={idkey:v['id'],'number':v['number'],'page':v['page'],'caption':claim(cap,'图 1：按条件分组的遗漏数量中位数。' if cap=='figure' else '表 1：合成研究的数据来源与采集时间。'),'image_path':v['image_path'],'extraction_status':'page_reference',**{k:blank() for k in ['purpose','data_source','processing_steps','how_to_read','author_interpretation']},'visual_encoding':{k:blank() for k in ['x_axis','y_axis','color','shape','error_bar']},'linked_findings':[],'evidence':[evidence(cap)]}
        if cap=='figure':
            item['purpose']=claim('figure','比较两组的遗漏数量中位数。');item['data_source']=claim('logs','任务界面的遗漏日志。');item['processing_steps']=claim('count','按参与者去重并计数。');item['visual_encoding']['x_axis']=claim('figure','条件','Condition');item['visual_encoding']['y_axis']=claim('figure','遗漏数量中位数','Median omission count');item['visual_encoding']['error_bar']=claim('figure','未绘制误差线','No error bars shown');item['how_to_read']=claim('figure','条形高度表示中位数。','Bar heights encode medians.');item['author_interpretation']=claim('finding','清单组发现更多遗漏。');item['linked_findings']=['FIND01']
        else:
            item['purpose']=claim('table','列出数据来源和采集时间。');item['data_source']=synth(['logs','survey'],'任务日志与任务后评分。','Task logs and post-task ratings.')
        a[key]=[item]
    chain=[('N1','research_question','rq',None,'研究问题'),('N2','study','assignment',None,'随机组间研究'),('N3','data','logs','D01','遗漏日志'),('N4','processing','count','A01','去重与计数'),('N5','metric','count','D03','遗漏计数'),('N6','analysis','test','A02','组间检验'),('N7','result','result','R01','统计结果'),('N8','finding','finding','FIND01','研究发现'),('N9','interpretation','interpretation','I01','作者解释'),('N10','contribution','contribution','C01','研究贡献')]
    a['research_logic']['nodes']=[{'node_id':nid,'type':kind,'label':claim(key,zh),'entity_ref':ref} for nid,kind,key,ref,zh in chain]
    relations=['addresses','collects','processed_by','produces','analyzed_by','produces','supports','interpreted_as','contributes_to']
    a['research_logic']['edges']=[{'source':chain[i][0],'target':chain[i+1][0],'relation':rel,'claim':synth([chain[i][2],chain[i+1][2]],'根据相邻步骤的论文证据重建此连接。','This link is reconstructed from the paper evidence for its adjacent steps.') if chain[i][2]!=chain[i+1][2] else claim(chain[i][2],'去重计数产生每位参与者的计数。')} for i,rel in enumerate(relations)]
    mapping={'participant_n':'participants','recruitment':'participants','group_assignment':'assignment','task_instructions':'task','study_duration':'task','dataset':'task','data_preprocessing':'count','statistical_test':'test','ethics':'ethics'}
    for check in a['reproducibility']:
        if check['item'] in mapping:
            key=mapping[check['item']];check['status']='reported';check['assessment']=claim(key,{'participants':'招募和人数见引文。','assignment':'分组见引文。','task':'任务信息见引文。','count':'去重计数步骤见引文。','test':'统计检验见引文。','ethics':'合成研究说明见引文。'}[key])
            if check['item'] in ('task_instructions','dataset'):check['status']='partially_reported'
    a['unresolved_questions']=[{'question':'Why was Mann–Whitney U chosen?','status':'not_reported','trigger':claim('test','文章报告使用双侧 Mann–Whitney U 检验。','The paper names a two-sided Mann-Whitney U test.'),'missing_information':blank()}, {'question':'Was an effect size reported?','status':'not_reported','trigger':claim('result','文章提供中位数、U 与 p 值。','The paper supplies medians, U and p values.'),'missing_information':blank()}]
    write_json(out/'paper_analysis.json',a)
    return out

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',default=str(Path(__file__).resolve().parents[1]/'examples/demo'));args=p.parse_args()
    print('Synthetic demo:',demo(args.out))
