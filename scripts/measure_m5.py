"""Bounded local synthetic M5 latency/DB overhead, no engagement/device/provider estimates."""
import argparse,json,statistics,tempfile,shutil,time
from pathlib import Path
from uuid import uuid4
from apps.core.storage import Store
from apps.core.domain import Journal
from apps.core.models import Create,Patch
from apps.core.creative import CreativeLibrary
from apps.core.feedback import Feedback,PersonalSpace
from apps.core.m5_contracts import CreativeSelection,CreativeDownload,FeedbackSave,FeedbackExact,FeedbackExport,SpaceUpdate

def run(n=300):
    if not 20<=n<=1000:raise ValueError('bounded N')
    parent=Path(tempfile.gettempdir()).resolve();temp=Path(tempfile.mkdtemp(prefix='m5-synthetic-metrics-',dir=parent))
    try:
        store=Store(temp/'data');j=Journal(store);lib=CreativeLibrary(j);f=Feedback(store);space=PersonalSpace(store)
        def size():
            with store.connect() as c:c.execute('PRAGMA wal_checkpoint(TRUNCATE)')
            return sum(p.stat().st_size for p in store.root.iterdir() if p.is_file())
        baseline=size();refs=[]
        for i in range(n):
            id=str(uuid4());j.write('create',id,Create(operation_id=uuid4(),entry_id=id,base_revision=0,payload={
                'type':'creative','raw_text':f'SYNTHETIC creative original {i} · paper scene','tags':['synthetic'],
                'creative_kind':'scene','creative_meta':{'title':f'SYNTHETIC idea {i}','collections':['Set '+str(i%5)]}}))
            if i<20:refs.append({'id':id,'revision':1})
        after_capture=size();metrics={}
        def measure(label,fn,runs=20):
            times=[]
            for _ in range(runs):
                start=time.perf_counter_ns();fn();times.append((time.perf_counter_ns()-start)/1e6)
            metrics[label]={'runs':runs,'median_ms':round(statistics.median(times),3),'min_ms':round(min(times),3),'max_ms':round(max(times),3)}
        measure('library_list_50',lambda:lib.list(limit=50))
        measure('literal_search',lambda:lib.list(q='original 2',limit=50))
        measure('collection_filter',lambda:lib.list(collection='Set 2',limit=50))
        target=[j.get(refs[-1]['id'])]
        def update_meta():
            e=target[0];j.write('edit',e['id'],Patch(operation_id=uuid4(),base_revision=e['revision'],changes={'creative_meta':{**e['creative_meta'],'title':'SYNTHETIC update '+str(e['revision'])}}));target[0]=j.get(e['id'])
        measure('metadata_update_commit_plus_receipt_read',update_meta)
        refs[-1]['revision']=target[0]['revision'];selection=CreativeSelection(entries=refs,fields=['raw_text','title','creative_kind','collections'])
        measure('creative_preview_20',lambda:lib.preview(selection,'synthetic'))
        p=lib.preview(selection,'synthetic');request=CreativeDownload(plan_id=p['plan_id'],content_hash=p['content_hash'],format='markdown')
        measure('creative_markdown_export_20',lambda:lib.export(request,'synthetic'))
        fs=f.save(FeedbackSave(draft_id=uuid4(),base_version=0,payload={'title':'SYNTHETIC feedback','description':'SYNTHETIC local measurement'}))
        exact=FeedbackExact(version=1,content_hash=fs['content_hash']);measure('feedback_hash_preview',lambda:f.list())
        measure('feedback_approval_commit',lambda:f.approve(fs['id'],exact))
        fe=FeedbackExport(version=1,content_hash=fs['content_hash']);measure('feedback_markdown_export',lambda:f.export(fs['id'],fe))
        measure('space_load',space.get);version=[0]
        def update_space():
            result=space.update(SpaceUpdate(base_version=version[0],state={'enabled':bool(version[0]%2),'theme':'sage'}));version[0]=result['version']
        measure('space_update_commit',update_space)
        return {'scope':'SYNTHETIC_LOCAL_ONLY','N':n,'metrics':metrics,'db_bytes':{'baseline':baseline,'after_capture':after_capture,'after_metadata_feedback_space':size(),'capture_growth':after_capture-baseline},'provider_metrics':'NOT_RUN','Galaxy_metrics':'NOT_RUN','engagement_KPIs':'NOT_COLLECTED','limitations':'Single local machine, bounded synthetic data, includes safe path checks and journal transaction overhead. Not a device/provider forecast.'}
    finally:shutil.rmtree(temp)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path);p.add_argument('--n',type=int,default=300);a=p.parse_args();result=run(a.n)
    if a.output:a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    else:print(json.dumps(result,ensure_ascii=False,indent=2))
