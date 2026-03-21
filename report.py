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

results = data.get("results", [])

# -----------------------------
# 2️⃣ Ask user for PDF output
# -----------------------------
pdf_file = input("Enter PDF output file name (e.g., report.pdf): ").strip()
if not pdf_file.lower().endswith(".pdf"):
    pdf_file += ".pdf"

# -----------------------------
# 3️⃣ Prepare statistics
# -----------------------------
severity_count = {"INFO": 0, "WARNING": 0, "ERROR": 0}
for r in results:
    sev = r.get("severity", "INFO").upper()
    if sev in severity_count:
        severity_count[sev] += 1

total_findings = len(results)
scan_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
repo_name = os.path.basename(os.getcwd())  # current folder name as repo

# -----------------------------
# 4️⃣ Jinja2 HTML template
# -----------------------------
html_template = """
<html>
<head>
<meta charset="utf-8">
<title>Semgrep Executive Report</title>
<style>
body { font-family: Arial, sans-serif; margin: 30px; }
h1, h2 { text-align: center; }
h2 { margin-top: 5px; color: #555; }
table { width: 100%; border-collapse: collapse; margin-top: 20px; }
th, td { border: 1px solid #ddd; padding: 8px; vertical-align: top; }
th { background-color: #555; color: white; }
.INFO { color: blue; font-weight: bold; }
.WARNING { color: orange; font-weight: bold; }
.ERROR { color: red; font-weight: bold; }
a { color: #1a0dab; text-decoration: none; }
a:hover { text-decoration: underline; }
.cover { text-align: center; margin-top: 200px; }
</style>
</head>
<body>

<div class="cover">
    <h1>Semgrep SAST Executive Report</h1>
    <h2>Repository: {{ repo_name }}</h2>
    <h2>Scan Date: {{ scan_date }}</h2>
    <h2>Total Findings: {{ total_findings }}</h2>
</div>
<div style="page-break-after: always;"></div>

<h2>Summary</h2>
<p>INFO: {{ severity.INFO }} | WARNING: {{ severity.WARNING }} | ERROR: {{ severity.ERROR }}</p>

<h2>Detailed Findings</h2>
<table>
<tr>
    <th>File</th>
    <th>Line</th>
    <th>Severity</th>
    <th>Rule ID</th>
    <th>Description</th>
    <th>References</th>
</tr>
{% for r in results %}
<tr>
    <td>{{ r.path }}</td>
    <td>{{ r.start.line }}</td>
    <td class="{{ r.severity }}">{{ r.severity }}</td>
    <td>{{ r.check_id }}</td>
    <td>{{ r.extra.message }}</td>
    <td>
        {% for ref in r.extra.metadata.references %}
            <a href="{{ ref }}">{{ ref }}</a><br/>
        {% endfor %}
    </td>
</tr>
{% endfor %}
</table>

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
    total_findings=total_findings,
    severity=severity_count,
    results=results
)

# Save temporary HTML (optional, useful for debugging)
html_file = "temp_report.html"
with open(html_file, "w", encoding="utf-8") as f:
    f.write(html_out)

# -----------------------------
# 6️⃣ Generate PDF
# -----------------------------
HTML(string=html_out).write_pdf(pdf_file)

print(f"✅ PDF report generated: {pdf_file}")
