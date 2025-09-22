from pathlib import Path
import json

from unstructured_client import UnstructuredClient
from unstructured_client.models import shared, operations

BASE_URL = "http://localhost:8000"
API_KEY  = "metti-una-chiave-robusta"
PDF_PATH = r"C:\Users\info\Desktop\work_space\repositories\data-loader-toolkit\unstructured\test\data\ui_ux_readme.pdf"

client = UnstructuredClient(server_url=BASE_URL, api_key_auth=API_KEY)

pdf = Path(PDF_PATH)
content = pdf.read_bytes()

params = shared.PartitionParameters(
    files=shared.Files(content=content, file_name=pdf.name),  # <-- shared, non operations
    strategy=shared.Strategy.HI_RES,
    hi_res_model_name="yolox",
    output_format="application/json",      # oppure "text/csv"
    coordinates=True,
    include_page_breaks=True,
    pdf_infer_table_structure=True,
    ocr_languages=["ita", "eng"],          # Tesseract
    languages=["it", "en"],                # hint del testo
)

req = operations.PartitionRequest(partition_parameters=params)  # <-- request wrapper in operations
resp = client.general.partition(request=req)

# Salva output
out = pdf.with_suffix(".json")
out.write_text(json.dumps(resp.elements or [], ensure_ascii=False, indent=2), encoding="utf-8")
print(f"[OK] JSON salvato in {out}")
