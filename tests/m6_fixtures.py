"""Original SYNTHETIC-only values; never derived from a real health record."""
from copy import deepcopy
from uuid import uuid4
from apps.core.health_contracts import HealthBatch

def record(kind='steps',id='SYNTHETIC-record-1',origin='synthetic.origin',**changes):
    fields={'steps':{'count':42,'unit':'count'},'sleep':{'stages':[],'stages_state':'MISSING'},'exercise':{'exercise_type':987654,'classification':'SOURCE_CODE'}}[kind]
    value={'type':kind,'source_id':id,'origin':origin,'status':'VALUE','modified':'2025-01-01T12:00:00Z','start':'2025-01-01T10:00:00Z','end':'2025-01-01T11:00:00Z','start_offset':None,'end_offset':None,'fields':fields}
    value.update(changes);return value

def batch(*records,sequence=1,epoch=None,permissions=None,mode='INITIAL_OR_RECOVERY'):
    return HealthBatch.model_validate({'schema_version':1,'source_system':'HEALTH_CONNECT','epoch':epoch or str(uuid4()),'sequence':sequence,'scopes':[{'type':kind,'permission':(permissions or {}).get(kind,'GRANTED'),'mode':mode,'records':[deepcopy(r) for r in records if r['type']==kind]} for kind in ('sleep','steps','exercise')]})
