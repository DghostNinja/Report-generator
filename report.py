import json
import os
import sys
import logging
from datetime import datetime
from jinja2 import Template
from weasyprint import HTML

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'web'))
from normalizers import normalize, make_severity_count

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# -----------------------------
# 1️⃣ Ask user for JSON file
# -----------------------------
while True:
    json_path = input("Enter the path to your report JSON file: ").strip()
    if os.path.isfile(json_path):
        break
    print("File not found. Please enter a valid path.")

with open(json_path, encoding="utf-8") as f:
    data = json.load(f)

tool_name, findings = normalize(data)
if not findings:
    print("Error: Unrecognized input format.\nSupported formats: Semgrep, SARIF (CodeQL, Trivy, etc.), Snyk.\nSave your tool's JSON output to a file and point to it here.")
    sys.exit(1)

# -----------------------------
# 2️⃣ Ask user for PDF output
# -----------------------------
pdf_file = input("Enter PDF output file name (e.g., report.pdf): ").strip()
if not pdf_file:
    print("Error: No filename provided.")
    sys.exit(1)
# Prevent path traversal in filename
pdf_file = os.path.basename(pdf_file)
if not pdf_file.lower().endswith(".pdf"):
    pdf_file += ".pdf"

# -----------------------------
# 3️⃣ Ask user for repository name
# -----------------------------
repo_name = input("Enter the repository name: ").strip()
if not repo_name:
    repo_name = os.path.basename(os.getcwd())

# -----------------------------
# 4️⃣ Render HTML template
# -----------------------------
severity_count = make_severity_count(findings)
results = findings
total_findings = len(findings)
critical_findings = len(findings)
scan_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
scan_date_short = datetime.now().strftime("%Y-%m-%d")

# -----------------------------
# 5️⃣ Jinja2 HTML template
# -----------------------------
html_template = """
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
    border-collapse: collapse; 
    margin-top: 20px;
    font-size: 9pt;
}
thead {
    background: #1a365d;
    color: white;
}
th { 
    padding: 12px 8px; 
    text-align: left;
    font-weight: 600;
    text-transform: uppercase;
    font-size: 8pt;
    letter-spacing: 0.5px;
}
td { 
    padding: 10px 8px; 
    vertical-align: top;
    border-bottom: 1px solid #e2e8f0;
}
tr:nth-child(even) { background: #f8fafc; }
tr:hover { background: #edf2f7; }
.severity-badge {
    padding: 4px 12px;
    border-radius: 12px;
    font-weight: bold;
    font-size: 8pt;
    text-transform: uppercase;
}
.severity-CRITICAL { background: #7f1d1d; color: white; }
.severity-HIGH { background: #dc2626; color: white; }
.severity-MEDIUM { background: #f59e0b; color: white; }
.severity-LOW { background: #22c55e; color: white; }
.check-id { 
    font-family: monospace; 
    font-size: 7pt;
    color: #4a5568;
    word-break: break-all;
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
    <div class="meta"><strong>Scan Date:</strong> {{ scan_date }}</div>
    <div class="meta"><strong>Tool:</strong> {{ tool_name }}</div>
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

<h2 class="section-title">Detailed Findings</h2>

{% if results %}
<table>
<thead>
    <tr>
        <th style="width: 8%">Severity</th>
        <th style="width: 22%">File Location</th>
        <th style="width: 28%">Rule ID</th>
        <th style="width: 30%">Description</th>
        <th style="width: 12%">Security Standards</th>
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
    No findings detected.
</p>
{% endif %}

<div class="footer">
    <p>Generated by SAST Executive Report Generator | {{ scan_date }}</p>
    <p>This report is intended for authorized personnel only. Findings should be reviewed by qualified security personnel.</p>
</div>

</body>
</html>
"""

# -----------------------------
# 6️⃣ Render HTML
# -----------------------------
template = Template(html_template, autoescape=True)
html_out = template.render(
    tool_name=tool_name,
    repo_name=repo_name,
    scan_date=scan_date,
    scan_date_short=scan_date_short,
    total_findings=total_findings,
    critical_findings=critical_findings,
    severity=severity_count,
    results=results
)

# -----------------------------
# 7️⃣ Generate PDF
# -----------------------------
try:
    HTML(string=html_out).write_pdf(pdf_file)
except Exception:
    logger.exception("Failed to generate PDF")
    print("Error: Failed to generate PDF. Check your input and try again.")
    sys.exit(1)

print(f"SAST report generated: {pdf_file}")
print(f"   Total findings: {total_findings}")
print(f"   Critical: {severity_count['CRITICAL']}, High: {severity_count['HIGH']}, Medium: {severity_count['MEDIUM']}, Low: {severity_count['LOW']}")
