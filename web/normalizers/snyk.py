from .base import Finding


SEVERITY_MAP = {
    'critical': 'CRITICAL',
    'high': 'HIGH',
    'medium': 'MEDIUM',
    'low': 'LOW',
}


def detect(data: dict) -> bool:
    return isinstance(data.get('vulnerabilities'), list)


def normalize(data: dict) -> list[Finding]:
    findings = []
    for vuln in data.get('vulnerabilities', []):
        severity_raw = vuln.get('severity', 'medium')
        severity = SEVERITY_MAP.get(severity_raw, 'MEDIUM')
        cwe_raw = vuln.get('identifiers', {}).get('CWE', [])
        cwe = [f'CWE-{c}' if isinstance(c, (int, float)) else c for c in cwe_raw]
        path = vuln.get('packageName', vuln.get('moduleName', ''))
        if vuln.get('path'):
            path = vuln['path']
        findings.append(Finding(
            check_id=vuln.get('id', ''),
            path=path,
            line=vuln.get('line', 0),
            message=vuln.get('title', vuln.get('description', '')),
            severity=severity,
            cwe=cwe,
            technology=[vuln.get('packageName', '')],
        ))
    return findings
