"""Bounded original-synthetic private-contract quality evaluation, no packaging/pilot.

Offline rehearsal is explicitly a scripted fixture, never quality/LIVE evidence.
Live mode requires fresh supported SDK funding/auth/catalog proof and the single Q01 ledger.
"""
import argparse
import ast
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
from uuid import UUID, uuid5

from apps.core import local_private as protection
from apps.core.storage import REPO, Store, SafeError, digest, encode, now
from apps.core.root_types import RootKind
from apps.core.conversation import Conversations
from apps.core.conversation_contracts import Message, NewConversation, SendMessage
from apps.core.conversation_controller import ConversationController
from apps.core.conversation_skills import NEUTRAL
from apps.core.local_private_ai import PrivatePilotGate
from apps.core.local_private_contracts import DurableConsentAcceptance, PrivateContextPreview, PrivateInferenceStart
from apps.core.local_private_provider import PrivateCodexConversationProvider
from apps.core.reflection_contracts import GoalCreate
from apps.core.deep_session_contracts import SessionAction, MapItem
from scripts.m8e_q01_budget import EvaluationLedger, NativeAttemptLease, PROFILES, ROOT
from scripts.m8e_q01_preflight import preflight, SAFE_CODES

NAMESPACE=UUID('81000000-0000-4000-8000-000000000001')
SESSION='ORIGINAL_SYNTHETIC_Q01_SESSION'
SENTINEL='ORIGINAL_SYNTHETIC_UNSELECTED_CONTEXT_SENTINEL'


def identifier(value):return uuid5(NAMESPACE,value)


def verify_baseline_generation():
    """Original generation inputs; current bounded register validator is disclosed.

    Do not pretend the full runtime equals the old baseline after a validator fix.
    Prove that the only controller difference is the register validator; all other
    frozen runtime/input sources must still match before baseline-content calls.
    """
    baseline=json.loads((ROOT/'baseline_manifest.json').read_text())
    controller_path='apps/core/conversation_controller.py'
    for name,expected in baseline['files'].items():
        current=(REPO/name).read_bytes()
        if digest(current)==expected:continue
        if name!=controller_path:raise SafeError('Q01_BASELINE_GENERATION_CHANGED',409)
        original=subprocess.check_output(['git','show',baseline['base_sha']+':'+name],cwd=REPO)
        if digest(original)!=expected:raise SafeError('Q01_BASELINE_GENERATION_CHANGED',409)
        def generation_tree(source):
            tree=ast.parse(source)
            tree.body=[node for node in tree.body if not isinstance(node,ast.FunctionDef) or node.name!='verify_address_form']
            return ast.dump(tree,include_attributes=False)
        if generation_tree(original)!=generation_tree(current):raise SafeError('Q01_BASELINE_GENERATION_CHANGED',409)
    return 'BASELINE_GENERATION_WITH_CURRENT_REGISTER_VALIDATION'


def require_fresh_proof(proof):
    if not isinstance(proof,dict) or proof.get('status')!='PASS' or proof.get('verification_source')!='EXISTING_SDK_METADATA':
        raise SafeError('Q01_NATIVE_METADATA_PROOF_REQUIRED',403)
    age=time.monotonic()-proof.get('observed_at_monotonic',0)
    if not 0<=age<=60:raise SafeError('Q01_METADATA_PROOF_STALE',409)
    for name,(_,model,effort) in PROFILES.items():
        if proof.get('profiles',{}).get(name)!={'model':model,'effort':effort,'verified':True}:
            raise SafeError('Q01_PROFILE_DENIED',403)
        funding=proof.get('funding',{}).get(name,{})
        if not all(funding.get(key) is True for key in ('included_usage_allowed','available_credits_absent','included_plan_verified')):
            raise SafeError('Q01_INCLUDED_USAGE_UNVERIFIED',403)


class EvaluationProvider:
    def __init__(self,model,effort,slot,case,ledger,proof,offline):
        self.model,self.effort=model,effort
        self.profile=model+':'+effort
        self.slot,self.case,self.ledger,self.proof,self.offline=slot,case,ledger,proof,offline
        self.payload=None;self.raw_result=None;self.outer_attempt=None

    def metadata(self):
        return {'route':'CODEX_SUBSCRIPTION','model':self.model,'effort':self.effort,
                'profile':self.profile,'live':not self.offline,'fallback':False,'payg':False}

    def readiness(self):
        if not self.offline:require_fresh_proof(self.proof)
        return {'account_type':'chatgpt','models':{'gpt-6-luna':['high','max'],'gpt-6.1-sol':['high']},
                'thread_started':False,'inference_started':False,'fallback':False,'payg':False}

    def execute(self,payload,schema,cancel,deadline,on_delta=None):
        mode,model,effort=PROFILES[self.slot['profile_id']]
        if (payload['mode'],self.model,self.effort)!=(mode,model,effort):raise SafeError('Q01_PROFILE_DENIED',403)
        turns=[part for part in payload['context'] if part['kind']=='CURRENT_TURN' and part['source_refs']==[payload['current_message_ref']]]
        if len(turns)!=1 or turns[0]['text']!=self.case['turns'][-1]:raise SafeError('Q01_SYNTHETIC_INPUT_MISMATCH',403)
        if payload['synthetic'] is not False or payload['tool_permissions'] or any(s['skill_id'] not in NEUTRAL for s in payload['skills']):
            raise SafeError('Q01_SCOPE_DENIED',403)
        if any(p['kind']=='JOURNAL_SELECTED' for p in payload['context']) or SENTINEL in encode(payload) or 'audio_hash' in encode(payload):
            raise SafeError('Q01_SCOPE_DENIED',403)
        self.payload=json.loads(encode(payload))
        if self.offline:
            candidate={'assistant_text':'ORIGINAL SYNTHETIC · Це лише технічна fixture-відповідь, не результат моделі.',
                       'source_refs':[payload['current_message_ref']],'goal_suggestion':None,
                       'closure':{'discussed':[],'clearer':'','unresolved':'','possible_steps':[]} if payload['purpose']=='CLOSURE' else None,
                       'topics':['self_reflection'],'working_map':None}
            self.raw_result={**self.metadata(),'text':encode(candidate),'profile_verified':True}
            return self.raw_result
        require_fresh_proof(self.proof)
        self.ledger.require_live()
        self.outer_attempt=self.ledger.begin(self.slot['slot_id'],digest(encode(payload).encode()))
        native=PrivateCodexConversationProvider(model=self.model,effort=self.effort,
                   budget=NativeAttemptLease(self.ledger,self.outer_attempt))
        self.raw_result=native.execute(payload,schema,cancel,deadline,on_delta)
        return self.raw_result


def scripted_history(controller,conversation_id,case_id,history):
    sources=[]
    for index,turn in enumerate(history):
        page=controller.conversations.get(conversation_id)
        if turn['role']=='USER':
            page=controller.conversations.send(conversation_id,SendMessage(operation_id=identifier(case_id+':seed:'+str(index)),
                         base_revision=page['conversation']['revision'],text=turn['text']),respond=False)
            sources.append(page['messages'][-1])
        else:
            # Explicitly scripted synthetic history, not a claimed provider call.
            # The PRIVATE_LOCAL wire/storage contract remains unchanged; provenance
            # for this fixture construction is carried in the experiment record.
            with controller.store.transaction() as connection:
                conversation=controller.conversations.row(connection,conversation_id)
                sequence=connection.execute('SELECT COALESCE(MAX(sequence),0)+1 FROM conversation_messages WHERE conversation_id=?',(conversation_id,)).fetchone()[0]
                message=Message(schema_version=1,id=identifier(case_id+':assistant-seed:'+str(index)),conversation_id=conversation.id,
                    role='ASSISTANT',raw_text=turn['text'],created_utc=now(),revision=1,provenance='MODEL_GENERATED',
                    source_reference=None,source_message_id=None,inference_reference=None,synthetic=False,privacy_class='PRIVATE_PERSONAL')
                value=message.model_dump(mode='json')
                connection.execute('INSERT INTO conversation_messages VALUES(?,?,?,?)',(value['id'],conversation_id,sequence,encode(value)))
                conversation.revision+=1;conversation.updated_utc=now()
                connection.execute('UPDATE conversations SET revision=?,payload=?,updated=? WHERE id=?',
                    (conversation.revision,encode(conversation.model_dump(mode='json')),conversation.updated_utc,conversation_id))
                sources.append(value)
    return sources


def downstream(store):
    with store.connect() as connection:
        result={}
        for table in ('entries','memories','health_records','practice_sessions','reflection_goals'):
            rows=[list(row) for row in connection.execute('SELECT * FROM '+table+' ORDER BY rowid')]
            result[table]={'rows':len(rows),'content_sha256':digest(encode(rows).encode())}
        return result


def run_case(slot,case,seed,*,ledger=None,proof=None,offline=True):
    work=Path(tempfile.mkdtemp(prefix='m8e-q01-original-synthetic-case-',dir=Path(tempfile.gettempdir()).resolve()))
    os.chmod(work,0o700)
    gate=None;providers=[]
    try:
        data=work/'ORIGINAL_SYNTHETIC_PRIVATE_CONTRACT';backups=work/'ORIGINAL_SYNTHETIC_BACKUP_CONTAINER'
        backups.mkdir(mode=0o700)
        # Direct disposable Store fixture, not a Mac package, installation or owner vault.
        receipt=protection.activation_receipt(data,digest(b'ORIGINAL_SYNTHETIC_Q01_FIXTURE_NOT_A_RELEASE'),backups,
            'INITIALIZE_PRIVATE_LOCAL:'+str(data),protection.CONSENT,True)
        store=Store(data,root_kind=RootKind.PRIVATE_LOCAL,private_creation=receipt)
        def factory(mode,model,effort):
            provider=EvaluationProvider(model,effort,slot,case,ledger,proof,offline);providers.append(provider);return provider
        gate=PrivatePilotGate(store,provider_factory=factory)
        controller=ConversationController(Conversations(store,False,mock_responses=False),private_gate=gate,timeout=120)
        gate.revocation_hooks.append(controller.revoke_private);gate.profile_change_hooks.append(controller.revoke_private)
        contract=gate.consent.contract()
        gate.accept_consent(SESSION,DurableConsentAcceptance(version=contract['version'],privacy_version=contract['privacy_version'],accepted=True))
        mode,_,_=PROFILES[slot['profile_id']]
        if mode=='DEEP':gate.select_deep(SESSION,'DEEP_ECONOMICAL' if slot['profile_id']=='DEEP_LUNA_MAX' else 'DEEP_QUALITY')
        from apps.core.domain import Journal
        from apps.core.models import Create
        unselected_text=SENTINEL+' '+seed['goal']+' '+case['turns'][-1]
        Journal(store).write('create',identifier(case['id']+':unselected-journal'),Create(operation_id=identifier(case['id']+':journal-op'),
            entry_id=identifier(case['id']+':unselected-journal'),base_revision=0,payload={'raw_text':unselected_text}))
        unrelated=controller.conversations.create(NewConversation(operation_id=identifier(case['id']+':unrelated')))
        controller.conversations.send(unrelated['conversation']['id'],SendMessage(operation_id=identifier(case['id']+':unrelated-message'),base_revision=1,text=unselected_text),respond=False)
        goal=controller.context.create(GoalCreate(operation_id=identifier(case['id']+':goal'),text=seed['goal'],user_agreed=True)) if mode=='DEEP' else None
        page=controller.conversations.create(NewConversation(operation_id=identifier(case['id']+':conversation'),goal_id=goal['id'] if goal else None,goal_revision=1 if goal else None))
        conversation_id=page['conversation']['id']
        sources=scripted_history(controller,conversation_id,case['id'],seed['history'])
        if mode=='DEEP':
            session=controller.deep.read(conversation_id)['session']
            controller.deep.session_action(conversation_id,SessionAction(operation_id=identifier(case['id']+':focus'),base_revision=session['revision'],action='focus',focus=seed['focus']))
            if seed['rejected']:
                source=next(item for item in sources if item['role']=='ASSISTANT')
                with store.transaction() as connection:
                    session=controller.deep.session(connection,conversation_id)
                    items=[MapItem(id=identifier(case['id']+':rejected:'+str(i)),kind='HYPOTHESIS',text=text,
                        provenance='MODEL_HYPOTHESIS',state='REJECTED',sources=[{'id':source['id'],'revision':1}]).model_dump(mode='json')
                        for i,text in enumerate(seed['rejected'])]
                    controller.deep.write(connection,session,items,{'provider_model':'ORIGINAL_SCRIPTED_SYNTHETIC_NOT_LIVE',
                        'provider_route':'OFFLINE_FIXTURE','selected_skills':[],'request_hash':'a'*64})
        before_counts=downstream(store)
        page=controller.conversations.get(conversation_id)
        preview=controller.private_preview(conversation_id,PrivateContextPreview(operation_id=identifier(case['id']+':preview'),
            base_revision=page['conversation']['revision'],text=case['turns'][-1],purpose=case['purpose']))
        queued=controller.send(conversation_id,PrivateInferenceStart(operation_id=identifier(case['id']+':send'),
            base_revision=page['conversation']['revision'],text=case['turns'][-1],purpose=case['purpose'],owner_approved_external_text=True,
            context_binding={key:preview[key] for key in ('receipt_id','context_hash','preview_hash')}),launch=False)
        job=queued['inference_job']['id'];started=time.monotonic();controller.run(job)
        outcome=controller.get(conversation_id,job)
        provider=next((item for item in providers if item.payload is not None),None)
        if provider and provider.outer_attempt:
            ledger.finish(provider.outer_attempt,'COMPLETED' if outcome['state']=='COMPLETED' else 'CANCELLED' if outcome['state']=='CANCELLED' else 'FAILED',outcome['error'])
        payload=provider.payload if provider else None
        comparable={key:payload.get(key) for key in ('mode','purpose','language','address_form','context','current_message_ref','source_refs_allowed','goal_revision','reflection_state')} if payload else None
        result={'slot_id':slot['slot_id'],'phase':slot['phase'],'case_id':case['id'],'profile_id':slot['profile_id'],
            'profile':PROFILES[slot['profile_id']],'origin':'OFFLINE_SCRIPTED_FIXTURE_NOT_MODEL_QUALITY' if offline else 'LIVE_ORIGINAL_SYNTHETIC',
            'state':outcome['state'],'error':outcome['error'],'assistant_candidate':outcome['candidate'],
            'raw_final_candidate':provider.raw_result.get('text') if provider and provider.raw_result else None,
            'provider_metadata':{key:provider.raw_result[key] for key in ('model','effort','profile','usage','elapsed_ms','frame_hash','auth_type','streaming_actual') if key in provider.raw_result} if provider and provider.raw_result else None,
            'evaluation_attempt_id':provider.outer_attempt if provider else None,'payload':payload,
            'payload_sha256':digest(encode(payload).encode()) if payload else None,
            'comparison_context_sha256':digest(encode(comparable).encode()) if comparable else None,
            'no_downstream_writes':downstream(store)==before_counts,'clinical_active':0,'real_private_data_used':False,
            'owner_pilot_accessed':False,'scripted_history_is_not_prior_live_output':True,
            'quality_assessment':'NOT_EVALUATED','wall_ms':round((time.monotonic()-started)*1000,3)}
        result['generation_validation_scope']='BASELINE_GENERATION_WITH_CURRENT_REGISTER_VALIDATION'
        if not result['no_downstream_writes']:raise SafeError('Q01_DOWNSTREAM_WRITE_DETECTED',409)
        return result
    finally:
        if gate:gate.disable()
        shutil.rmtree(work)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase',choices=['BASELINE','CANDIDATE'],required=True)
    parser.add_argument('--offline-fixture',action='store_true')
    parser.add_argument('--live',action='store_true')
    parser.add_argument('--slot',action='append')
    args=parser.parse_args()
    if args.live==args.offline_fixture:raise SystemExit('Exactly one of --offline-fixture or --live is required')
    plan=json.loads((ROOT/'experiment_plan.json').read_text())
    cases={item['id']:item for item in json.loads((ROOT/'cases.json').read_text())['cases']}
    slots=[item for item in plan['slots'] if item['phase']==args.phase and (not args.slot or item['slot_id'] in args.slot)]
    if args.slot and set(args.slot)!={item['slot_id'] for item in slots}:raise SystemExit('UNKNOWN_OR_WRONG_PHASE_SLOT')
    if args.live:
        # Live work must stay in the canonical main checkout; exact-C test clones
        # may rehearse offline but cannot accidentally obtain a fresh live counter.
        branch=subprocess.check_output(['git','symbolic-ref','--short','HEAD'],cwd=REPO,text=True).strip()
        if branch!='main':raise SystemExit('CANONICAL_MAIN_CHECKOUT_REQUIRED')
        if args.phase=='BASELINE':
            verify_baseline_generation()
        else:
            # This delivered correction changes validation, not model input.
            # The preregistered condition forbids spending a second arm as a
            # duplicate model benchmark when no generation change is justified.
            raise SystemExit('CANDIDATE_NOT_RUN_NO_MODEL_INPUT_CHANGE')
    output=REPO/'generated/m8e-q01'/('offline' if args.offline_fixture else 'live')
    output.mkdir(parents=True,exist_ok=True)
    ledger=EvaluationLedger() if args.live else None
    for slot in slots:
        target=output/(slot['slot_id']+'.json')
        if args.live and target.exists():raise SystemExit('NO_AUTOMATIC_RERUN_OF_RECORDED_SLOT')
        try:
            proof=preflight() if args.live else None
            row=run_case(slot,cases[slot['case_id']],plan['context_seeds'][slot['case_id']],ledger=ledger,proof=proof,offline=args.offline_fixture)
            target.write_text(json.dumps(row,ensure_ascii=False,indent=2)+'\n')
            print(json.dumps({'slot':slot['slot_id'],'origin':row['origin'],'state':row['state'],'error':row['error'],
                              'attempts':ledger.summary()['attempts'] if ledger else 0}),flush=True)
            if args.live and row['state']!='COMPLETED':raise SystemExit('LIVE_STOP_REVIEW_FAILED_CASE_NO_AUTOMATIC_RETRY')
        except SafeError as error:
            local_codes={'Q01_NATIVE_METADATA_PROOF_REQUIRED','Q01_METADATA_PROOF_STALE','Q01_PROFILE_DENIED',
                'Q01_SCOPE_DENIED','Q01_SYNTHETIC_INPUT_MISMATCH','Q01_DOWNSTREAM_WRITE_DETECTED',
                'Q01_TEST_LEDGER_CANNOT_AUTHORIZE_LIVE','Q01_CANONICAL_LEDGER_REQUIRED','Q01_FROZEN_INPUT_CHANGED',
                'Q01_LEDGER_SCOPE_CHANGED','Q01_SLOT_ALREADY_ATTEMPTED_NO_AUTOMATIC_RETRY','Q01_ATTEMPT_LIMIT'}
            code=error.code if error.code in SAFE_CODES|local_codes else 'Q01_EVALUATION_FAILED'
            print(json.dumps({'live_status':'BLOCKED','code':code,'attempts':ledger.summary()['attempts'] if ledger else 0}),flush=True)
            raise SystemExit(2)


if __name__=='__main__':main()
