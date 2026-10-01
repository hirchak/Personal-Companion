// SYNTHETIC secrets/notes only, disposable fake IndexedDB with native Node WebCrypto.
import 'fake-indexeddb/auto';
import {afterEach,beforeEach,describe,it,expect} from 'vitest';
import {PhoneStore,openPhoneDB} from '../src/phone-store';
import {validatePayload} from '../src/phone-validation';
const PASSPHRASE='SYNTHETIC passphrase for controlled fixture only';
const NOTE='SYNTHETIC · paper orchard 🦉 <script>inert</script>';
const stores:PhoneStore[]=[];
const dbName='personal-companion-synthetic-phone';
const local=()=>{const store=new PhoneStore();stores.push(store);return store;};
async function clear(){await new Promise<void>(resolve=>{const r=indexedDB.deleteDatabase(dbName);r.onsuccess=()=>resolve();r.onblocked=()=>{throw new Error('test leaked a database handle');};});}
async function persisted(){const db=await openPhoneDB();try{return await new Promise<any[]>(resolve=>{const r=db.transaction('vault').objectStore('vault').getAll();r.onsuccess=()=>resolve(r.result);});}finally{db.close();}}
beforeEach(async()=>{await clear();});
afterEach(async()=>{for(const store of stores)store.lock();stores.length=0;await clear();});
describe('M2 synthetic encrypted outbox',()=>{
 it('atomic local create/edit/delete and reload with actual crypto',async()=>{const a=local();await a.create(PASSPHRASE);const id=crypto.randomUUID();await a.capture('create',id,{raw_text:NOTE,type:'daily',mood_rating:0,energy_rating:null});await a.capture('edit',id,{raw_text:NOTE+' edited',type:'daily',mood_rating:0});let data=await a.state();expect(data.outbox.map(o=>o.base_revision)).toEqual([0,1]);expect(data.records[id].payload.raw_text).toBe(NOTE+' edited');a.lock();const b=local();await expect(b.unlock('SYNTHETIC wrong password')).rejects.toThrow('UNLOCK_OR_INTEGRITY_FAILED');data=await b.unlock(PASSPHRASE);expect(data.outbox).toHaveLength(2);await b.capture('delete',id,null);expect((await b.state()).records[id].deleted).toBe(true);expect((await b.state()).outbox[2].base_revision).toBe(2);});
 it('persisted records and recovery have no plaintext note/password/credential; IVs differ',async()=>{const a=local();await a.create(PASSPHRASE);const id=crypto.randomUUID();await a.capture('create',id,{raw_text:NOTE});await a.mutate(s=>{s.pairing={credential:'SYNTHETIC credential hidden in encrypted state',epoch:'SYNTHETIC:0'};});let rows=await persisted();let text=JSON.stringify(rows);expect(text).not.toContain(NOTE);expect(text).not.toContain(PASSPHRASE);expect(text).not.toContain('SYNTHETIC credential');const first=rows.find(r=>r.ciphertext).iv;await a.capture('edit',id,{raw_text:NOTE+' second'});rows=await persisted();expect(rows.find(r=>r.ciphertext).iv).not.toBe(first);const pkg=await a.recovery();text=JSON.stringify(pkg);expect(text).not.toContain(NOTE);expect(text).not.toContain('SYNTHETIC credential');expect(pkg.checksum).toBeTruthy();a.lock();await expect(a.state()).rejects.toThrow('LOCKED');});
 it('quota/write failure has no local receipt or partial entry/outbox',async()=>{const a=local();await a.create(PASSPHRASE);const original=IDBObjectStore.prototype.put;IDBObjectStore.prototype.put=function(){throw new DOMException('SYNTHETIC quota','QuotaExceededError');};try{await expect(a.capture('create',crypto.randomUUID(),{raw_text:NOTE})).rejects.toThrow();}finally{IDBObjectStore.prototype.put=original;}expect(Object.keys((await a.state()).records)).toHaveLength(0);expect((await a.state()).outbox).toHaveLength(0);});
 it('two store instances use revision CAS, never silent lost update',async()=>{const a=local();await a.create(PASSPHRASE);const b=local();await b.unlock(PASSPHRASE);const results=await Promise.allSettled([a.capture('create',crypto.randomUUID(),{raw_text:NOTE}),b.capture('create',crypto.randomUUID(),{raw_text:NOTE+' B'})]);expect(results.some(r=>r.status==='fulfilled')).toBe(true);const final=await a.state();expect(final.outbox.length).toBe(results.filter(r=>r.status==='fulfilled').length);});
 it('encrypted recovery restores only into empty store and requires reconciliation',async()=>{const a=local();await a.create(PASSPHRASE);await a.capture('create',crypto.randomUUID(),{raw_text:NOTE});const pkg=await a.recovery();await expect(a.restoreRecovery(pkg,PASSPHRASE)).rejects.toThrow('RECOVERY_TARGET_NOT_EMPTY');await a.forget();const b=local();await expect(b.restoreRecovery({...pkg,checksum:'corrupted'},PASSPHRASE)).rejects.toThrow('RECOVERY_CHECKSUM');const recovered=await b.restoreRecovery(pkg,PASSPHRASE);expect(recovered.repair).toBe(true);expect(recovered.pairing).toBe(null);expect(Object.values(recovered.records)[0].payload.raw_text).toBe(NOTE);await expect(b.sync()).rejects.toThrow('REPAIR_REQUIRED');});
 it('unsupported future physical schema refuses without wiping existing encrypted records',async()=>{const a=local();await a.create(PASSPHRASE);await a.capture('create',crypto.randomUUID(),{raw_text:NOTE});a.lock();const db=await new Promise<IDBDatabase>(resolve=>{const r=indexedDB.open(dbName,4);r.onsuccess=()=>resolve(r.result);});const count=await new Promise<number>(resolve=>{const r=db.transaction('vault').objectStore('vault').count();r.onsuccess=()=>resolve(r.result);});db.close();await expect(local().unlock(PASSPHRASE)).rejects.toThrow('UNSUPPORTED_STORAGE_SCHEMA');const current=await new Promise<IDBDatabase>(resolve=>{const r=indexedDB.open(dbName);r.onsuccess=()=>resolve(r.result);});const actual=await new Promise<number>(resolve=>{const r=current.transaction('vault').objectStore('vault').count();r.onsuccess=()=>resolve(r.result);});expect(actual).toBe(count);current.close();});
 it('shared input schema/semantic constraints preserve zero/null, DST and exact text',()=>{expect(validatePayload({raw_text:NOTE,type:'daily',mood_rating:0,energy_rating:null})).toBeTruthy();expect(()=>validatePayload({raw_text:'   '})).toThrow();expect(()=>validatePayload({raw_text:NOTE,type:'inbox',mood_rating:null})).toThrow();expect(()=>validatePayload({raw_text:NOTE,type:'daily',mood_rating:NaN})).toThrow();expect(()=>validatePayload({raw_text:NOTE,timezone:'not/a-zone'})).toThrow();expect(validatePayload({raw_text:NOTE,type:'sleep',sleep_start_utc:'2026-10-25T02:30:00+02:00',wake_at_utc:'2026-10-25T02:30:00+01:00',occurred_at_utc:'2026-10-25T02:30:00+01:00',time_precision:'instant',local_date:'2026-10-25',timezone:'Europe/Warsaw'})).toBeTruthy();});
});

it('M2-A08 encrypted schema migration requires confirmation and keeps outbox',async()=>{
 const a=local();await a.create(PASSPHRASE);const id=crypto.randomUUID();await a.capture('create',id,{raw_text:NOTE});const original=await a.state();const rows=await persisted();const config={...rows.find(x=>x.salt),storage_schema:1};
 const enc=new TextEncoder(),bytes=(s:string)=>Uint8Array.from(atob(s),c=>c.charCodeAt(0)),b64=(a:Uint8Array)=>btoa(Array.from(a,b=>String.fromCharCode(b)).join(''));
 const material=await crypto.subtle.importKey('raw',enc.encode(PASSPHRASE),'PBKDF2',false,['deriveKey']);const key=await crypto.subtle.deriveKey({name:'PBKDF2',hash:'SHA-256',salt:bytes(config.salt),iterations:600000},material,{name:'AES-GCM',length:256},false,['encrypt']);const iv=crypto.getRandomValues(new Uint8Array(12));const ciphertext=await crypto.subtle.encrypt({name:'AES-GCM',iv,additionalData:enc.encode(`pc-phone:SYNTHETIC:${config.device_id}:1:${config.salt}:600000:1`)},key,enc.encode(JSON.stringify({...original,format:1})));
 await a.forget();const db=await new Promise<IDBDatabase>(resolve=>{const r=indexedDB.open(dbName,1);r.onupgradeneeded=()=>r.result.createObjectStore('vault');r.onsuccess=()=>resolve(r.result);});await new Promise<void>(resolve=>{const tx=db.transaction('vault','readwrite');tx.objectStore('vault').put(config,'config');tx.objectStore('vault').put({format:1,storage_schema:1,revision:1,iv:b64(iv),ciphertext:b64(new Uint8Array(ciphertext))},'state');tx.oncomplete=()=>resolve();});db.close();
 const b=local();await expect(b.unlock(PASSPHRASE)).rejects.toThrow('LOCAL_MIGRATION_CONFIRMATION_REQUIRED');expect((await persisted()).find(x=>x.salt).storage_schema).toBe(1);
 const migrated=await b.unlock(PASSPHRASE,true);expect(migrated.format).toBe(2);expect(migrated.outbox).toEqual(original.outbox);expect(migrated.records[id].payload.raw_text).toBe(NOTE);expect((await persisted()).find(x=>x.salt).storage_schema).toBe(2);
});

it('M2-A09 DB open failure is surfaced without creating a saved record',async()=>{
 const original=indexedDB.open.bind(indexedDB);Object.defineProperty(indexedDB,'open',{configurable:true,value:()=>{throw new DOMException('SYNTHETIC open failure','UnknownError');}});
 try{await expect(local().create(PASSPHRASE)).rejects.toThrow();}finally{Object.defineProperty(indexedDB,'open',{configurable:true,value:original});}
 expect(await local().exists()).toBe(false);
});

it('M2-A09 logical migration failure rolls back encrypted state and config',async()=>{
 const a=local();await a.create(PASSPHRASE);const original=await a.state(),rows=await persisted();const config={...rows.find(x=>x.salt),storage_schema:1};const enc=new TextEncoder(),bytes=(s:string)=>Uint8Array.from(atob(s),c=>c.charCodeAt(0)),b64=(b:Uint8Array)=>btoa(Array.from(b,x=>String.fromCharCode(x)).join(''));const material=await crypto.subtle.importKey('raw',enc.encode(PASSPHRASE),'PBKDF2',false,['deriveKey']);const key=await crypto.subtle.deriveKey({name:'PBKDF2',hash:'SHA-256',salt:bytes(config.salt),iterations:600000},material,{name:'AES-GCM',length:256},false,['encrypt']);const iv=crypto.getRandomValues(new Uint8Array(12)),ciphertext=await crypto.subtle.encrypt({name:'AES-GCM',iv,additionalData:enc.encode(`pc-phone:SYNTHETIC:${config.device_id}:1:${config.salt}:600000:1`)},key,enc.encode(JSON.stringify({...original,format:1})));a.lock();const db=await openPhoneDB();await new Promise<void>(resolve=>{const tx=db.transaction('vault','readwrite');tx.objectStore('vault').put(config,'config');tx.objectStore('vault').put({format:1,storage_schema:1,revision:1,iv:b64(iv),ciphertext:b64(new Uint8Array(ciphertext))},'state');tx.oncomplete=()=>resolve();});db.close();
 const b=local();const put=IDBObjectStore.prototype.put;IDBObjectStore.prototype.put=function(){throw new DOMException('SYNTHETIC migration failure','QuotaExceededError');};try{await expect(b.unlock(PASSPHRASE,true)).rejects.toThrow();}finally{IDBObjectStore.prototype.put=put;}expect((await persisted()).find(x=>x.salt).storage_schema).toBe(1);expect((await persisted()).find(x=>x.ciphertext).storage_schema).toBe(1);expect((await b.unlock(PASSPHRASE,true)).format).toBe(2);
});

it('M2-A03 choosing Mac or phone is a new mutation from current revision, never local fake confirmation',async()=>{
 for(const choice of ['mac','phone'] as const){await clear();const a=local();await a.create(PASSPHRASE);const id=crypto.randomUUID();await a.capture('create',id,{raw_text:NOTE});await a.mutate(s=>{s.records[id].state='CONFLICT';s.records[id].current={id,revision:4,raw_text:'SYNTHETIC current Mac',type:'inbox',tags:[],timezone:'Europe/Warsaw',occurred_at_utc:null,local_date:null,time_precision:'unknown'};s.outbox[0].state='CONFLICT';});const old=(await a.state()).outbox[0].operation_id;const resolved=await a.resolve(id,choice);expect(resolved.outbox).toHaveLength(1);expect(resolved.outbox[0].operation_id).not.toBe(old);expect(resolved.outbox[0].base_revision).toBe(4);expect(resolved.records[id].state).toBe('QUEUED');expect(resolved.outbox[0].payload?.raw_text).toBe(choice==='mac'?'SYNTHETIC current Mac':NOTE);a.lock();}
});

it('M2-N01 successful server prepare + encrypted write failure never finalizes; fresh invite retry does',async()=>{
 const a=local();await a.create(PASSPHRASE);
 const originalFetch=globalThis.fetch,originalPut=IDBObjectStore.prototype.put;
 let pending=true,active=false,finalizations=0,prepares=0;
 globalThis.fetch=async(input,init)=>{
  if(String(input).endsWith('/pair')){
   prepares++;pending=true;active=false;
   return new Response(JSON.stringify({device_id:(await a.state()).device_id,credential:'SYNTHETIC controlled credential '+prepares,epoch:'SYNTHETIC:0',state:'PENDING'}),{status:200});
  }
  if(String(input).endsWith('/finalize')){finalizations++;pending=false;active=true;return new Response(JSON.stringify({state:'ACTIVE'}),{status:200});}
  throw new Error('unexpected fixture route');
 };
 IDBObjectStore.prototype.put=function(){throw new DOMException('SYNTHETIC pairing persistence failure','QuotaExceededError');};
 try{await expect(a.pair('SYNTHETIC invite 1','SYNTHETIC phone')).rejects.toThrow();}
 finally{IDBObjectStore.prototype.put=originalPut;}
 expect(pending).toBe(true);expect(active).toBe(false);expect(finalizations).toBe(0);expect((await a.state()).pairing).toBe(null);
 try{await a.pair('SYNTHETIC fresh owner invite','SYNTHETIC phone');expect(active).toBe(true);expect(finalizations).toBe(1);expect((await a.state()).pairing?.credential).toContain('2');expect(JSON.stringify(await persisted())).not.toContain('SYNTHETIC controlled credential');}
 finally{globalThis.fetch=originalFetch;}
});

it('M2-N01 encrypted credential survives lost confirmation response; foreground sync repeats confirmation',async()=>{
 const a=local();await a.create(PASSPHRASE);const originalFetch=globalThis.fetch;
 let confirmations=0;
 globalThis.fetch=async(input)=>{
  if(String(input).endsWith('/pair'))return new Response(JSON.stringify({device_id:(await a.state()).device_id,credential:'SYNTHETIC retryable credential',epoch:'SYNTHETIC:0',state:'PENDING'}),{status:200});
  if(String(input).endsWith('/finalize')){confirmations++;if(confirmations===1)throw new TypeError('SYNTHETIC lost response');return new Response(JSON.stringify({state:'ACTIVE'}),{status:200});}
  if(String(input).endsWith('/snapshot'))return new Response(JSON.stringify({epoch:'SYNTHETIC:0',checkpoint:0,entries:[],tombstones:[],schema_version:2}),{status:200});
  throw new Error('unexpected fixture route');
 };
 try{await expect(a.pair('SYNTHETIC invite','SYNTHETIC phone')).rejects.toThrow();a.lock();const b=local();await b.unlock(PASSPHRASE);expect((await b.state()).pairing).not.toBe(null);await b.sync();expect(confirmations).toBe(2);}
 finally{globalThis.fetch=originalFetch;}
});
