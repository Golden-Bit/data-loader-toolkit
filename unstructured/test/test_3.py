# demo_langchain_api_loader.py
from pathlib import Path
from langchain_community.document_loaders import UnstructuredFileLoader

# ====== CONFIG ======
API_URL = "http://localhost:8000/"   # tua API self-hosted
API_KEY = "metti-una-chiave-robusta"                   # deve combaciare con UNSTRUCTURED_API_KEY del container
FILE_PATH = r"C:\Users\info\Desktop\work_space\repositories\data-loader-toolkit\unstructured\test\data\ui_ux_readme.pdf"

# Modalità del loader: "single" | "elements" | "paged"
MODE = "elements"

# kwargs passati a Unstructured (vedi docs Unstructured/LC)
UNSTRUCTURED_KWARGS = {
    "strategy": "hi_res",                 # "fast" | "hi_res" | "ocr_only" | "auto"
    "hi_res_model_name": "yolox",         # o "detectron2_onnx" se l’hai
    "coordinates": True,
    "include_page_breaks": True,
    "pdf_infer_table_structure": True,    # (vale con hi_res/auto)
    "ocr_languages": ["ita", "eng"],      # codici Tesseract
    "languages": ["it", "en"],            # hint lingua testo
    # altri parametri utili:
    # "xml_keep_tags": False,
    # "extract_image_block_types": ["table"],
    # "unique_element_ids": True,
}
# ====================

loader = UnstructuredAPIFileLoader(
    file_path=FILE_PATH,
    mode=MODE,
    api_key=API_KEY,
    api_url=API_URL,
    **UNSTRUCTURED_KWARGS,
)

docs = loader.load()

print(f"Documenti/elementi caricati: {len(docs)}")
for i, d in enumerate(docs[:5], start=1):
    print(f"\n--- DOC {i} ---")
    print(d.page_content[:400])
    print(d.metadata)
