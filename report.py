import json
import os
from datetime import datetime
from jinja2 import Template
from weasyprint import HTML

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

all_results = data.get("results", [])

# -----------------------------
# 2️⃣ Ask user for PDF output
# -----------------------------
pdf_file = input("Enter PDF output file name (e.g., report.pdf): ").strip()
if not pdf_file.lower().endswith(".pdf"):
    pdf_file += ".pdf"

# -----------------------------
# 3️⃣ Ask user for repository name
# -----------------------------
repo_name = input("Enter the repository name: ").strip()
if not repo_name:
    repo_name = os.path.basename(os.getcwd())

# -----------------------------
# 4️⃣ Filter and prepare statistics
# -----------------------------
severity_count = {"INFO": 0, "WARNING": 0, "ERROR": 0}
for r in all_results:
    sev = r.get("extra", {}).get("severity", "INFO").upper()
    if sev in severity_count:
        severity_count[sev] += 1

results = [r for r in all_results if r.get("extra", {}).get("severity", "").upper() in ("WARNING", "ERROR")]

total_findings = len(all_results)
critical_findings = len(results)
scan_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
scan_date_short = datetime.now().strftime("%Y-%m-%d")

# -----------------------------
# 4️⃣ CNES-style Jinja2 HTML template
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
.cover .badge.warning { background: #fed7aa; color: #c2410c; border: 2px solid #ea580c; }
.cover .badge.error { background: #fecaca; color: #b91c1c; border: 2px solid #dc2626; }
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
.severity-WARNING { background: #fed7aa; color: #c2410c; }
.severity-ERROR { background: #fecaca; color: #b91c1c; }
.check-id { 
    font-family: monospace; 
    font-size: 8pt;
    color: #4a5568;
    word-break: break-all;
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
    <div class="meta"><strong>Report Type:</strong> CNES-Style Executive Summary</div>
    <div class="badge-container">
        <div class="badge warning">{{ severity.WARNING }} WARNINGS</div>
        <div class="badge error">{{ severity.ERROR }} ERRORS</div>
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
            <div class="label">Actionable Items<br/>(WARNING/ERROR)</div>
        </div>
        <div class="summary-item">
            <div class="number">{{ severity.ERROR }}</div>
            <div class="label">Critical Issues</div>
        </div>
        <div class="summary-item">
            <div class="number">{{ severity.WARNING }}</div>
            <div class="label">Warnings</div>
        </div>
    </div>
</div>

<div class="risk-matrix">
    <h3>Risk Distribution</h3>
    <div class="risk-item high">
        <div class="risk-level">High Risk</div>
        <div class="risk-count">{{ severity.ERROR }}</div>
    </div>
    <div class="risk-item medium">
        <div class="risk-level">Medium Risk</div>
        <div class="risk-count">{{ severity.WARNING }}</div>
    </div>
    <div class="risk-item low">
        <div class="risk-level">Low Risk (Filtered)</div>
        <div class="risk-count">{{ severity.INFO }}</div>
    </div>
</div>

<p style="font-size: 10pt; color: #4a5568; margin: 20px 0;">
    <strong>Methodology:</strong> This report presents findings from automated Static Application Security Testing (SAST) analysis. 
    Only WARNING and ERROR severity findings are included in the detailed table below, as INFO-level findings do not require 
    immediate action. Findings have been categorized according to CWE and OWASP standards.
</p>

<div class="page-break"></div>

<h2 class="section-title">Detailed Findings (WARNING/ERROR Only)</h2>

{% if results %}
<table>
<thead>
    <tr>
        <th style="width: 8%">Severity</th>
        <th style="width: 25%">File Location</th>
        <th style="width: 15%">Rule ID</th>
        <th style="width: 35%">Description</th>
        <th style="width: 17%">Security Standards</th>
    </tr>
</thead>
<tbody>
{% for r in results %}
<tr>
    <td><span class="severity-badge severity-{{ r.extra.severity }}">{{ r.extra.severity }}</span></td>
    <td>
        <div class="file-path">{{ r.path }}</div>
        <div style="color: #718096; font-size: 8pt;">Line {{ r.start.line }}</div>
    </td>
    <td class="check-id">{{ r.check_id }}</td>
    <td class="description">{{ r.extra.message }}</td>
    <td>
        {% if r.extra.metadata.cwe %}
            {% for cwe in r.extra.metadata.cwe[:2] %}
                <span class="cwe-tag">{{ cwe }}</span>
            {% endfor %}
        {% endif %}
        {% if r.extra.metadata.technology %}
            <br/>
            {% for tech in r.extra.metadata.technology[:2] %}
                <span class="technology-tag">{{ tech }}</span>
            {% endfor %}
        {% endif %}
    </td>
</tr>
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

# -----------------------------
# 5️⃣ Render HTML
# -----------------------------
template = Template(html_template)
html_out = template.render(
    repo_name=repo_name,
    scan_date=scan_date,
    scan_date_short=scan_date_short,
    total_findings=total_findings,
    critical_findings=critical_findings,
    severity=severity_count,
    results=results
)

html_file = "temp_report.html"
with open(html_file, "w", encoding="utf-8") as f:
    f.write(html_out)

# -----------------------------
# 6️⃣ Generate PDF
# -----------------------------
HTML(string=html_out).write_pdf(pdf_file)

print(f"✅ CNES-style executive SAST report generated: {pdf_file}")
print(f"   Filtered to {critical_findings} actionable items ({severity_count['WARNING']} warnings, {severity_count['ERROR']} errors)")
