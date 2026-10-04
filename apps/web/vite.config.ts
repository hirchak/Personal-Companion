import { defineConfig } from "vite";
import { createHash } from "node:crypto";
import { readdirSync, readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { join } from "node:path";
export default defineConfig({
  define: { __PC_BUILD_ID__: JSON.stringify(process.env.PC_BUILD_COMMIT || "DEVELOPMENT") },
  plugins: [
    {
      name: "synthetic-pwa-shell",
      closeBundle() {
        const dir = "dist";
        const files = readdirSync(join(dir, "assets")).map(
          (f) => "/assets/" + f,
        );
        const index = readFileSync(join(dir, "index.html"), "utf8");
        mkdirSync(join(dir, "phone"), { recursive: true });
        writeFileSync(join(dir, "phone/index.html"), index);
        const version = createHash("sha256")
          .update(index + files.join())
          .digest("hex")
          .slice(0, 16);
        const precache = [
          "/phone/",
          "/manifest.webmanifest",
          "/icons/journal-192.png",
          "/icons/journal-512.png",
          ...files,
        ];
        const source = `const CACHE='pc-phone-shell-${version}';const FILES=${JSON.stringify(precache)};
self.addEventListener('install',event=>event.waitUntil((async()=>{const staged=await caches.open(CACHE);try{await staged.addAll(FILES)}catch(error){await caches.delete(CACHE);throw error}})()));
self.addEventListener('activate',event=>event.waitUntil((async()=>{await self.clients.claim();for(const name of await caches.keys())if(name.startsWith('pc-phone-shell-')&&name!==CACHE)await caches.delete(name)})()));
self.addEventListener('message',event=>{if(event.source&&event.source.url&&new URL(event.source.url).origin===self.location.origin&&event.data?.type==='ACTIVATE_WAITING')self.skipWaiting()});
self.addEventListener('fetch',event=>{const u=new URL(event.request.url);if(u.origin!==self.location.origin||event.request.method!=='GET'||u.pathname.startsWith('/api/'))return;if(!FILES.includes(u.pathname)&&event.request.mode!=='navigate')return;event.respondWith((async()=>{const cache=await caches.open(CACHE);const stored=await cache.match(event.request.mode==='navigate'?'/phone/':u.pathname);return stored||fetch(event.request)})())});`;
        writeFileSync(join(dir, "phone/sw.js"), source);
        writeFileSync(
          join(dir, "phone/shell-version.json"),
          JSON.stringify({ version, storage_schema: 2, synthetic: true }),
        );
      },
    },
  ],
});
