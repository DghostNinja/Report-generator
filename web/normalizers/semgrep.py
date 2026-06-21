from .base import Finding


def detect(data: dict) -> bool:
    results = data.get('results')
    if not isinstance(results, list):
        return False
    if not results:
        return True
    return 'check_id' in results[0] and 'extra' in results[0]


def normalize(data: dict) -> list[Finding]:
    findings = []
    for r in data.get('results', []):
        severity = _compute_severity(r)
        meta = r.get('extra', {}).get('metadata', {})
        cwe = meta.get('cwe', [])
        if isinstance(cwe, str):
            cwe = [cwe]
        tech = meta.get('technology', [])
        if isinstance(tech, str):
            tech = [tech]
        findings.append(Finding(
            check_id=r.get('check_id', ''),
            path=r.get('path', ''),
            line=r.get('start', {}).get('line', 0),
            message=r.get('extra', {}).get('message', ''),
            severity=severity,
            cwe=cwe,
            technology=tech,
        ))
    return findings


def _compute_severity(result: dict) -> str:
    impact = result.get('extra', {}).get('metadata', {}).get('impact', 'LOW').upper()
    likelihood = result.get('extra', {}).get('metadata', {}).get('likelihood', 'LOW').upper()
    severity_type = result.get('extra', {}).get('severity', 'INFO').upper()
    if severity_type == 'ERROR':
        return 'CRITICAL'
    if impact == 'HIGH' or likelihood == 'HIGH':
        return 'HIGH'
    if impact == 'MEDIUM' or likelihood == 'MEDIUM':
        return 'MEDIUM'
    return 'LOW'
