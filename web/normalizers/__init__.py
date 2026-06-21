from .base import Finding, make_severity_count, SEVERITY_LEVELS

from . import semgrep
from . import sarif
from . import snyk


NORMALIZERS = [
    ('Semgrep', semgrep),
    ('SARIF', sarif),
    ('Snyk', snyk),
]


def detect_tool(data: dict) -> tuple[str, callable]:
    for name, module in NORMALIZERS:
        if module.detect(data):
            return name, module.normalize
    return ('', None)


def normalize(data: dict) -> tuple[str, list[Finding]]:
    name, normalize_fn = detect_tool(data)
    if normalize_fn is None:
        return ('', [])
    return name, normalize_fn(data)
