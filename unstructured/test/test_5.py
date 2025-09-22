# demo_langchain_unstructured_api_full.py
from pathlib import Path
import json
from langchain_unstructured import UnstructuredLoader

# ========= CONFIG =========

# Modalità post-processing del loader: "elements" | "single" | "paged"
MODE = "elements"

# Formato risposta dell'API: "application/json" | "text/csv"
# ATTENZIONE: il loader si aspetta JSON; per CSV meglio usare la versione con 'requests'.
OUTPUT_FORMAT = "application/json"

# ========= PARAMETRI DI PARTITION (API) =========
# Coprono praticamente tutto ciò che la tua API self-hosted accetta.
UNSTRUCTURED_KWARGS = {
    # --- strategia e modelli ---
    "strategy": "hi_res",                   # "fast" | "hi_res" | "ocr_only" | "auto"
    "hi_res_model_name": "yolox",           # oppure "detectron2_onnx" se l'hai
    "output_format": OUTPUT_FORMAT,         # "application/json" (consigliato col loader)

    # --- OCR / lingua ---
    "ocr_languages": ["ita", "eng"],        # codici Tesseract (ita, eng, fra, deu, spa, ...)
    "languages": ["it", "en"],              # hint ISO-639-1 del testo
    "encoding": "utf-8",

    # --- layout / coordinate / page breaks ---
    "coordinates": True,                    # includi coordinate per ogni elemento
    "include_page_breaks": True,            # inserisce page break nel testo (utile per chunking)
    "starting_page_number": 1,              # offset numerazione pagine

    # --- tabelle PDF ---
    "pdf_infer_table_structure": True,      # inferenza tabella (solo hi_res/auto)
    "skip_infer_table_types": [],           # es. ["pdf"] per saltare inferenza su PDF
    # "extract_image_block_types": ["table"],# estrae payload immagine per certi blocchi (es. tabelle)
    # "extract_image_block_to_payload": True,# (se estrai immagini) includile nel payload JSON

    # --- contenuto XML/HTML ---
    "xml_keep_tags": False,                 # True per mantenere i tag XML nel testo

    # --- slide (PPTX) ---
    "include_slide_notes": True,            # includi note delle slide

    # --- chunking (post-process Unstructured prima della conversione in Document) ---
    #   "basic": split a lunghezza; "by_title": sezioni per titoli (pdf/doc)
    "chunking_strategy": "by_title",        # "basic" | "by_title" | None
    "combine_under_n_chars": 2000,          # merge di pezzetti troppo corti
    "max_characters": 4000,                 # max lunghezza chunk
    "multipage_sections": True,             # sezioni che attraversano più pagine
    "new_after_n_chars": None,              # forza nuovo chunk dopo N caratteri (None = disabilitato)
    "overlap": 200,                         # overlap fra chunk
    "overlap_all": False,                   # overlap anche su blocchi senza titolo
    "unique_element_ids": True,             # assegna ID univoci agli elementi

    # --- tipi MIME / hint contenuto (di solito non serve specificare) ---
    # "content_type": "application/pdf",
}

# ========= ESECUZIONE =========
def main():
    pdf = Path(FILE_PATH)
    if not pdf.exists():
        raise FileNotFoundError(f"File non trovato: {pdf}")

    loader = UnstructuredLoader(
        file_path=str(pdf),
        mode=MODE,
        partition_via_api=True,    # usa la tua API, non il processing locale
        url=API_URL,               # endpoint completo /general/v0/general
        api_key=API_KEY,           # header 'unstructured-api-key'
        **UNSTRUCTURED_KWARGS,     # tutti i parametri di sopra
    )

    docs = loader.load()

    # Output base
    print(f"Documenti/elementi caricati: {len(docs)}")
    for i, d in enumerate(docs[:5], start=1):
        print(f"\n--- DOC {i} ---")
        print(d.page_content[:400])
        print(d.metadata)

    # Salva il risultato in JSON "stile LangChain" (lista di Document in forma dict)
    out_json = pdf.with_suffix(".lc.json")
    as_dicts = []
    for d in docs:
        as_dicts.append({
            "page_content": d.page_content,
            "metadata": dict(d.metadata) if hasattr(d, "metadata") else {},
        })

    out_json.write_text(json.dumps(as_dicts, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[OK] Salvataggio JSON (LangChain Document) in: {out_json}")

    # Nota su CSV:
    if OUTPUT_FORMAT == "text/csv":
        print("\n[Nota] Hai impostato OUTPUT_FORMAT='text/csv'. "
              "Il loader LangChain si aspetta JSON: per CSV usa lo script via 'requests' "
              "per salvare direttamente il contenuto CSV dell'API.")

if __name__ == "__main__":
    main()
