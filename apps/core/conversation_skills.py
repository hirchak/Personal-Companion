"""One deterministic skill registry; clinical skills are metadata-only, never instructions."""
from pathlib import Path
import json
from .storage import REPO,SafeError,digest,encode
NEUTRAL=('core_reflection','deep_session','goal_setting','session_closure')
OFF=('cbt_reflection','worry_rumination','sleep_review','nightmare_review','grounding')

class ConversationSkills:
    def __init__(self,root=None):self.root=Path(root or REPO/'skills/conversation')
    def select(self,mode,purpose='REFLECT'):
        if mode not in {'FREE','DEEP'} or purpose not in {'REFLECT','GOAL_PROPOSAL','CLOSURE'}:raise SafeError('SKILL_SELECTION_DENIED',403)
        names=['core_reflection']
        if mode=='DEEP':names.append('deep_session')
        if purpose=='GOAL_PROPOSAL':names.append('goal_setting')
        if purpose=='CLOSURE':names.append('session_closure')
        return [self.read(name) for name in names]
    def read(self,name):
        if name not in NEUTRAL:raise SafeError('SKILL_OFF',403)
        try:
            data=json.loads((self.root/(name+'.json')).read_text())
            if data['skill_id']!=name or data['clinical'] is not False or data['provenance']!='ORIGINAL_PROJECT_AUTHORED':raise ValueError()
        except (ValueError,KeyError,OSError):raise SafeError('SKILL_INTEGRITY') from None
        return dict(data,content_hash=digest(encode(data).encode()))
    def binding(self,selected):return [{'skill_id':s['skill_id'],'version':s['version'],'content_hash':s['content_hash']} for s in selected]
    def verify(self,bindings):
        for b in bindings:
            current=self.read(b['skill_id'])
            if current['version']!=b['version'] or current['content_hash']!=b['content_hash']:raise SafeError('SKILL_CHANGED',409)
    def catalog(self):return {'neutral':[{'skill_id':s,'version':self.read(s)['version'],'status':'AVAILABLE_NEUTRAL_SYNTHETIC_ONLY','clinical':False} for s in NEUTRAL],'off':[{'skill_id':s,'status':'CONTRACT_ONLY_NOT_ACTIVE','clinical':True} for s in OFF]}
