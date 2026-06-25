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


def merge_results(results: list[tuple[str, list[Finding]]]) -> tuple[str, list[Finding]]:
    """Merge multiple (tool_name, findings) pairs into one."""
    names = []
    all_findings = []
    seen = set()
    for name, findings in results:
        if findings:
            names.append(name)
            for f in findings:
                key = (f.path, f.line, f.message)
                if key not in seen:
                    seen.add(key)
                    all_findings.append(f)
    tool_label = ' + '.join(dict.fromkeys(names)) if names else ''
    return tool_label, all_findings
