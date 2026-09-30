"""Generate OpenAPI from the actual adapter using only a disposable synthetic root."""
import json
import shutil
import tempfile
from pathlib import Path
from apps.core.api import create_app
root = Path(tempfile.mkdtemp(prefix='m1-schema-', dir=Path(tempfile.gettempdir()).resolve()))
try:
    app = create_app(root / 'data')
    Path('packages/contracts/openapi.json').write_text(json.dumps(app.openapi(), ensure_ascii=False, indent=2) + '\n')
finally:
    shutil.rmtree(root)
