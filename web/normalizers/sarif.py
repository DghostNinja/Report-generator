from .base import Finding


SEVERITY_MAP = {
    'error': 'CRITICAL',
    'warning': 'HIGH',
    'note': 'LOW',
    'none': 'LOW',
}


def detect(data: dict) -> bool:
    return isinstance(data.get('runs'), list) and len(data['runs']) > 0


def normalize(data: dict) -> list[Finding]:
    findings = []
    runs = data.get('runs', [])
    for run in runs:
        rules = _build_rule_map(run)
        tool_name = _get_tool_name(run)
        for result in run.get('results', []):
            rule_id = result.get('ruleId', '')
            rule = rules.get(rule_id, {})
            level = result.get('level', rule.get('defaultLevel', 'warning'))
            severity = SEVERITY_MAP.get(level, 'HIGH')
            message = _get_message(result)
            cwe = rule.get('cwe', [])
            location = _get_location(result)
            tech = [tool_name] if tool_name else []
            remediation = _get_remediation(result)
            findings.append(Finding(
                check_id=rule_id,
                path=location.get('path', ''),
                line=location.get('line', 0),
                message=message,
                severity=severity,
                remediation=remediation,
                cwe=cwe,
                technology=tech,
            ))
    return findings


def _build_rule_map(run: dict) -> dict:
    rules = {}
    for rule in run.get('tool', {}).get('driver', {}).get('rules', []):
        rule_id = rule.get('id', '')
        props = rule.get('properties', {}) or {}
        cwe_raw = props.get('cwe', props.get('cwes', []))
        if isinstance(cwe_raw, str):
            cwe_raw = [cwe_raw]
        cwe = []
        for c in cwe_raw:
            cwe.append(f'CWE-{c}' if isinstance(c, (int, float)) else str(c))
        default_level = rule.get('defaultConfiguration', {}).get('level', 'warning')
        rules[rule_id] = {
            'defaultLevel': default_level,
            'cwe': cwe,
        }
    return rules


def _get_message(result: dict) -> str:
    msg = result.get('message', {})
    if isinstance(msg, str):
        return msg
    return msg.get('text', msg.get('markdown', ''))


def _get_location(result: dict) -> dict:
    locs = result.get('locations', [])
    if not locs:
        return {}
    phys = locs[0].get('physicalLocation', {})
    art = phys.get('artifactLocation', {})
    path = art.get('uri', art.get('uriBaseId', ''))
    region = phys.get('region', {})
    line = region.get('startLine', region.get('startColumn', 0))
    return {'path': path, 'line': line}


def _get_remediation(result: dict) -> str:
    fixes = result.get('fixes', [])
    for fix in fixes:
        desc = fix.get('description', {})
        text = desc.get('text', '') if isinstance(desc, dict) else str(desc)
        if text:
            return text
    return ''


def _get_tool_name(run: dict) -> str:
    return run.get('tool', {}).get('driver', {}).get('name', '')
