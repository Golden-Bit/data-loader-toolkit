#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
from pathlib import Path
import requests

# =========================
# CONFIG — MODIFICA QUI
# =========================
BASE_URL = "http://localhost:8000"                 # URL del tuo server
API_KEY  = "metti-una-chiave-robusta"              # Deve matchare UNSTRUCTURED_API_KEY del container
PDF_PATH = r"C:\Users\info\Desktop\work_space\repositories\data-loader-toolkit\unstructured\test\data\ui_ux_readme.pdf"        # Percorso PDF da processare (usa r"" su Windows)

# Strategia: "fast" | "hi_res" | "ocr_only" | "auto"
STRATEGY = "hi_res"

# Modello per hi_res (se usi hi_res o auto)
HI_RES_MODEL = "yolox"                              # oppure "detectron2_onnx" se disponibile

# Lingue OCR per PDF scansionati (codici Tesseract, es: ita, eng, deu, fra, spa)
OCR_LANGS = ["ita", "eng"]

# Hint lingue testo per il partizionamento (codici ISO, es: it, en, de, fr, es)
LANGUAGES = ["it", "en"]

# Flags aggiuntivi
INCLUDE_COORDINATES = True
INCLUDE_PAGE_BREAKS = True
PDF_INFER_TABLE_STRUCTURE = True                    # tabelle (solo hi_res/auto)

# Formato risposta: "json" oppure "csv"
OUTPUT_FORMAT = "json"

# File di output (vuoto = salva accanto al PDF con .json/.csv)
OUT_FILE = ""
# =========================


def main():
    base_url = BASE_URL.rstrip("/")
    endpoint = f"{base_url}/general/v0/general"
    pdf_path = Path(PDF_PATH)

    if not pdf_path.exists():
        raise FileNotFoundError(f"File non trovato: {pdf_path}")

    # Header: chiave API e Accept coerente col formato richiesto
    headers = {
        "unstructured-api-key": API_KEY,
        "Accept": "application/json" if OUTPUT_FORMAT == "json" else "text/csv",
    }

    # Form-data: parametri supportati dall’API Unstructured
    # NB: booleane come stringhe "true"/"false"
    data = {
        "strategy": STRATEGY,
        "hi_res_model_name": HI_RES_MODEL,
        "coordinates": "true" if INCLUDE_COORDINATES else "false",
        "include_page_breaks": "true" if INCLUDE_PAGE_BREAKS else "false",
        "output_format": "application/json" if OUTPUT_FORMAT == "json" else "text/csv",
        "pdf_infer_table_structure": "true" if PDF_INFER_TABLE_STRUCTURE else "false",
    }

    # Liste con sintassi key[]
    for lang in OCR_LANGS:
        data.setdefault("ocr_languages[]", []).append(lang)
    for lang in LANGUAGES:
        data.setdefault("languages[]", []).append(lang)

    # File multipart: il campo DEVE chiamarsi "files"
    with open(pdf_path, "rb") as fh:
        files = {"files": (pdf_path.name, fh, "application/pdf")}

        # (facoltativo) healthcheck per debug rapido
        try:
            hc = requests.get(f"{base_url}/healthcheck", timeout=5)
            print(f"[healthcheck] {hc.status_code} {hc.text[:120]}")
        except Exception as e:
            print(f"[healthcheck] fallito: {e}")

        print(f"POST {endpoint}")
        print(f"  file={pdf_path.name}")
        print(f"  strategy={STRATEGY}  hi_res_model={HI_RES_MODEL}  output={OUTPUT_FORMAT}")
        if OCR_LANGS:
            print(f"  ocr_languages={OCR_LANGS}")
        if LANGUAGES:
            print(f"  languages={LANGUAGES}")

        resp = requests.post(endpoint, headers=headers, data=data, files=files, timeout=180)

    if resp.status_code != 200:
        # dettaglio errore
        try:
            print(f"ERRORE {resp.status_code}: {resp.json()}")
        except Exception:
            print(f"ERRORE {resp.status_code}: {resp.text[:500]}")
        raise SystemExit(2)

    # Percorso output
    out_path = Path(OUT_FILE) if OUT_FILE else pdf_path.with_suffix(f".{OUTPUT_FORMAT}")

    # Salva risposta
    if OUTPUT_FORMAT == "csv":
        out_path.write_bytes(resp.content)
        print(f"[OK] CSV salvato: {out_path}")
    else:
        try:
            payload = resp.json()
        except Exception:
            payload = json.loads(resp.text)
        out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[OK] JSON salvato: {out_path}")

        # breve riepilogo
        if isinstance(payload, list):
            print(f"  elementi: {len(payload)}")
            if payload:
                print("  primo elemento (preview):")
                print(json.dumps(payload[0], ensure_ascii=False, indent=2)[:800])


if __name__ == "__main__":
    main()
