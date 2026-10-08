# ---------------------------------------------------------------
# LabLend - Lab Equipment Issue & Return Tracker
#   docker build -t lablend .                 -> production image
#   docker build --target test -t lablend-test .  -> image with pytest
# ---------------------------------------------------------------
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app ./app
COPY wsgi.py .

# ---- test stage: used by Jenkins to run the unit tests ----------
FROM base AS test
COPY requirements-dev.txt .
RUN pip install -r requirements-dev.txt
COPY tests ./tests
CMD ["pytest", "-v"]

# ---- production stage -------------------------------------------
FROM base AS production
RUN useradd --create-home lablend && chown -R lablend /app
USER lablend

EXPOSE 5000
HEALTHCHECK --interval=15s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/health', timeout=4)"

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "1", "--threads", "4", "--access-logfile", "-", "wsgi:app"]
