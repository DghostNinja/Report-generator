FROM python:3.13-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 libpangocairo-1.0-0 libcairo2 \
    shared-mime-info fonts-dejavu-core && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY web/ web/
COPY samples/ samples/
COPY LICENSE/LICENSE.txt LICENSE/

RUN adduser --disabled-password --gecos '' app && chown -R app:app /app
USER app

ENV FLASK_DEBUG=0 PYTHONDONTWRITEBYTECODE=1

EXPOSE 5000
WORKDIR /app/web
CMD ["python3", "app.py"]
