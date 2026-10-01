#!/usr/bin/env python3
"""Owner-authorized project-local Android build dependencies only. No global changes."""
import hashlib,json,os,platform,subprocess,tarfile,urllib.request,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
TOOLS=ROOT/'generated/android-tools';TOOLS.mkdir(parents=True,exist_ok=True)
def download(url,name,sha=None):
    out=TOOLS/name
    if not out.exists():
        subprocess.run(['curl','--fail','--location','--retry','2','--silent','--show-error',url,'--output',str(out)],check=True)
    if sha and hashlib.sha256(out.read_bytes()).hexdigest()!=sha:raise RuntimeError('DEPENDENCY_CHECKSUM_MISMATCH')
    return out
if platform.system()!='Darwin' or platform.machine()!='arm64':raise SystemExit('THIS_BOOTSTRAP_IS_MAC_ARM64_ONLY')
if not (TOOLS/'jdk/Contents/Home/bin/java').exists():
    info=json.loads(subprocess.check_output(['curl','-fsSL','https://api.adoptium.net/v3/assets/latest/17/hotspot?architecture=aarch64&image_type=jdk&os=mac']))[0]['binary']['package']
    archive=download(info['link'],'jdk.tar.gz',info['checksum'])
    folder=TOOLS/'jdk-extract';folder.mkdir(exist_ok=True)
    with tarfile.open(archive) as f:f.extractall(folder,filter='data')
    next(folder.iterdir()).rename(TOOLS/'jdk')
SDK=TOOLS/'sdk';SDK.mkdir(exist_ok=True)
if not (SDK/'cmdline-tools/latest/bin/sdkmanager').exists():
    archive=download('https://dl.google.com/android/repository/commandlinetools-mac-13114758_latest.zip','cmdline.zip')
    with zipfile.ZipFile(archive) as f:f.extractall(SDK)
    (SDK/'cmdline-tools').rename(SDK/'cmdline-temp')
    (SDK/'cmdline-tools').mkdir();(SDK/'cmdline-temp').rename(SDK/'cmdline-tools/latest')
    for f in (SDK/'cmdline-tools/latest/bin').iterdir():f.chmod(0o755)
if not (TOOLS/'gradle-8.13/bin/gradle').exists():
    url='https://services.gradle.org/distributions/gradle-8.13-bin.zip'
    sha=subprocess.check_output(['curl','-fsSL',url+'.sha256']).decode().strip()
    with zipfile.ZipFile(download(url,'gradle.zip',sha)) as f:f.extractall(TOOLS)
    (TOOLS/'gradle-8.13/bin/gradle').chmod(0o755)
env={**os.environ,'JAVA_HOME':str(TOOLS/'jdk/Contents/Home'),'ANDROID_HOME':str(SDK),'ANDROID_USER_HOME':str(TOOLS/'android-user'),'GRADLE_USER_HOME':str(TOOLS/'gradle-cache')}
manager=[str(TOOLS/'jdk/Contents/Home/bin/java'),'-Dcom.android.sdklib.toolsdir='+str(SDK/'cmdline-tools/latest'),'-classpath',str(SDK/'cmdline-tools/latest/lib/sdkmanager-classpath.jar'),'com.android.sdklib.tool.sdkmanager.SdkManagerCli']
subprocess.run([*manager,'--sdk_root='+str(SDK),'--licenses'],input='y\n'*30,text=True,env=env,check=True,stdout=subprocess.DEVNULL)
subprocess.run([*manager,'--sdk_root='+str(SDK),'platform-tools','platforms;android-36','build-tools;35.0.0'],env=env,check=True)
print('PROJECT_LOCAL_ANDROID_DEPENDENCIES_READY')
