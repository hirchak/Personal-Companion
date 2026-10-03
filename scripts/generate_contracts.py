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
    from apps.core import conversation_contracts,reflection_contracts,conversation_runtime_contracts
    for prefix,module in (('conversation',conversation_contracts),('reflection',reflection_contracts),('conversation-runtime',conversation_runtime_contracts)):
        for name,schema in module.schemas().items():
            Path('packages/contracts',prefix+'-'+name.lower()+'.json').write_text(json.dumps(schema,ensure_ascii=False,indent=2)+'\n')
finally:
    shutil.rmtree(root)
