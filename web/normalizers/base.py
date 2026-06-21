from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Finding:
    check_id: str
    path: str
    line: int
    message: str
    severity: str
    remediation: str = ''
    cwe: list[str] = field(default_factory=list)
    technology: list[str] = field(default_factory=list)


SEVERITY_ORDER = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
SEVERITY_LEVELS = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']


def make_severity_count(findings: list[Finding]) -> dict[str, int]:
    counts = {s: 0 for s in SEVERITY_LEVELS}
    for f in findings:
        severity = f.severity.upper()
        if severity in counts:
            counts[severity] += 1
    return counts
