"""SYNTHETIC preview server; no unlock/pairing secret printed or logged."""
import tempfile
from pathlib import Path
import uvicorn
from apps.core.api import create_app
root=Path(tempfile.mkdtemp(prefix='m2-preview-synthetic-',dir=Path(tempfile.gettempdir()).resolve()))
try:
    app=create_app(root/'data',port=8769,m2=True)
    print('Synthetic PWA preview: http://127.0.0.1:8769/phone/ (loopback only)',flush=True)
    uvicorn.run(app,host='127.0.0.1',port=8769,access_log=False,log_level='critical')
finally:
    import shutil
    shutil.rmtree(root)
