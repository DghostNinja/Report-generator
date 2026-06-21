# SAST Executive Report Generator

Generate professional PDF security reports from **Semgrep** SAST scan results. Upload a JSON results file via the web UI or call the API directly from your CI/CD pipeline.

---

## Table of Contents

- [Features](#features)
- [Quick Start](#quick-start)
- [Usage](#usage)
  - [Web Interface](#web-interface)
  - [API — CI/CD Pipeline Integration](#api--cicd-pipeline-integration)
  - [CLI (Local)](#cli-local)
- [Project Structure](#project-structure)
- [Technology Stack](#technology-stack)

---

## Features

- **Professional PDF reports** — Executive summary with risk distribution, severity badges, and a detailed findings table.
- **Automated severity computation** — Maps Semgrep severity and impact/likelihood metadata to CRITICAL / HIGH / MEDIUM / LOW.
- **Multiple interfaces** — Web upload form, REST API, and standalone CLI script.
- **Pipeline-ready** — Pipe `semgrep --json` output directly to the API and get a PDF back.

---

## Quick Start

### Local Development

```bash
# Clone the repository
git clone <repo-url>
cd Report-generator

# Install dependencies
pip install flask>=3.0.0 jinja2>=3.0.0 weasyprint>=60.0

# Start the web server
cd web
python app.py
```

Open [http://localhost:5000](http://localhost:5000) in your browser.

### Generate a Report (Minimal Example)

1. Run Semgrep on your project:
   ```bash
   semgrep --json > results.json
   ```
2. Open [http://localhost:5000](http://localhost:5000), upload `results.json`, and click **Generate PDF Report**.

---

## Usage

### Web Interface

Navigate to the web app and use the upload form:

1. Select your Semgrep JSON results file.
2. Enter a repository name (optional — used in the report header).
3. Click **Generate PDF Report** to download.

### API — CI/CD Pipeline Integration

The `POST /api/v1/generate-report` endpoint is designed for pipeline automation. It accepts Semgrep JSON and returns a PDF.

> The examples below use the live hosted version at `https://sast-report-generator.onrender.com`. Replace with `http://localhost:5000` if running locally.

#### Common Pipeline Patterns

- **Pipe Semgrep output directly** — The most common approach for CI/CD:

  ```bash
  semgrep --json | curl -X POST https://sast-report-generator.onrender.com/api/v1/generate-report \
    -H "Content-Type: application/json" \
    -d @- \
    -o sast_report.pdf
  ```

- **Include a repository name** — Labels the report with your repo name:

  ```bash
  semgrep --json | curl -X POST "https://sast-report-generator.onrender.com/api/v1/generate-report?repo_name=my-app" \
    -H "Content-Type: application/json" \
    -d @- \
    -o sast_report.pdf
  ```

- **Upload a saved JSON file** — For when you already have the results file:

  ```bash
  curl -X POST https://sast-report-generator.onrender.com/api/v1/generate-report \
    -F "file=@results.json" \
    -F "repo_name=my-app" \
    -o sast_report.pdf
  ```

#### Step-by-Step Breakdown

Let's walk through what happens with the pipe command:

1. **`semgrep --json`** — Runs Semgrep on your code and outputs the results as JSON to stdout.
2. **`|`** (pipe) — Sends that JSON output to the next command.
3. **`curl -X POST <url>`** — Makes a POST request to the API endpoint.
4. **`-H "Content-Type: application/json"`** — Tells the API you're sending JSON data.
5. **`-d @-`** — Reads the piped data (`@-` means "read from stdin") and sends it as the request body.
6. **`-o sast_report.pdf`** — Saves the response (the PDF) to a file named `sast_report.pdf`.

#### API Reference

**Endpoint:** `POST /api/v1/generate-report`

| Parameter | Location | Required | Description |
|-----------|----------|----------|-------------|
| `file` | multipart form | required\* | Semgrep JSON results file |
| `repo_name` | form / query | optional | Repository name for the report header |

\*For JSON body requests, the full Semgrep JSON is sent as the request body instead of using the `file` field.

**Responses:**

| Status | Meaning |
|--------|---------|
| `200 OK` | PDF generated successfully (`Content-Type: application/pdf`) |
| `400 Bad Request` | Missing or invalid input — returns `{"error": "..."}` |
| `500 Internal Server Error` | PDF generation failed — returns `{"error": "..."}` |

#### Example: GitLab CI Job

```yaml
sast-report:
  stage: security
  image: python:3.12-slim
  script:
    - pip install semgrep
    - semgrep --json | curl -X POST https://sast-report-generator.onrender.com/api/v1/generate-report
        -H "Content-Type: application/json"
        -d @-
        -o sast_report.pdf
  artifacts:
    paths:
      - sast_report.pdf
```

#### Example: GitHub Actions Job

```yaml
- name: Generate SAST Report
  run: |
    semgrep --json | curl -X POST https://sast-report-generator.onrender.com/api/v1/generate-report \
      -H "Content-Type: application/json" \
      -d @- \
      -o sast_report.pdf
- name: Upload Report
  uses: actions/upload-artifact@v4
  with:
    name: sast-report
    path: sast_report.pdf
```

### CLI (Local)

You can also generate a report locally without the web server:

```bash
python report.py
```

The script will prompt you for:
1. Path to your Semgrep JSON file.
2. Output PDF filename.
3. Repository name.

## Project Structure

```
Report-generator/
├── web/
│   ├── app.py                  # Flask web application and API
│   ├── templates/
│   │   └── index.html          # Web UI frontend
│   └── uploads/                # Temporary uploaded files
├── report.py                   # Standalone CLI script
├── requirements.txt            # Python dependencies
├── render.yaml                 # Render deployment configuration
├── start.sh                    # Local development launcher
└── README.md                   # This file
```

---

## Technology Stack

| Component | Technology |
|-----------|-----------|
| Web Framework | [Flask](https://flask.palletsprojects.com/) |
| PDF Generation | [WeasyPrint](https://weasyprint.org/) |
| Template Engine | [Jinja2](https://jinja.palletsprojects.com/) |
| SAST Tool | [Semgrep](https://semgrep.dev/) |
| Languages | Python, HTML/CSS, JavaScript |

---

## Input Format

The API expects a **Semgrep JSON output** file. Generate it with:

```bash
semgrep --json > results.json
```

The JSON should contain a `results` array where each result has `check_id`, `path`, `start.line`, and `extra` fields (with `severity`, `message`, and optional `metadata.impact` / `metadata.likelihood`).

---

## License

This project is licensed under the [MIT License](LICENSE/LICENSE.txt).


