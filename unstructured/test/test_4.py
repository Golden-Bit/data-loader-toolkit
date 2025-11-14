# demo_langchain_unstructured_api.py
from pathlib import Path
from langchain_unstructured import UnstructuredLoader

# ====== CONFIG ======
API_URL = "http://34.13.153.241:8333/" #"http://localhost:8000/"
API_KEY = "metti-una-chiave-robusta"
FILE_PATH = r"C:\Users\info\Desktop\work_space\repositories\data-loader-toolkit\unstructured\test\data\documentazione_richiesta.pdf"

# Il loader supporta post-processing "elements"/"paged"/"single" via param 'mode'
MODE = "elements"

UNSTRUCTURED_KWARGS = {
    "strategy": "hi_res",
    "hi_res_model_name": "yolox",
    "coordinates": True,
    "include_page_breaks": True,
    "pdf_infer_table_structure": True,
    "ocr_languages": ["ita", "eng"],
    "languages": ["it", "en"],
}
# ====================

loader = UnstructuredLoader(
    file_path=FILE_PATH,
    mode=MODE,
    partition_via_api=True,   # <<< usa API, non locale
    api_key=API_KEY,
    url=API_URL,              # <<< punta alla tua API self-hosted
    **UNSTRUCTURED_KWARGS,
)

docs = loader.load()

print(f"Documenti/elementi caricati: {len(docs)}")
for i, d in enumerate(docs[:5], start=1):
    print(f"\n--- DOC {i} ---")
    print(d.page_content[:400])
    print(d.metadata)
