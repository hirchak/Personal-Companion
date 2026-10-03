import argparse
import os
from pathlib import Path
from uuid import uuid4
from .storage import Store, SafeError
from .domain import Journal
from .models import Create

def main():
    os.umask(0o077)
    p = argparse.ArgumentParser(description='M1 synthetic-only local journal')
    sub = p.add_subparsers(dest='command', required=True)
    for name in ['serve', 'init', 'backup', 'restore']:
        s = sub.add_parser(name)
        s.add_argument('--root', type=Path, required=True)
        if name in {'backup', 'restore'}:
            s.add_argument('--artifact', type=Path, required=True)
        if name == 'serve':
            s.add_argument('--port', type=int, default=8765)
            s.add_argument('--mode',choices=['local','m2-synthetic'],default='local')
            s.add_argument('--test-tls',action='store_true')
            s.add_argument('--synthetic-conversations',action='store_true',help='Explicit deterministic conversation demo, marked synthetic root only')
            s.add_argument('--synthetic-practices',action='store_true',help='Explicit neutral practice fixtures on marked synthetic root only')
        if name == 'init':
            s.add_argument('--seed', action='store_true')
    args = p.parse_args()
    try:
        if args.command == 'restore':
            Store.restore(args.artifact, args.root)
            print('Synthetic restore complete; reconciliation required.')
            return
        if args.command == 'init' and args.root.exists():
            raise SafeError('INITIALIZER_REQUIRES_NEW_ROOT')
        store = Store(args.root)
        if args.command == 'backup':
            store.backup(args.artifact)
            print('Synthetic consistent backup complete.')
        elif args.command == 'init':
            if args.seed:
                j = Journal(store)
                samples = [('inbox', 'SYNTHETIC · Думка про тихий ранок. ☀'), ('daily', 'SYNTHETIC · Сьогодні завершено невеликий малюнок.'),
                           ('sleep', 'SYNTHETIC · Нотатка про відпочинок, без вимірювання сну.'), ('creative', 'SYNTHETIC · Ідея: місто з паперовими садами.')]
                for kind, text in samples:
                    entry_id = uuid4()
                    j.write('create', entry_id, Create(operation_id=uuid4(), entry_id=entry_id, base_revision=0, payload={'type': kind, 'raw_text': text}))
            print('New SYNTHETIC demo initialized.')
        else:
            if not 1024 <= args.port <= 65535:
                raise SafeError('INVALID_PORT')
            from .network import deny_egress
            deny_egress()
            from .api import create_app
            import uvicorn
            tls={}
            scheme='http'
            if args.test_tls:
                if args.mode!='m2-synthetic': raise SafeError('TLS_TEST_REQUIRES_M2_HARNESS')
                import tempfile,subprocess
                directory=Path(tempfile.mkdtemp(prefix='m2-synthetic-tls-',dir=Path(tempfile.gettempdir()).resolve()))
                cert,key=directory/'certificate.pem',directory/'key.pem'
                subprocess.run(['openssl','req','-x509','-newkey','rsa:2048','-nodes','-days','1','-subj','/CN=localhost','-addext','subjectAltName=IP:127.0.0.1,DNS:localhost','-keyout',str(key),'-out',str(cert)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=True)
                tls={'ssl_keyfile':str(key),'ssl_certfile':str(cert)}
                scheme='https'
                print('Synthetic TLS test only: no trust installation; actual Android route OFF.',flush=True)
            app = create_app(args.root, args.port,m2=args.mode=='m2-synthetic',scheme=scheme,synthetic_practices=args.synthetic_practices,synthetic_conversations=args.synthetic_conversations)
            print(f'Open {scheme}://127.0.0.1:{args.port}\nOne-time unlock code (5 min): {app.state.auth.code}', flush=True)
            print('Stop: Ctrl+C. Lock/logout requires restart for a new one-time code.', flush=True)
            uvicorn.run(app, host='127.0.0.1', port=args.port, access_log=False, log_level='critical', **tls)
            if tls:
                import shutil
                shutil.rmtree(directory)
    except (SafeError, OSError, ValueError) as exc:
        print(exc.code if isinstance(exc, SafeError) else 'LOCAL_OPERATION_FAILED')
        raise SystemExit(1) from None

if __name__ == '__main__':
    main()
