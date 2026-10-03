import {readFileSync} from 'node:fs';
import {createRequire} from 'node:module';
const require=createRequire(new URL('../apps/web/package.json',import.meta.url));
const Ajv=require('ajv/dist/2020');
const ajv=new Ajv({strict:false,allErrors:true});
const load=p=>JSON.parse(readFileSync(new URL('../'+p,import.meta.url),'utf8'));
const registry=load('research/admission/registry.json');
let checks=0;
function verify(schema,valid,invalid){const validate=ajv.compile(schema);if(!validate(valid))throw Error('Valid fixture failed '+JSON.stringify(validate.errors));checks++;for(const x of invalid){if(validate(x))throw Error('Unknown namespace admitted');checks++;}}
const source=registry.claims.find(x=>x.source_ids.length);
verify(load('research/admission/schemas/claim.schema.json'),source,[{...source,source_bindings:{...source.source_bindings,UNKNOWN:'a'.repeat(64)}}]);
const approval={module_id:'synthetic_candidate',version:'synthetic-1',content_hash:'a'.repeat(64),claim_bindings:{'claim:RG-01':'a'.repeat(64)},source_bindings:{'gate:S01':'a'.repeat(64)},reviewer:'Synthetic reviewer',reviewer_role:'CONTENT_REVIEWER',reviewed_on:'2026-10-03',scope:'synthetic',rights_hash:'a'.repeat(64),technical_sha:'b'.repeat(40)};
verify(load('research/admission/schemas/approval.schema.json'),approval,[{...approval,source_bindings:{UNKNOWN:'a'.repeat(64)}},{...approval,claim_bindings:{UNKNOWN:'a'.repeat(64)}}]);
verify(load('research/admission/schemas/registry.schema.json'),registry,[{...registry,claims:registry.claims.map((x,i)=>i===0?{...x,source_bindings:{UNKNOWN:'a'.repeat(64)}}:x)}]);
console.log(JSON.stringify({status:'PASS',standalone_checks:checks,oracle:'Ajv 2020 independent from Python validator'}));
