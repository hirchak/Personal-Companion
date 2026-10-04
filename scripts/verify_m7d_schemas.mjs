import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
const require=createRequire(new URL('../apps/web/package.json',import.meta.url));
const Ajv=require('ajv/dist/2020');const ajv=new Ajv({strict:false,allErrors:true});require('ajv-formats')(ajv);
const uid='70000000-0000-4000-8000-000000000001';let checks=0;
function check(name,good,bad){const validate=ajv.compile(JSON.parse(readFileSync(new URL('../packages/contracts/deep-session-'+name+'.json',import.meta.url),'utf8')));if(!validate(good))throw Error(JSON.stringify(validate.errors));checks++;for(const v of bad){if(validate(v))throw Error('Unsafe admitted:'+name);checks++;}}
const item={kind:'HYPOTHESIS',text:'ORIGINAL SYNTHETIC assumption',provenance:'MODEL_HYPOTHESIS',source_refs:['s0']};
check('workingmapcandidate',{items:[item]},[{items:[{...item,provenance:'USER_CONFIRMED'}]},{items:[{...item,source_refs:['private-id']}]},{items:[item],diagnosis:'inert'}]);
const binding={receipt_id:uid,context_hash:'a'.repeat(64),preview_hash:'b'.repeat(64)};
check('contextbinding',binding,[{...binding,context_hash:'unsafe'},{...binding,skills:['sleep_review']}]);
const action={operation_id:uid,base_version:1,item_id:uid,action:'reject',user_confirmed:true};
check('mapaction',action,[{...action,user_confirmed:false},{...action,action:'activate'},{...action,diagnosis:'inert'}]);
check('contextselection',{type:'LAST_7_DAYS',timezone:'Europe/Warsaw'},[{type:'ALL_PRIVATE_VAULT'},{type:'LAST_7_DAYS',health:true}]);
console.log(JSON.stringify({status:'PASS',checks,oracle:'Independent Ajv2020 structural oracle; cross-field/source semantics tested in Python/controller'}));
