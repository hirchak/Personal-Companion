#!/usr/bin/env python3
"""Offline exact-C native build from existing tools/assets. Never installs dependencies."""
import argparse
import importlib.metadata
import json
import os
from pathlib import Path
import plistlib
import shutil
import subprocess
import sys
import sysconfig

from apps.core import release
from apps.core.native_macos import PRODUCT, CHANNEL, bundle_files
from apps.core.storage import REPO, SafeError, digest, encode

SPARKLE_HASH = 'c2bf58aa8387266ac179357b1415d6f2635f044da8be41042af32425dae6da0c'
SPARKLE_DIR = REPO/'generated/m8f/dependencies/Sparkle-2.10.0'
PYTHON_ROOT = Path('/Library/Frameworks/Python.framework/Versions/3.13')
ASR = REPO/'generated/local-asr'


def run(*args, **kwargs):
    subprocess.run(list(map(str, args)), check=True, **kwargs)


def macho(path):
    if not path.is_file() or path.is_symlink(): return False
    with path.open('rb') as f: magic = f.read(4)
    return magic in {b'\xcf\xfa\xed\xfe',b'\xfe\xed\xfa\xcf',b'\xca\xfe\xba\xbe',b'\xbe\xba\xfe\xca'}


def bundled_runtime(framework):
    framework.mkdir(parents=True)
    # Framework Python's system installation is a build input, never a runtime path.
    run('/usr/bin/lipo', PYTHON_ROOT/'Python', '-thin','arm64','-output',framework/'Python')
    (framework/'bin').mkdir()
    run('/usr/bin/lipo',PYTHON_ROOT/'bin/python3.13','-thin','arm64','-output',framework/'bin/python3.13')
    stdlib = framework/'lib/python3.13'
    shutil.copytree(PYTHON_ROOT/'lib/python3.13',stdlib,
        ignore=shutil.ignore_patterns('site-packages','__pycache__','*.pyc','test','tests','idlelib','tkinter','_tkinter*','_test*','config-3.13-darwin','turtledemo','ensurepip'))
    site = stdlib/'site-packages'; site.mkdir()
    existing = Path(sysconfig.get_path('purelib')).resolve()
    inventory = []
    for line in (REPO/'requirements.runtime.lock').read_text().splitlines():
        name, version = line.split('=='); dist = importlib.metadata.distribution(name)
        if dist.version != version: raise SafeError('RUNTIME_PREREQUISITE_INCOMPATIBLE')
        for item in dist.files or []:
            source = Path(dist.locate_file(item)).resolve()
            if (not source.is_relative_to(existing) or not source.is_file() or source.suffix == '.pyc'
                    or '__pycache__' in source.parts or source.name in {'direct_url.json','RECORD'}): continue
            target = site/source.relative_to(existing); target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(source,target)
        inventory.append({'name':name,'version':version,'licence_files':[
            str(x) for x in dist.files or [] if 'license' in str(x).lower() or 'copying' in str(x).lower()]})
    # Copy CPython-bundled OpenSSL/libffi dylibs only; reject arbitrary Homebrew paths.
    extras = framework/'lib'; queue = [p for p in framework.rglob('*') if macho(p)]
    examined = set()
    for p in queue:
        if p in examined: continue
        examined.add(p)
        listing = subprocess.check_output(['/usr/bin/otool','-L',str(p)],text=True)
        for line in listing.splitlines()[1:]:
            if not line.startswith('\t'):continue  # Universal-architecture headings are not dependencies.
            dependency = line.strip().split(' (')[0]
            if not dependency.startswith('/') or dependency.startswith(('/usr/lib/','/System/Library/')): continue
            source = Path(dependency)
            if not source.is_relative_to(PYTHON_ROOT): raise SafeError('UNBUNDLED_DYLIB_DEPENDENCY')
            target = framework/'Python' if source == PYTHON_ROOT/'Python' else extras/source.name
            if not target.exists(): shutil.copyfile(source,target); queue.append(target)
            relative = os.path.relpath(target,p.parent)
            run('/usr/bin/install_name_tool','-change',dependency,'@loader_path/'+relative,p)
        if p == framework/'Python':run('/usr/bin/install_name_tool','-id','@rpath/EmbeddedPython/Python',p)
        elif p.suffix=='.dylib':run('/usr/bin/install_name_tool','-id','@loader_path/'+p.name,p)
        # Nested byte seals are made before the native inventory.
        run('/usr/bin/codesign','--force','--sign','-','--options','runtime','--entitlements',REPO/'apps/macos/development.entitlements',p,
            stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    (framework/'bin/python3.13').chmod(0o755)
    for p in framework.rglob('*.dylib'): p.chmod(0o755)
    return inventory


def bundle_asr(resources):
    engine = ASR/'build-v1.9.4-cpu/bin/whisper-cli'
    weights = ASR/'models/ggml-small.bin'
    notice = ASR/'source-v1.9.4/ggml-org-whisper.cpp-927cfce/LICENSE'
    expected_engine = '54d1e7bf2e36ec29bdf70b87a45e26158396d5004909d16d5ad76e51920b566c'
    expected_model = '1be3a9b2063867b937e64e2ec7483364a79917e157fa98c5d94b5c1fffea987b'
    if (not engine.is_file() or not weights.is_file() or not notice.is_file()
            or digest(engine.read_bytes())!=expected_engine or digest(weights.read_bytes())!=expected_model
            or digest(notice.read_bytes())!='94f29bbed6a22c35b992c5c6ebf0e7c92f13b836b90f36f461c9cf2f0f1d010d'):
        raise SafeError('LOCAL_ASR_MODEL_INTEGRITY')
    licence = REPO/'apps/macos/licences/WHISPER_MODEL_LICENSE.txt'
    if not licence.is_file(): raise SafeError('ASR_BUNDLE_BLOCKED')
    root=resources/'asr'; (root/'build-v1.9.4-cpu/bin').mkdir(parents=True); (root/'models').mkdir()
    shutil.copyfile(engine,root/'build-v1.9.4-cpu/bin/whisper-cli')
    (root/'build-v1.9.4-cpu/bin/whisper-cli').chmod(0o755)
    shutil.copyfile(weights,root/'models/ggml-small.bin')
    shutil.copyfile(ASR/'M7C_ASR_MODEL_RECEIPT.json',root/'M7C_ASR_MODEL_RECEIPT.json')
    shutil.copyfile(notice,resources/'licences/WHISPER_CPP_LICENSE.txt')
    shutil.copyfile(licence,resources/'licences/WHISPER_MODEL_LICENSE.txt')
    run('/usr/bin/codesign','--verify','--strict',root/'build-v1.9.4-cpu/bin/whisper-cli')
    receipt={'engine':'whisper.cpp','version':'1.9.4-dev','source_commit':'927cfce34f31707e17f2bff35c349632fb9e2c3a',
        'engine_original_sha256':expected_engine,'engine_sha256':expected_engine,'model':'small-multilingual',
        'model_revision':'5359861c739e955e79d9a303bcbc70fb988958b1','model_sha256':expected_model,
        'engine_licence':'MIT','model_licence':'MIT','cloud_asr':False,'new_download_bytes':0}
    (root/'bundle-receipt.json').write_text(encode(receipt))
    return receipt


def build(args):
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip()
    if subprocess.check_output(['git','status','--porcelain'],cwd=REPO,text=True).strip():
        raise SafeError('CLEAN_CHECKOUT_REQUIRED')
    if sys.platform!='darwin' or os.uname().machine!='arm64':raise SafeError('REFERENCE_MAC_INCOMPATIBLE')
    archive=SPARKLE_DIR.parent/'Sparkle-2.10.0.tar.xz'
    if not archive.is_file() or digest(archive.read_bytes()) != SPARKLE_HASH:
        raise SafeError('SPARKLE_PREREQUISITE_REQUIRED')
    run('/usr/bin/codesign','--verify','--deep','--strict',SPARKLE_DIR/'Sparkle.framework')
    output=Path(args.output).absolute()
    if not output.is_relative_to(REPO/'generated/m8f') or output.exists():raise SafeError('GENERATED_OUTPUT_REQUIRED')
    output.mkdir(parents=True)
    payload=REPO/'generated/releases'/('M8F-payload-'+commit)
    payload.parent.mkdir(parents=True,exist_ok=True)
    pm=release.prepare(payload) if not payload.exists() else release.validate_package(payload,release.read_json(payload/'release-manifest.json')['manifest_hash'])
    if pm['git_commit']!=commit:raise SafeError('RELEASE_INTEGRITY')
    app=output/'Personal Companion.app'
    macos=app/'Contents/MacOS'; macos.mkdir(parents=True)
    resources=app/'Contents/Resources'; resources.mkdir()
    (resources/'licences').mkdir()
    shutil.copytree(payload,resources/'payload')
    (resources/'payload/native_entry.py').write_text(
        "import sys\nfrom pathlib import Path\nsys.dont_write_bytecode=True\nsys.path.insert(0,str(Path(__file__).resolve().parent))\nfrom apps.core.native_macos import main\nmain()\n")
    # Add entry to the accepted unsigned payload manifest without changing its schema.
    pm=dict(pm);pm['files']=release.file_hashes(resources/'payload');pm['manifest_hash']=release.identity(pm)
    (resources/'payload/release-manifest.json').write_text(encode(pm))
    framework=app/'Contents/Frameworks'; framework.mkdir()
    runtime_inventory=bundled_runtime(resources/'runtime')
    shutil.copytree(SPARKLE_DIR/'Sparkle.framework',framework/'Sparkle.framework',symlinks=True)
    shutil.copyfile(SPARKLE_DIR/'LICENSE',resources/'licences/SPARKLE_LICENSE.txt')
    for name in ('react','react-dom'):
        shutil.copyfile(REPO/'apps/web/node_modules'/name/'LICENSE',resources/'licences'/(name.upper()+'_LICENSE.txt'))
    python_notice=PYTHON_ROOT/'Resources/English.lproj/Documentation/_sources/license.rst.txt'
    if not python_notice.is_file():raise SafeError('PYTHON_LICENCE_REQUIRED')
    shutil.copyfile(python_notice,resources/'licences/PYTHON_LICENSE.txt')
    shutil.copyfile(REPO/'docs/M8F_USER_GUIDE.md',resources/'User Guide.md')
    asr=None if args.without_asr else bundle_asr(resources)
    iconset=output/'Companion.iconset';iconset.mkdir()
    run('/usr/bin/xcrun','swift','-module-cache-path',REPO/'generated/m8f/swift-cache',
        REPO/'apps/macos/DrawIcon.swift',output/'icon-source.png')
    for size in (16,32,128,256,512):
        for scale in (1,2):
            name=f'icon_{size}x{size}'+('@2x' if scale==2 else '')+'.png'
            run('/usr/bin/sips','-z',size*scale,size*scale,output/'icon-source.png','--out',iconset/name,stdout=subprocess.DEVNULL)
    run('/usr/bin/iconutil','-c','icns',iconset,'-o',resources/'Companion.icns')
    profile='LOCAL_TEST' if args.test_public_key else 'DEVELOPMENT'
    public_key=Path(args.test_public_key).read_text().strip() if args.test_public_key else None
    if public_key:
        import base64
        from urllib.parse import urlparse
        if len(base64.b64decode(public_key,validate=True))!=32:raise SafeError('UPDATE_IDENTITY_INVALID')
        feed=urlparse(args.test_feed or '')
        if feed.scheme!='http' or feed.hostname!='127.0.0.1' or feed.username or feed.password or feed.query:
            raise SafeError('LOCAL_TEST_FEED_REQUIRED')
    info={'CFBundleExecutable':'PersonalCompanion','CFBundleIdentifier':PRODUCT+('.test' if public_key else '.dev'),
        'CFBundleName':'Personal Companion','CFBundleDisplayName':'Personal Companion',
        'CFBundlePackageType':'APPL','CFBundleShortVersionString':'0.8.6','CFBundleVersion':str(args.build),
        'CFBundleIconFile':'Companion.icns',
        'LSMinimumSystemVersion':'14.0','NSHighResolutionCapable':True,'NSPrincipalClass':'NSApplication',
        'NSMicrophoneUsageDescription':'Запис голосу зберігається на цьому Mac. Розпізнавання локальне; надсилання тексту лише за вашим вибором.',
        'NSHumanReadableCopyright':'Personal Companion — engineering candidate, local review only',
        'PCSourceSHA':commit,'PCProfile':profile,'PCProductionUpdates':'DISABLED',
        'SUEnableAutomaticChecks':False,'SUAutomaticallyUpdate':False,
        'SUVerifyUpdateBeforeExtraction':True,'SURequireSignedFeed':True,
        'SUEnableInstallerLauncherService':False,'SUEnableDownloaderService':False,
        'NSAppTransportSecurity':{'NSAllowsLocalNetworking':True}}
    if public_key:
        if not args.test_home or not args.test_home.startswith('/private/tmp/m8f-') or '..' in Path(args.test_home).parts:
            raise SafeError('DISPOSABLE_TEST_HOME_REQUIRED')
        info.update(SUPublicEDKey=public_key,SUFeedURL=args.test_feed,PCTestHome=args.test_home)
    with (app/'Contents/Info.plist').open('wb') as f:plistlib.dump(info,f,sort_keys=True)
    cmd=['/usr/bin/xcrun','swiftc','-swift-version','5','-O','-target','arm64-apple-macos14.0',
         '-module-cache-path',str(REPO/'generated/m8f/swift-cache'),'-framework','AppKit','-framework','WebKit',
         '-framework','LocalAuthentication','-framework','AVFoundation','-F',str(framework),
         '-framework','Sparkle','-Xlinker','-rpath','-Xlinker','@executable_path/../Frameworks']
    if public_key:cmd+=['-D','LOCAL_TEST']
    run(*cmd, REPO/'apps/macos/PersonalCompanion.swift','-o',macos/'PersonalCompanion')
    run('/usr/bin/codesign','--force','--sign','-','--options','runtime','--entitlements',
        REPO/'apps/macos/development.entitlements',macos/'PersonalCompanion')
    manifest={'format':1,'product':PRODUCT,'channel':CHANNEL if public_key else 'DISABLED',
        'arch':'arm64','minimum_macos':'14.0','build':args.build,'version':'0.8.6','source_sha':commit,
        'profile':profile,'production_updates':'DISABLED','payload_manifest_hash':pm['manifest_hash'],
        'runtime':runtime_inventory,'sparkle':{'version':'2.10.0','archive_sha256':SPARKLE_HASH,'signature':'ADHOC_NO_TEAM'},
        'python':subprocess.check_output([sys.executable,'-c','import platform;print(platform.python_version())'],text=True).strip(),
        'runtime_lock_sha256':digest((REPO/'requirements.runtime.lock').read_bytes()),'asr':asr,
        'defaults':release.DEFAULTS,'licences':'Contents/Resources/licences'}
    manifest['files'],manifest['symlinks']=bundle_files(app)
    manifest['manifest_hash']=release.identity(manifest)
    (resources/'native-manifest.json').write_text(encode(manifest))
    run('/usr/bin/codesign','--force','--sign','-','--options','runtime','--entitlements',
        REPO/'apps/macos/development.entitlements',app)
    run('/usr/bin/codesign','--verify','--deep','--strict',app)
    # Exact bundle byte proof with runtime PATH containing no developer tools.
    python=resources/'runtime/bin/python3.13'
    probe=subprocess.check_output([str(python),'-I','-B','-c',
        'import sys,importlib.util,json;print(json.dumps({"prefix":sys.prefix,"minimal":all(importlib.util.find_spec(x) is None for x in ["pip","pytest","playwright","httpx"])}))'],
        env={'PATH':'/var/empty'},text=True)
    if not json.loads(probe)['minimal']:raise SafeError('RUNTIME_ENVIRONMENT_NOT_MINIMAL')
    from apps.core.native_macos import validate_bundle
    validate_bundle(app)
    if (subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip()!=commit
            or subprocess.check_output(['git','status','--porcelain'],cwd=REPO,text=True).strip()):
        raise SafeError('CHECKOUT_CHANGED')
    if args.dmg:
        image=output/'Personal Companion.dmg'
        staging=output/'dmg-content';staging.mkdir()
        shutil.copytree(app,staging/app.name,symlinks=True)
        (staging/'Applications').symlink_to('/Applications',target_is_directory=True)
        shutil.copyfile(REPO/'docs/M8F_USER_GUIDE.md',staging/'Почніть тут.md')
        run('/usr/bin/hdiutil','create','-fs','APFS','-volname','Personal Companion — LOCAL TEST',
            '-srcfolder',staging,'-format','UDZO',image)
        shutil.rmtree(staging)
    # Only safe metadata in stdout; local paths remain ignored and owner-facing.
    (output/'build-receipt.json').write_text(encode({'source_sha':commit,'build':args.build,
        'manifest_hash':manifest['manifest_hash'],'profile':profile,'dmg_sha256':digest(image.read_bytes()) if args.dmg else None,
        'status':'DEVELOPMENT_LOCAL_ONLY','production_notarization':'NOT_RUN'}))
    return {'source_sha':commit,'build':args.build,'status':'DEVELOPMENT_LOCAL_ONLY','manifest_hash':manifest['manifest_hash']}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',required=True);p.add_argument('--build',type=int,required=True)
    p.add_argument('--test-public-key');p.add_argument('--test-feed');p.add_argument('--test-home');p.add_argument('--without-asr',action='store_true')
    p.add_argument('--dmg',action='store_true')
    a=p.parse_args()
    if a.build<1:raise SafeError('INVALID_BUILD')
    print(encode(build(a)))


if __name__=='__main__':main()
