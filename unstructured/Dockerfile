# ===========================
# Stage 1: Build environment
# ===========================
FROM ubuntu:24.04 AS builder

ENV DEBIAN_FRONTEND=noninteractive
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# 1) Python 3.12 + toolchain + OCR + deps OpenCV
RUN apt-get update && apt-get install -y --no-install-recommends \
      python3.12 python3.12-dev python3.12-venv python3-pip \
      build-essential curl git pkg-config \
      # OCR
      tesseract-ocr tesseract-ocr-eng tesseract-ocr-ita \
      tesseract-ocr-fra tesseract-ocr-deu tesseract-ocr-spa \
      libtesseract-dev libleptonica-dev \
      # Dipendenze runtime OpenCV (risolve libGL.so.1 & co.)
      libgl1 libglib2.0-0 libsm6 libxext6 libxrender1 libgomp1 \
      # (facoltativo ma utile in alcuni casi)
      poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# 2) Virtualenv Python 3.12
RUN python3.12 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 3) Librerie Python: Unstructured + Uvicorn
RUN pip install --no-cache-dir --upgrade pip setuptools wheel \
 && pip install --no-cache-dir "unstructured[all-docs]" \
 && pip install --no-cache-dir uvicorn

# 4) Clona l'API Unstructured (non è su PyPI)
WORKDIR /opt
RUN git clone https://github.com/Unstructured-IO/unstructured-api.git
WORKDIR /opt/unstructured-api
# (opzionale) fissa una release nota stabile:
# RUN git checkout tags/v0.0.71

# 5) Requirements dell’API (compatibili con Py 3.12)
RUN pip install --no-cache-dir -r requirements/base.txt

# ===========================
# Stage 2: Runtime
# ===========================
FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Python 3.12 + OCR + deps OpenCV anche nel runtime
RUN apt-get update && apt-get install -y --no-install-recommends \
      python3.12 python3.12-venv \
      # OCR
      tesseract-ocr tesseract-ocr-eng tesseract-ocr-ita \
      tesseract-ocr-fra tesseract-ocr-deu tesseract-ocr-spa \
      libtesseract-dev libleptonica-dev pkg-config \
      # Dipendenze runtime OpenCV (libGL, X11, OpenMP)
      libgl1 libglib2.0-0 libsm6 libxext6 libxrender1 libgomp1 \
      # (facoltativo)
      poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Copia venv + codice API dal builder
COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /opt/unstructured-api /opt/unstructured-api
ENV PATH="/opt/venv/bin:$PATH"
WORKDIR /opt/unstructured-api

# ===== ENV defaults (override a runtime) =====
ENV PORT=8000 \
    HOST=0.0.0.0 \
    WORKERS=1 \
    UNSTRUCTURED_MEMORY_FREE_MINIMUM_MB=2048 \
    UNSTRUCTURED_PARALLEL_MODE_ENABLED=true \
    UNSTRUCTURED_PARALLEL_MODE_THREADS=4 \
    UNSTRUCTURED_PARALLEL_MODE_SPLIT_SIZE=1 \
    UNSTRUCTURED_PARALLEL_RETRY_ATTEMPTS=2 \
    UNSTRUCTURED_PARALLEL_MODE_URL="http://127.0.0.1:8000/general/v0/general" \
    UNSTRUCTURED_HI_RES_MODEL_NAME=yolox \
    ALLOW_ORIGINS="*" \
    UNSTRUCTURED_ALLOWED_MIMETYPE="application/pdf,image/jpeg,image/png" \
    UNSTRUCTURED_PDF_HI_RES_MAX_PAGES=9999 \
    SCARF_NO_ANALYTICS=true \
    DO_NOT_TRACK=true
# ENV UNSTRUCTURED_REDIRECT_ROOT_URL="https://docs.tua-azienda.it/unstructured"

EXPOSE 8000

# ===== Avvio =====
# uso la shell-form per espandere le ENV (PORT/WORKERS) nel comando
CMD bash -lc 'uvicorn prepline_general.api.app:app \
  --host "$HOST" --port "$PORT" --workers "${WORKERS:-1}" \
  --log-level info --access-log'
