import os
import json
import uuid
import io
import time
import logging
from collections import defaultdict, deque
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, send_file, flash, make_response, jsonify
from jinja2 import Template
from weasyprint import HTML

from normalizers import normalize, make_severity_count, merge_results

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

# --- Rate limiter ---
_limits = defaultdict(lambda: defaultdict(deque))

def rate_limit(max_reqs, window=60):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            key = request.remote_addr or 'unknown'
            now = time.time()
            dq = _limits[f.__name__][key]
            while dq and dq[0] < now - window:
                dq.popleft()
            if len(dq) >= max_reqs:
                logger.warning('Rate limit hit for %s from %s', f.__name__, key)
                return jsonify(error=f'Rate limit exceeded. Max {max_reqs} requests per {window}s.'), 429
            dq.append(now)
            return f(*args, **kwargs)
        return wrapper
    return decorator

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, 'uploads')

os.makedirs(UPLOAD_DIR, exist_ok=True)

REPORT_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Executive SAST Report</title>
<style>
@page {
    size: A4;
    margin: 20mm;
    @bottom-center {
        content: "Page " counter(page) " of " counter(pages);
        font-size: 9pt;
        color: #666;
    }
}
body { 
    font-family: 'DejaVu Sans', Arial, sans-serif; 
    margin: 0; 
    padding: 0;
    font-size: 10pt;
    color: #333;
}
.cover {
    text-align: center;
    margin-top: 180px;
    page-break-after: always;
}
.cover h1 {
    font-size: 28pt;
    color: #1a365d;
    margin-bottom: 30px;
    border-bottom: 4px solid #1a365d;
    padding-bottom: 15px;
    display: inline-block;
}
.cover .subtitle {
    font-size: 16pt;
    color: #4a5568;
    margin-bottom: 50px;
}
.cover .meta {
    font-size: 12pt;
    color: #718096;
    margin: 8px 0;
}
.cover .badge-container {
    margin-top: 60px;
    display: flex;
    justify-content: center;
    gap: 30px;
}
.cover .badge {
    padding: 20px 40px;
    border-radius: 8px;
    font-weight: bold;
    font-size: 14pt;
}
.cover .badge.critical { background: #7f1d1d; color: white; border: 2px solid #991b1b; }
.cover .badge.high { background: #dc2626; color: white; border: 2px solid #b91c1c; }
.cover .badge.medium { background: #f59e0b; color: white; border: 2px solid #d97706; }
.cover .badge.low { background: #22c55e; color: white; border: 2px solid #16a34a; }
.header {
    background: linear-gradient(135deg, #1a365d 0%, #2d5a87 100%);
    color: white;
    padding: 15px 25px;
    margin-bottom: 30px;
    border-radius: 4px;
}
.header h2 {
    margin: 0;
    font-size: 16pt;
}
.summary-section {
    background: #f7fafc;
    padding: 25px;
    border-radius: 8px;
    margin-bottom: 30px;
    border-left: 5px solid #1a365d;
}
.summary-grid {
    display: table;
    width: 100%;
}
.summary-item {
    display: table-cell;
    text-align: center;
    padding: 15px;
    border-right: 1px solid #e2e8f0;
}
.summary-item:last-child { border-right: none; }
.summary-item .number {
    font-size: 32pt;
    font-weight: bold;
    color: #1a365d;
}
.summary-item .label {
    font-size: 10pt;
    color: #718096;
    text-transform: uppercase;
    letter-spacing: 1px;
}
.risk-matrix {
    margin: 30px 0;
    padding: 20px;
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
}
.risk-matrix h3 {
    margin-top: 0;
    color: #1a365d;
    border-bottom: 2px solid #1a365d;
    padding-bottom: 10px;
}
.risk-item {
    display: inline-block;
    width: 30%;
    padding: 15px;
    margin: 10px 1%;
    text-align: center;
    border-radius: 6px;
    background: #fff;
    border: 1px solid #e2e8f0;
}
.risk-item.high { background: #fef2f2; border-color: #dc2626; }
.risk-item.medium { background: #fffbeb; border-color: #d97706; }
.risk-item.low { background: #f0fdf4; border-color: #16a34a; }
.risk-item .risk-level { font-size: 11pt; font-weight: bold; text-transform: uppercase; }
.risk-item.high .risk-level { color: #dc2626; }
.risk-item.medium .risk-level { color: #d97706; }
.risk-item.low .risk-level { color: #16a34a; }
.risk-item .risk-count { font-size: 24pt; font-weight: bold; color: #1a365d; }
table { 
    width: 100%; 
    table-layout: fixed;
    border-collapse: collapse; 
    margin-top: 20px;
    font-size: 9pt;
}
thead {
    background: #1a365d;
    color: white;
}
th { 
    padding: 12px 12px; 
    text-align: left;
    font-weight: 600;
    text-transform: uppercase;
    font-size: 7.5pt;
    letter-spacing: 0.3px;
}
td { 
    padding: 10px 12px; 
    vertical-align: top;
    border-bottom: 1px solid #e2e8f0;
    overflow-wrap: break-word;
    word-wrap: break-word;
}
tr:nth-child(even) { background: #f8fafc; }
tr:hover { background: #edf2f7; }
.severity-badge {
    padding: 3px 10px;
    border-radius: 10px;
    font-weight: bold;
    font-size: 7.5pt;
    text-transform: uppercase;
    letter-spacing: 0.3px;
}
.severity-CRITICAL { background: #7f1d1d; color: white; }
.severity-HIGH { background: #dc2626; color: white; }
.severity-MEDIUM { background: #f59e0b; color: white; }
.severity-LOW { background: #22c55e; color: white; }
.check-id { 
    font-family: monospace; 
    font-size: 7pt;
    color: #4a5568;
    overflow-wrap: break-word;
    word-wrap: break-word;
    line-height: 1.3;
}
.file-path {
    font-family: monospace;
    font-size: 8pt;
    color: #2d5a87;
}
.description {
    font-size: 9pt;
    color: #4a5568;
    line-height: 1.4;
}
.footer {
    margin-top: 40px;
    padding-top: 20px;
    border-top: 2px solid #e2e8f0;
    font-size: 8pt;
    color: #718096;
    text-align: center;
}
.technology-tag {
    display: inline-block;
    background: #e2e8f0;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 7pt;
    margin: 2px;
}
.cwe-tag {
    color: #dc2626;
    font-size: 7pt;
}
.page-break { page-break-before: always; }
.section-title {
    color: #1a365d;
    font-size: 14pt;
    border-bottom: 2px solid #1a365d;
    padding-bottom: 8px;
    margin-bottom: 20px;
}
</style>
</head>
<body>

<!-- COVER PAGE -->
<div class="cover">
    <h1>SAST EXECUTIVE REPORT</h1>
    <div class="subtitle">Static Application Security Testing Analysis</div>
    <div class="meta"><strong>Repository:</strong> {{ repo_name }}</div>
    <div class="meta"><strong>Scan Date:</strong> {{ scan_date_short }}</div>
    <div class="meta"><strong>Tool:</strong> {{ tool_name }}</div>
    <div class="meta"><strong>Report Type:</strong> Executive Summary</div>
    <div class="badge-container">
        <div class="badge critical">{{ severity.CRITICAL }} CRITICAL</div>
        <div class="badge high">{{ severity.HIGH }} HIGH</div>
        <div class="badge medium">{{ severity.MEDIUM }} MEDIUM</div>
        <div class="badge low">{{ severity.LOW }} LOW</div>
    </div>
</div>

<!-- MAIN CONTENT -->
<div class="header">
    <h2>Executive Summary</h2>
</div>

<div class="summary-section">
    <div class="summary-grid">
        <div class="summary-item">
            <div class="number">{{ total_findings }}</div>
            <div class="label">Total Findings</div>
        </div>
        <div class="summary-item">
            <div class="number">{{ critical_findings }}</div>
            <div class="label">Total Findings</div>
        </div>
    </div>
</div>

<div class="risk-matrix">
    <h3>Risk Distribution</h3>
    <div class="risk-item high" style="background: #fef2f2; border-color: #7f1d1d;">
        <div class="risk-level" style="color: #7f1d1d;">Critical</div>
        <div class="risk-count">{{ severity.CRITICAL }}</div>
    </div>
    <div class="risk-item high">
        <div class="risk-level">High Risk</div>
        <div class="risk-count">{{ severity.HIGH }}</div>
    </div>
    <div class="risk-item medium">
        <div class="risk-level">Medium Risk</div>
        <div class="risk-count">{{ severity.MEDIUM }}</div>
    </div>
    <div class="risk-item low">
        <div class="risk-level">Low Risk</div>
        <div class="risk-count">{{ severity.LOW }}</div>
    </div>
</div>

<p style="font-size: 10pt; color: #4a5568; margin: 20px 0;">
    <strong>Methodology:</strong> This report presents findings from automated security analysis. 
    Findings are categorized by severity (CRITICAL / HIGH / MEDIUM / LOW) and mapped to 
    relevant CWE identifiers where available. Each finding includes the file location, 
    rule identifier, and a description of the issue.
</p>

<div class="page-break"></div>

<h2 class="section-title">Detailed Findings (WARNING/ERROR Only)</h2>

{% if results %}
<table>
<thead>
    <tr>
        <th style="width: 10%">Severity</th>
        <th style="width: 19%">File Location</th>
        <th style="width: 15%">Rule ID</th>
        <th style="width: 34%">Description</th>
        <th style="width: 22%">CWE / Tech</th>
    </tr>
</thead>
<tbody>
{% for r in results %}
<tr>
    <td><span class="severity-badge severity-{{ r.severity }}">{{ r.severity }}</span></td>
    <td>
        <div class="file-path">{{ r.path }}</div>
        <div style="color: #718096; font-size: 8pt;">Line {{ r.line }}</div>
    </td>
    <td class="check-id">{{ r.check_id }}</td>
    <td class="description">{{ r.message }}</td>
    <td>
        {% if r.cwe %}
            {% for cwe in r.cwe[:2] %}
                <span class="cwe-tag">{{ cwe }}</span>
            {% endfor %}
        {% endif %}
        {% if r.technology %}
            <br/>
            {% for tech in r.technology[:2] %}
                <span class="technology-tag">{{ tech }}</span>
            {% endfor %}
        {% endif %}
    </td>
</tr>
{% if r.remediation %}
<tr>
    <td colspan="5" style="padding: 2px 8px 10px; font-size: 8pt; color: #2d5a87; border-bottom: 1px solid #e2e8f0;">
        <strong>Remediation:</strong> {{ r.remediation }}
    </td>
</tr>
{% endif %}
{% endfor %}
</tbody>
</table>
{% else %}
<p style="text-align: center; padding: 40px; color: #16a34a; font-size: 14pt;">
    No WARNING or ERROR findings detected. Your code passes security checks.
</p>
{% endif %}

<div class="footer">
    <p>Generated by SAST Executive Report Generator | {{ scan_date }}</p>
    <p>This report is intended for authorized personnel only. Findings should be reviewed by qualified security personnel.</p>
</div>

</body>
</html>
"""

def generate_pdf(data, repo_name: str) -> io.BytesIO:
    """Generate PDF from one or more scan data dicts.
    Pass a single dict or a list of dicts for multi-tool merge."""
    inputs = data if isinstance(data, list) else [data]
    results = []
    for d in inputs:
        name, findings = normalize(d)
        if findings:
            results.append((name, findings))
    if not results:
        raise ValueError('Unrecognized input format. Supported: Semgrep, SARIF, Snyk')
    tool_name, findings = merge_results(results)
    severity_count = make_severity_count(findings)
    total_findings = len(findings)
    now = datetime.now()
    scan_date = now.strftime('%Y-%m-%d %H:%M:%S')
    scan_date_short = now.strftime('%Y-%m-%d')
    template = Template(REPORT_TEMPLATE, autoescape=True)
    html_out = template.render(
        tool_name=tool_name,
        repo_name=repo_name or 'Unknown',
        scan_date=scan_date,
        scan_date_short=scan_date_short,
        total_findings=total_findings,
        critical_findings=total_findings,
        severity=severity_count,
        results=findings,
    )
    pdf_buffer = io.BytesIO()
    HTML(string=html_out).write_pdf(pdf_buffer)
    pdf_buffer.seek(0)
    return pdf_buffer

@app.route('/', methods=['GET', 'POST'])
@rate_limit(20, 60)
def index():
    if request.method == 'POST':
        uploaded = request.files.getlist('file')
        repo_name = request.form.get('repo_name', '').strip()
        if not uploaded or all(f.filename == '' for f in uploaded):
            flash('No file uploaded', 'error')
            return redirect(request.url)
        datas = []
        for f in uploaded:
            if not f or not f.filename:
                continue
            temp_id = uuid.uuid4().hex
            json_path = os.path.join(UPLOAD_DIR, f'scan_{temp_id}.json')
            f.save(json_path)
            try:
                with open(json_path, encoding='utf-8') as jf:
                    datas.append(json.load(jf))
            except Exception:
                flash(f'Invalid JSON in {f.filename}', 'error')
                return redirect(request.url)
            finally:
                if os.path.exists(json_path):
                    os.remove(json_path)
        if not datas:
            flash('No valid JSON files uploaded', 'error')
            return redirect(request.url)
        data = datas if len(datas) > 1 else datas[0]
        try:
            pdf_buffer = generate_pdf(data, repo_name)
            return send_file(
                pdf_buffer,
                mimetype='application/pdf',
                as_attachment=True,
                download_name='sast_report.pdf'
            )
        except ValueError as e:
            flash(str(e), 'error')
            return redirect(request.url)
        except Exception:
            logger.exception('Failed to generate report')
            flash('Error generating report. Please check your input and try again.', 'error')
            return redirect(request.url)
    response = make_response(render_template('index.html'))
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/api/v1/generate-report', methods=['POST'])
@rate_limit(10, 60)
def api_generate_report():
    repo_name = ''

    if request.is_json:
        data = request.get_json()
        if not data:
            return {'error': 'Empty request body'}, 400
        repo_name = request.args.get('repo_name', '')
    elif request.files:
        uploaded = request.files.getlist('file')
        repo_name = request.form.get('repo_name', '').strip()
        if not uploaded or all(f.filename == '' for f in uploaded):
            return {'error': 'No file uploaded'}, 400
        datas = []
        for f in uploaded:
            if f and f.filename:
                try:
                    datas.append(json.load(f))
                except json.JSONDecodeError:
                    return {'error': f'Invalid JSON in {f.filename}'}, 400
        data = datas if len(datas) > 1 else datas[0]
    else:
        return {'error': 'Send JSON body (Content-Type: application/json) or multipart form with "file" field'}, 400

    try:
        pdf_buffer = generate_pdf(data, repo_name)
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name='sast_report.pdf'
        )
    except ValueError as e:
        return {'error': str(e)}, 400
    except Exception:
        logger.exception('API report generation failed')
        return {'error': 'Failed to generate report. Please check your input and try again.'}, 500


if __name__ == '__main__':
    debug_mode = os.environ.get('FLASK_DEBUG', '0') == '1'
    app.run(host='0.0.0.0', port=5000, debug=debug_mode)