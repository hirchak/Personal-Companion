"""Persistent goal-wide request ceiling, independent of vault/process/retry/checkpoint."""
import sqlite3,time,threading
from pathlib import Path
from .storage import SafeError,REPO

class LiveEvaluationBudget:
    maximum=100
    goal='M7C_OWNER_2026_10_03'
    def __init__(self,path=None):
        self.path=Path(path or REPO/'generated/m7c-live-evaluation-ledger.sqlite3')
        self.path.parent.mkdir(parents=True,exist_ok=True)
        with self.connect() as c:c.execute('CREATE TABLE IF NOT EXISTS attempts(id TEXT PRIMARY KEY,goal TEXT NOT NULL,route TEXT NOT NULL,model TEXT NOT NULL,started REAL NOT NULL,outcome TEXT NOT NULL)')
    def connect(self):
        c=sqlite3.connect(self.path,timeout=10);c.row_factory=sqlite3.Row;return c
    def reserve(self,id,route,model):
        with self.connect() as c:
            c.execute('BEGIN IMMEDIATE')
            if c.execute('SELECT 1 FROM attempts WHERE id=?',(id,)).fetchone():raise SafeError('LIVE_ATTEMPT_REUSE',409)
            if c.execute('SELECT count(*) FROM attempts WHERE goal=?',(self.goal,)).fetchone()[0]>=self.maximum:raise SafeError('LIVE_EVAL_LIMIT',429)
            c.execute('INSERT INTO attempts VALUES(?,?,?,?,?,?)',(id,self.goal,route,model,time.time(),'STARTED'))
    def finish(self,id,outcome):
        if outcome not in {'COMPLETED','FAILED','CANCELLED'}:raise SafeError('LIVE_OUTCOME_INVALID')
        with self.connect() as c:c.execute('UPDATE attempts SET outcome=? WHERE id=?',(outcome,id))
    def summary(self):
        with self.connect() as c:
            rows=[dict(r) for r in c.execute('SELECT route,model,outcome,count(*) AS requests FROM attempts WHERE goal=? GROUP BY route,model,outcome',(self.goal,))]
        total=sum(r['requests'] for r in rows);return {'goal':self.goal,'maximum':self.maximum,'total_requests':total,'remaining':self.maximum-total,'routes':rows,'raw_payload_logged':False}
