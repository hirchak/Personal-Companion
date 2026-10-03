import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
const require = createRequire(new URL('../apps/web/package.json', import.meta.url));
const Ajv = require('ajv/dist/2020');
const ajv = new Ajv({strict:false, allErrors:true});
require('ajv-formats')(ajv);
const load = name => JSON.parse(readFileSync(new URL('../packages/contracts/conversation-runtime-'+name+'.json', import.meta.url), 'utf8'));
let checks=0;
function check(name,good,bad) {
  const validate=ajv.compile(load(name));
  if(!validate(good)) throw Error(JSON.stringify(validate.errors)); checks++;
  for(const value of bad){if(validate(value))throw Error('Unsafe structure admitted: '+name);checks++;}
}
const candidate={assistant_text:'ORIGINAL SYNTHETIC',source_refs:['s0'],goal_suggestion:null,closure:null,topics:['work']};
check('conversationcandidate',candidate,[{...candidate,tool:{shell:'inert'}},{...candidate,topics:['PTSD']},{...candidate,source_refs:['private-message-id']},{...candidate,assistant_text:''}]);
const start={operation_id:'70000000-0000-4000-8000-000000000001',base_revision:1,text:'ORIGINAL SYNTHETIC',purpose:'REFLECT',synthetic_test_ack:true};
check('inferencestart',start,[{...start,synthetic_test_ack:false},{...start,skills:['sleep_review']},{...start,purpose:'DIAGNOSE'}]);
const point={message_id:start.operation_id,source_revision:1,operation_id:start.operation_id,preview_hash:'a'.repeat(64),user_confirmed:true};
check('journalpointconfirm',point,[{...point,user_confirmed:false},{...point,raw_text:'model-injected text'}]);
console.log(JSON.stringify({status:'PASS',checks,oracle:'Independent Ajv 2020, no Python validator'}));
