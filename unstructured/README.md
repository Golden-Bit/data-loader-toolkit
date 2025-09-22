# README — Unstructured API (self-hosted) con OCR su Docker (Ubuntu 24.04, Python 3.12)

Questa guida ti mostra **come buildare, avviare e testare** la tua immagine Docker dell’API Unstructured self-hosted con OCR, e come configurare i **parametri più importanti** (workers, parallel mode, limiti memoria, CORS, ecc.). Alla fine trovi esempi `curl`, Python (SDK e `requests`), e un esempio `docker-compose` con **coordinatore + pool di worker** per il parallelismo.

---

## Requisiti

* Docker / Docker Desktop
* (Facoltativo) Docker Compose v2
* Porta `8000` libera sulla macchina host
* PDF di test

---

## 1) Build dell’immagine

Assumendo che il tuo `Dockerfile` sia nella cartella corrente:

```bash
docker build -t unstructured-api:ubuntu24-py312-ocr .
```

Se sei su Windows PowerShell, **stesso comando**.

---

## 2) Avvio rapido (singola istanza)

### Linux / macOS

```bash
docker run --rm --name unstructured-api \
  -p 8000:8000 \
  -e UNSTRUCTURED_API_KEY="metti-una-chiave-robusta" \
  unstructured-api:ubuntu24-py312-ocr
```

### Windows PowerShell

```powershell
docker run --rm --name unstructured-api `
  -p 8000:8000 `
  -e UNSTRUCTURED_API_KEY="metti-una-chiave-robusta" `
  unstructured-api:ubuntu24-py312-ocr
```

#### Verifica healthcheck

```bash
curl -s http://localhost:8000/healthcheck
# {"healthcheck": "HEALTHCHECK STATUS: EVERYTHING OK!"}
```

> Se non ottieni `200 OK`, controlla i log:
> `docker logs -f unstructured-api`

---

## 3) Parametri d’avvio utili (ENV)

Puoi impostarli con `-e CHIAVE=valore` in `docker run` o nel `docker-compose`.

| Variabile                               |   Default | Descrizione                                                                                        |
| --------------------------------------- | --------: | -------------------------------------------------------------------------------------------------- |
| `UNSTRUCTURED_API_KEY`                  | *(vuoto)* | Se impostata, l’API richiede questo header: `unstructured-api-key`                                 |
| `ALLOW_ORIGINS`                         |       `*` | CORS; in produzione limita al tuo dominio                                                          |
| `UNSTRUCTURED_MEMORY_FREE_MINIMUM_MB`   |    `2048` | Se la RAM libera scende sotto questa soglia → `503` (anti OOM)                                     |
| `UNSTRUCTURED_HI_RES_MODEL_NAME`        |   `yolox` | Modello hi-res (`yolox` o `detectron2_onnx`)                                                       |
| `UNSTRUCTURED_PDF_HI_RES_MAX_PAGES`     |    `9999` | Limite di pagine in hi\_res                                                                        |
| `UNSTRUCTURED_PARALLEL_MODE_ENABLED`    |    `true` | Abilita parallel mode per PDF (vedi §6)                                                            |
| `UNSTRUCTURED_PARALLEL_MODE_THREADS`    |       `4` | Thread interni usati dal coordinatore                                                              |
| `UNSTRUCTURED_PARALLEL_MODE_SPLIT_SIZE` |       `1` | Pagine per chunk nelle chiamate parallele                                                          |
| `UNSTRUCTURED_PARALLEL_RETRY_ATTEMPTS`  |       `2` | Retry sui 5xx remoti in parallel mode                                                              |
| `UNSTRUCTURED_PARALLEL_MODE_URL`        | *(vuoto)* | **Obbligatorio** se `PARALLEL_MODE_ENABLED=true`: URL del **pool di worker** `/general/v0/general` |
| `DO_NOT_TRACK` / `SCARF_NO_ANALYTICS`   |    `true` | Disabilita telemetrie di base                                                                      |

> **Importante**: se abiliti il **Parallel Mode**, DEVI valorizzare `UNSTRUCTURED_PARALLEL_MODE_URL` (es. a un Nginx con dietro più worker). Se non lo imposti, l’API risponde con **500**: `Parallel mode enabled but no url set!`.

---

## 4) Log in tempo reale / livelli di log

Vedi log:

```bash
docker logs -f unstructured-api
```

Vuoi un log più verboso? Sovrascrivi il comando di default e passa flag a `uvicorn`:

```bash
docker run --rm --name unstructured-api \
  -p 8000:8000 \
  -e UNSTRUCTURED_API_KEY="metti-una-chiave-robusta" \
  unstructured-api:ubuntu24-py312-ocr \
  uvicorn prepline_general.api.app:app --host 0.0.0.0 --port 8000 --workers 1 --log-level debug --access-log
```

---

## 5) Test: chiamata `curl` all’endpoint `/general/v0/general`

> Attenzione al **percorso esatto**: `http://localhost:8000/general/v0/general`

### Linux / macOS

```bash
curl -X POST "http://localhost:8000/general/v0/general" \
  -H "unstructured-api-key: metti-una-chiave-robusta" \
  -H "Accept: application/json" \
  -F "files=@/percorso/al/file.pdf;type=application/pdf" \
  -F "strategy=hi_res" \
  -F "hi_res_model_name=yolox" \
  -F "coordinates=true" \
  -F "include_page_breaks=true" \
  -F "pdf_infer_table_structure=true" \
  -F "ocr_languages[]=ita" -F "ocr_languages[]=eng" \
  -F "languages[]=it" -F "languages[]=en" \
  -F "output_format=application/json"
```

### Windows PowerShell

```powershell
curl.exe -X POST "http://localhost:8000/general/v0/general" `
  -H "unstructured-api-key: metti-una-chiave-robusta" `
  -H "Accept: application/json" `
  -F "files=@C:\path\to\file.pdf;type=application/pdf" `
  -F "strategy=hi_res" `
  -F "hi_res_model_name=yolox" `
  -F "coordinates=true" `
  -F "include_page_breaks=true" `
  -F "pdf_infer_table_structure=true" `
  -F "ocr_languages[]=ita" -F "ocr_languages[]=eng" `
  -F "languages[]=it" -F "languages[]=en" `
  -F "output_format=application/json"
```

---

## 6) Modalità parallela (coordinatore + pool worker)

Per sfruttare il **Parallel Mode** sui PDF multi-pagina:

1. Alza **uno o più “worker”** (repliche identiche dell’immagine) **senza** `UNSTRUCTURED_PARALLEL_MODE_ENABLED`.
2. Metti davanti un **Nginx** (o bilanciatore) che espone `/general/v0/general` e instrada ai worker.
3. Avvia un **coordinatore** con:

   * `UNSTRUCTURED_PARALLEL_MODE_ENABLED=true`
   * `UNSTRUCTURED_PARALLEL_MODE_URL=http://nginx:8080/general/v0/general`
   * `UNSTRUCTURED_PARALLEL_MODE_THREADS` e `...SPLIT_SIZE` a piacere

### Esempio `docker-compose.yml` (minimo)

```yaml
version: "3.9"
services:
  # Pool di worker
  worker:
    image: unstructured-api:ubuntu24-py312-ocr
    deploy:
      replicas: 3               # 3 worker
    environment:
      UNSTRUCTURED_API_KEY: "metti-una-chiave-robusta"
      UNSTRUCTURED_PARALLEL_MODE_ENABLED: "false"
    # opzionale: persisti cache modelli
    volumes:
      - hf_cache:/root/.cache/huggingface
    expose:
      - "8000"

  # Nginx reverse proxy verso i worker
  nginx:
    image: nginx:alpine
    depends_on: [worker]
    ports:
      - "8080:8080"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro

  # Coordinatore
  coordinator:
    image: unstructured-api:ubuntu24-py312-ocr
    depends_on: [nginx]
    environment:
      UNSTRUCTURED_API_KEY: "metti-una-chiave-robusta"
      UNSTRUCTURED_PARALLEL_MODE_ENABLED: "true"
      UNSTRUCTURED_PARALLEL_MODE_URL: "http://nginx:8080/general/v0/general"
      UNSTRUCTURED_PARALLEL_MODE_THREADS: "4"
      UNSTRUCTURED_PARALLEL_MODE_SPLIT_SIZE: "1"
    ports:
      - "8000:8000"

volumes:
  hf_cache:
```

### `nginx.conf` di esempio

```nginx
events {}
http {
  upstream unstructured_workers {
    server worker:8000;  # docker DNS: tutti i replica condividono il nome
    # con swarm/k8s usare service discovery/ingress
  }

  server {
    listen 8080;

    location /general/v0/general {
      proxy_pass http://unstructured_workers;
      proxy_http_version 1.1;
      proxy_set_header Host $host;
      proxy_set_header Connection "";
      proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
  }
}
```

Avvio:

```bash
docker compose up -d
# invia le richieste al coordinatore: http://localhost:8000/general/v0/general
```

---

## 7) Persistenza cache modelli (facoltativo ma consigliato)

Unstructured/torch/transformers possono scaricare modelli al primo run. Per evitare download ripetuti, mappa la cache:

```bash
docker run --rm --name unstructured-api \
  -p 8000:8000 \
  -e UNSTRUCTURED_API_KEY="metti-una-chiave-robusta" \
  -v hf_cache:/root/.cache/huggingface \
  unstructured-api:ubuntu24-py312-ocr
```

In Compose hai già visto un volume `hf_cache`.

---

## 8) Client: Python con `requests`

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
from pathlib import Path
import requests

BASE_URL = "http://localhost:8000"
API_KEY  = "metti-una-chiave-robusta"
PDF_PATH = r"C:\path\to\file.pdf"

endpoint = f"{BASE_URL.rstrip('/')}/general/v0/general"
headers = {
    "unstructured-api-key": API_KEY,
    "Accept": "application/json",
}
data = {
    "strategy": "hi_res",
    "hi_res_model_name": "yolox",
    "coordinates": "true",
    "include_page_breaks": "true",
    "pdf_infer_table_structure": "true",
    "output_format": "application/json",
}
# liste stile form
data["ocr_languages[]"] = ["ita","eng"]
data["languages[]"] = ["it","en"]

with open(PDF_PATH, "rb") as fh:
    files = {"files": (Path(PDF_PATH).name, fh, "application/pdf")}
    r = requests.post(endpoint, headers=headers, data=data, files=files, timeout=180)

if r.status_code != 200:
    print(r.status_code, r.text)
    raise SystemExit(1)

payload = r.json()
Path(PDF_PATH).with_suffix(".json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
print("OK")
```

---

## 9) Client: Python con **SDK** `unstructured-client`

```python
from pathlib import Path
import json
from unstructured_client import UnstructuredClient
from unstructured_client.models import shared, operations

BASE_URL = "http://localhost:8000"
API_KEY  = "metti-una-chiave-robusta"
PDF_PATH = r"C:\path\to\file.pdf"

client = UnstructuredClient(server_url=BASE_URL, api_key_auth=API_KEY)

pdf = Path(PDF_PATH)
content = pdf.read_bytes()

params = shared.PartitionParameters(
    files=shared.Files(content=content, file_name=pdf.name),
    strategy=shared.Strategy.HI_RES,
    hi_res_model_name="yolox",
    output_format=shared.OutputFormat.APPLICATION_JSON,
    coordinates=True,
    include_page_breaks=True,
    pdf_infer_table_structure=True,
    ocr_languages=["ita", "eng"],
    languages=["it", "en"],
)

req = operations.PartitionRequest(partition_parameters=params)
resp = client.general.partition(request=req)  # SDK punta a /general/v0/general

out = pdf.with_suffix(".json")
out.write_text(json.dumps(resp.elements or [], ensure_ascii=False, indent=2), encoding="utf-8")
print("OK:", out)
```

> Se l’SDK lamenta versioni/modelli, aggiorna `unstructured-client` e verifica che il server esponga `/general/v0/general`.

---

## 10) Client: **LangChain** con `langchain-unstructured`

```python
from langchain_unstructured import UnstructuredLoader

FILE_PATH = r"C:\path\to\file.pdf"
API_URL   = "http://localhost:8000/general/v0/general"
API_KEY   = "metti-una-chiave-robusta"

loader = UnstructuredLoader(
    file_path=FILE_PATH,
    mode="elements",                 # "single" | "elements" | "paged"
    partition_via_api=True,
    url=API_URL,
    api_key=API_KEY,
    # parametri partition:
    strategy="hi_res",
    hi_res_model_name="yolox",
    coordinates=True,
    include_page_breaks=True,
    pdf_infer_table_structure=True,
    ocr_languages=["ita","eng"],
    languages=["it","en"],
    # chunking lato Unstructured (opzionale):
    chunking_strategy="by_title",    # "basic" | "by_title"
    combine_under_n_chars=2000,
    max_characters=4000,
    overlap=200,
    overlap_all=False,
)

docs = loader.load()
print("Docs:", len(docs))
```

> Se vedi 404 con un path “ripetuto”, assicurati che `url` sia **esattamente** `http://host:8000/general/v0/general` (niente doppioni come `/general/v0/general/general/v0/general`).

---

## 11) Troubleshooting

* **`ImportError: libGL.so.1`**: risolto nell’immagine — abbiamo installato `libgl1 libglib2.0-0 libsm6 libxrender1 libxext6`.
* **`Parallel mode enabled but no url set!`**: imposta `UNSTRUCTURED_PARALLEL_MODE_URL` **oppure** disabilita `UNSTRUCTURED_PARALLEL_MODE_ENABLED`.
* **`401 Unauthorized`**: header `unstructured-api-key` assente/errato.
* **`422` PDF invalid/encrypted**: file cifrato o corrotto. Decrittalo o fornisci un PDF valido.
* **Modelli lenti al primo run**: usa un volume per la cache (`~/.cache/huggingface`) per velocizzare i run successivi.
* **CORS**: in produzione limita `ALLOW_ORIGINS` a domini specifici.

---

## 12) Aggiungere lingue OCR

Nell’immagine sono installati: `eng`, `ita`, `deu`, `fra`, `spa`.
Vuoi altre lingue? Estendi il Dockerfile nel layer runtime:

```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr-pol tesseract-ocr-por tesseract-ocr-nld \
 && rm -rf /var/lib/apt/lists/*
```

Poi potrai usare `ocr_languages=["pol"]`, ecc.

---

## 13) Sicurezza & produzione

* Usa un `API_KEY` **robusto** e metti l’API dietro un reverse proxy **HTTPS**.
* Imposta `ALLOW_ORIGINS` al tuo/i dominio/i.
* Considera **rate-limit** a livello di proxy.
* Monitora RAM/CPU e regola `UNSTRUCTURED_MEMORY_FREE_MINIMUM_MB` e `PARALLEL_*`.

---

Fatto! Ora hai tutto per **buildare, avviare, testare e scalare** la tua Unstructured API self-hosted con OCR.
