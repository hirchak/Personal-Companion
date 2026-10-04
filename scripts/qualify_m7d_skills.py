"""Build/check exact OFF qualification metadata; never clinical content or runtime permission."""
import argparse,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
REG=ROOT/'research/admission/registry.json'
LINKS={'cbt_reflection':['thought_record'],'worry_rumination':['worry_rumination'],'sleep_review':['sleep_education','clinical_sleep_window','expanded_health_access'],'nightmare_review':['dream_irt'],'grounding':['grounding_relaxation']}
PURPOSE={'cbt_reflection':'Future reviewed fact/interpretation/automatic-thought reflection contract.','worry_rumination':'Future reviewed practical-problem versus repetitive-worry boundaries.','sleep_review':'Future subjective-versus-wearable sleep review; missing is not zero.','nightmare_review':'Future bounded user-reported dream discussion; no symbolic interpretation as fact.','grounding':'Future exact admitted low-risk practice recommendation, user-selected only.'}
EXCLUSIONS={'cbt_reflection':['forced_disputation','irrational_thought_label','diagnosis'],'worry_rumination':['reassurance_loop','unreviewed_worry_postponement'],'sleep_review':['autonomous_CBT_I','sleep_restriction_therapy','sleep_compression','personalized_sleep_window','diagnosis','health_connect_access'],'nightmare_review':['symbolic_interpretation_as_fact','PTSD_diagnosis','IRT_runtime_content','exposure','trauma_processing'],'grounding':['improvised_practice','unreviewed_dose','unadmitted_protocol_steps']}

def packages():
 registry=json.loads(REG.read_text());modules={m['id']:m for m in registry['modules']};result={}
 for skill,names in LINKS.items():
  # Registry module names are exact; absence fails rather than inventing admission.
  related=[modules[n] for n in names]
  fields=('id','version','research_packets','claim_ids','finding_ids','missing_gates','rights','evidence_status','content_status','required_reviewer_role','activation_status','exact_content_hash','qualified_clinical_review_record')
  dependencies=[{k:m[k] for k in fields} for m in related]
  result[skill]={'schema_version':1,'skill_id':skill,'version':'0.1.0-candidate','status':'CANDIDATE_METADATA_ONLY','activation_state':'OFF','runtime_instructions':None,'purpose':PURPOSE[skill],'intended_problem_class':skill,'registry_path':'research/admission/registry.json','registry_sha256':hashlib.sha256(REG.read_bytes()).hexdigest(),'admission_dependencies':dependencies,'research_packet_ids':sorted({x for m in related for x in m['research_packets']}),'claim_ids':sorted({x for m in related for x in m['claim_ids']}),'unresolved_finding_ids':sorted({x for m in related for x in m['finding_ids']}),'rights_status':'NOT_CLEARED_FOR_RUNTIME_CONTENT','evidence_status':'UNRESOLVED_CANONICAL_FINDINGS','qualified_content_review_required':True,'local_RAW_status':'MANIFEST_ONLY_NOT_LOCALLY_RECEIVED','allowed_future_behaviors':['EXACT_ACCOUNTABLE_REVIEWED_CONTENT_ONLY','USER_CAN_REJECT_PAUSE_STOP','SOURCE_BOUND_UNCERTAINTY','EXPLICIT_USER_RECOMMENDATION_PREVIEW'],'forbidden_behaviors':['clinical_activation','diagnosis','licensed_therapist_claim','private_data','health_to_AI','automatic_practice','automatic_memory',*EXCLUSIONS[skill]],'input_requirements':['exact_goal_revision','explicit_user_scope','source_revisions','exact_content_version_hash','accountable_evidence_content_rights_approval','separate_owner_activation_permission'],'stop_pause_requirements':['user_stop_immediate','missing_admission_fail_closed','stale_source_pause_review','unsupported_private_scope_deny'],'output_schema_proposal':{'type':'object','additionalProperties':False,'required':['candidate_text','source_refs','practice_reference'],'properties':{'candidate_text':{'type':'string','maxLength':1200},'source_refs':{'type':'array','maxItems':8,'items':{'type':'string'}},'practice_reference':{'type':['string','null'],'description':'Exact M7A admitted ID/version/hash; inert recommendation only'}}},'synthetic_eval_cases':[skill+'_OFF_DENIAL',skill+'_STALE_ADMISSION',skill+'_NO_HEALTH_ACCESS',skill+'_TEXT_CANNOT_EXECUTE_PRACTICE'],'practice_link':'candidate -> UI -> explicit user click -> M7A exact admission -> package; no model execution'}
 return result

def run(check=False):
 folder=ROOT/'skills/qualification';folder.mkdir(parents=True,exist_ok=True)
 for skill,p in packages().items():
  path=folder/(skill+'.json')
  if check:assert json.loads(path.read_text())==p,'CANONICAL_QUALIFICATION_DRIFT:'+skill
  else:path.write_text(json.dumps(p,ensure_ascii=False,indent=2)+'\n')
 print('5 CANDIDATE/OFF packages; canonical metadata exact; clinical active0')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');run(p.parse_args().check)
