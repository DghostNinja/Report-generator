# Security Report Generator

Generate professional PDF security reports from SAST/SCA scan results. Upload a JSON results file via the web UI or call the API directly from your CI/CD pipeline.

**Supported tools:**
- **Semgrep** — SAST (static analysis)
- **SARIF** — Standard format (CodeQL, Trivy, Roslyn, etc.)
- **Snyk** — SCA/container scanning

Format is **auto-detected** — just pipe the JSON and get a PDF back.

---

## Features

- **Professional PDF reports** — Executive summary with risk distribution, severity badges, and a detailed findings table.
- **Auto-detects tool format** — Semgrep, SARIF, and Snyk all work without configuration.
- **Multiple interfaces** — Web upload form, REST API, and standalone CLI script.
- **Pipeline-ready** — Pipe any supported tool's JSON output directly to the API.

---

## Quick Start

### Local Development

**Quick start (recommended):**
```bash
git clone https://github.com/DghostNinja/Report-generator.git
cd Report-generator
pip install -r requirements.txt
./start.sh
```

Or step-by-step:
```bash
cd web
python app.py
```

Open [http://localhost:5000](http://localhost:5000).

### Generate a Report

```bash
semgrep --json > results.json
# Upload via the web UI, or:
curl -X POST http://localhost:5000/api/v1/generate-report \
  -F "file=@results.json" -F "repo_name=my-app" -o sast_report.pdf
```

---

## Usage

### Web Interface

1. Select your scan results JSON file (Semgrep, SARIF, or Snyk).
2. Enter a repository name (optional).
3. Click **Generate PDF Report** to download.

### API — CI/CD Pipeline Integration

The `POST /api/v1/generate-report` endpoint auto-detects the tool format. No need to specify which tool you're using.

> Replace `https://sast-report-generator.onrender.com` with `http://localhost:5000` if running locally.

#### Semgrep

```bash
semgrep --json | curl -X POST https://sast-report-generator.onrender.com/api/v1/generate-report \
  -H "Content-Type: application/json" -d @- -o sast_report.pdf
```

#### SARIF (CodeQL, Trivy, etc.)

```bash
codeql database analyze --format=sarif-latest | curl -X POST \
  https://sast-report-generator.onrender.com/api/v1/generate-report \
  -H "Content-Type: application/json" -d @- -o sast_report.pdf
```

#### Snyk

```bash
snyk test --json | curl -X POST https://sast-report-generator.onrender.com/api/v1/generate-report \
  -H "Content-Type: application/json" -d @- -o sast_report.pdf
```

#### With repository name

```bash
semgrep --json | curl -X POST "https://sast-report-generator.onrender.com/api/v1/generate-report?repo_name=my-app" \
  -H "Content-Type: application/json" -d @- -o sast_report.pdf
```

#### Upload a saved file

```bash
curl -X POST https://sast-report-generator.onrender.com/api/v1/generate-report \
  -F "file=@results.json" -F "repo_name=my-app" -o sast_report.pdf
```

#### Step-by-Step Breakdown

1. **Tool command** (`semgrep --json`, `snyk test --json`, etc.) — Runs the tool and outputs JSON to stdout.
2. **`|`** (pipe) — Sends that JSON to the next command.
3. **`curl -X POST <url>`** — Makes a POST request to the API endpoint.
4. **`-H "Content-Type: application/json"`** — Tells the API you're sending JSON data.
5. **`-d @-`** — Reads the piped data (`@-` = stdin) and sends it as the request body.
6. **`-o sast_report.pdf`** — Saves the response (the PDF) to a file.

#### API Reference

**Endpoint:** `POST /api/v1/generate-report`

| Parameter | Location | Required | Description |
|-----------|----------|----------|-------------|
| `file` | multipart form | required\* | Security scan results (Semgrep, SARIF, Snyk) |
| `repo_name` | form / query | optional | Repository name for the report header |

\*For JSON body requests, the entire JSON is sent as the request body. Tool format is auto-detected.

**Responses:**

| Status | Meaning |
|--------|---------|
| `200 OK` | PDF generated successfully (`Content-Type: application/pdf`) |
| `400 Bad Request` | Missing or invalid input — returns `{"error": "..."}` |
| `500 Internal Server Error` | PDF generation failed — returns `{"error": "..."}` |

#### GitLab CI Example

```yaml
sast-report:
  stage: security
  image: python:3.12-slim
  script:
    - pip install semgrep
    - semgrep --json | curl -X POST https://sast-report-generator.onrender.com/api/v1/generate-report
        -H "Content-Type: application/json" -d @- -o sast_report.pdf
  artifacts:
    paths:
      - sast_report.pdf
```

#### GitHub Actions Example

```yaml
- name: Generate SAST Report
  run: |
    semgrep --json | curl -X POST https://sast-report-generator.onrender.com/api/v1/generate-report \
      -H "Content-Type: application/json" -d @- -o sast_report.pdf
- name: Upload Report
  uses: actions/upload-artifact@v4
  with:
    name: sast-report
    path: sast_report.pdf
```

### CLI (Local)

```bash
python report.py
```

The script prompts for:
1. Path to your scan results JSON file.
2. Output PDF filename.
3. Repository name.

---

## Project Structure

```
Report-generator/
├── web/
│   ├── app.py                  # Flask web application and API
│   ├── normalizers/            # Tool format normalizers
│   │   ├── base.py             # Common schema (Finding dataclass)
│   │   ├── semgrep.py          # Semgrep normalizer
│   │   ├── sarif.py            # SARIF normalizer
│   │   ├── snyk.py             # Snyk normalizer
│   │   └── __init__.py         # Auto-detect dispatcher
│   ├── templates/
│   │   └── index.html          # Web UI frontend
│   └── uploads/                # Temporary uploaded files
├── report.py                   # Standalone CLI script
├── requirements.txt            # Python dependencies
├── render.yaml                 # Render deployment configuration
├── start.sh                    # Local development launcher
├── LICENSE/LICENSE.txt         # MIT License
└── README.md                   # This file
```

---

## Technology Stack

| Component | Technology |
|-----------|-----------|
| Web Framework | [Flask](https://flask.palletsprojects.com/) |
| PDF Generation | [WeasyPrint](https://weasyprint.org/) |
| Template Engine | [Jinja2](https://jinja.palletsprojects.com/) |
| SAST Tools | [Semgrep](https://semgrep.dev/), [SARIF](https://sarifweb.azurewebsites.net/), [Snyk](https://snyk.io/) |
| Languages | Python, HTML/CSS, JavaScript |

---

## Input Formats

### Semgrep
```bash
semgrep --json > results.json
```

### SARIF (CodeQL, Trivy, etc.)
```bash
codeql database analyze --format=sarif-latest > results.sarif
trivy fs --format sarif . > results.sarif
```

### Snyk
```bash
snyk test --json > results.json
snyk code test --json > results.json
```

---

## License

This project is licensed under the [MIT License](LICENSE/LICENSE.txt).
