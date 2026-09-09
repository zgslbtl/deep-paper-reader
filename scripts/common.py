"""Shared file and schema helpers; no network or model calls."""
import json
from pathlib import Path
import jsonschema
ROOT = Path(__file__).resolve().parents[1]

def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))

def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def schema_errors(value, name):
    schema = read_json(ROOT / 'schemas' / f'{name}.schema.json')
    jsonschema.Draft202012Validator.check_schema(schema)
    return [{'path': '/'.join(map(str, e.absolute_path)), 'message': e.message}
            for e in jsonschema.Draft202012Validator(schema).iter_errors(value)]

def require_schema(value, name):
    errors = schema_errors(value, name)
    if errors:
        raise ValueError(f'{name}: {errors[:5]}')
