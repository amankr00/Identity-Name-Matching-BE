# ID Name Verification Backend

FastAPI backend that reads an Excel file with `Name` + `Aadhaar URL/Image`, performs OCR on each ID image, compares the OCR result with the provided name, and returns a processed Excel file.

---

## Quick Navigation

- [What This Service Does](#what-this-service-does)
- [How Matching Works](#how-matching-works)
- [Input and Output Format](#input-and-output-format)
- [Run Locally](#run-locally-after-cloning)
- [API Endpoints](#api-endpoints)
- [Environment Variables](#environment-variables)
- [Troubleshooting](#troubleshooting)
- [Project Structure](#project-structure)

---

## What This Service Does

- Accepts Excel upload (`.xlsx`, `.xlsm`, `.xltx`, `.xltm`).
- Reads each row from the active sheet (starting row `2`).
- Uses OCR (`pytesseract`) to extract text from ID image.
- Calculates fuzzy similarity between input name and OCR output.
- Returns a new Excel file with:
  - `Match Status` (`Matched` / `Not Matched`)
  - Debug columns (optional) for diagnostics.

---

## How Matching Works

1. Read name from **Column A**.
2. Resolve image source from **Column B**.
3. Supported sources:
   - Embedded image in Excel cell
   - Plain image URL
   - Hyperlink cell
   - `=HYPERLINK("...","...")` formula
   - Local file path (if server can access it)
4. Download/decode image bytes.
5. Run OCR using multiple image preprocessing variants.
6. Compute similarity using two strategies:
   - Name vs extracted candidate name
   - Name vs full OCR text windows
7. Use best score and compare against `MATCH_THRESHOLD`.
8. Write result to output Excel.

---

## Input and Output Format

### Input Sheet

| Column | Meaning |
|---|---|
| A | Name |
| B | Aadhaar image source (URL/hyperlink/formula/embedded image/path) |

Row `1` can be headers.

### Output Sheet

| Column | Meaning |
|---|---|
| C | `Match Status` |
| D | `Extracted Name` (if debug enabled) |
| E | `Similarity Score` (if debug enabled) |
| F | `Debug` (if debug enabled) |
| G | `OCR Preview` (if debug enabled) |

---

## Run Locally (After Cloning)

### 1) Clone and enter backend folder

```bash
git clone <YOUR_REPO_URL>
cd <YOUR_REPO_NAME>/backend
```

### 2) Install Tesseract (required)

macOS:

```bash
brew install tesseract
```

Ubuntu/Debian:

```bash
sudo apt-get update
sudo apt-get install -y tesseract-ocr tesseract-ocr-eng tesseract-ocr-hin
```

### 3) Create virtual environment and install dependencies

Python `3.12` or `3.13` recommended.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If your default Python is too new and install fails, use Python 3.12:

```bash
brew install python@3.12
/opt/homebrew/bin/python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 4) Configure environment

```bash
cp .env.example .env
```

Recommended Aadhaar configuration (`.env`):

```env
MATCH_THRESHOLD=80
OUTPUT_DEBUG_COLUMNS=1
TESSERACT_LANG=eng+hin
```

### 5) Start backend

```bash
python -m uvicorn app.main:app --reload --port 8000
```

### 6) Verify health

```bash
curl http://localhost:8000/api/health
```

Expected response:

```json
{
  "status": "ok",
  "ocr_engine": "tesseract"
}
```

---

## API Endpoints

### `GET /api/health`

Returns backend and OCR status.

### `POST /api/process`

Processes Excel and returns processed Excel file.

- Content type: `multipart/form-data`
- Form field: `file`

Example:

```bash
curl -X POST "http://localhost:8000/api/process" \
  -F "file=@input.xlsx" \
  -o output_matched.xlsx
```

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `MATCH_THRESHOLD` | `90` | Similarity cutoff (0-100) |
| `OUTPUT_DEBUG_COLUMNS` | `1` | `1` include debug columns D-G, `0` disable |
| `TESSERACT_LANG` | `eng` | OCR language pack (`eng+hin` recommended for Aadhaar) |

---

## Troubleshooting

<details>
<summary><strong>All rows are <code>Not Matched</code></strong></summary>

1. Check OCR engine:
   ```bash
   curl http://localhost:8000/api/health
   ```
   Ensure `ocr_engine` is `tesseract`.
2. Lower threshold:
   - Set `MATCH_THRESHOLD=75` (or lower) in `.env`.
3. Keep debug enabled:
   - `OUTPUT_DEBUG_COLUMNS=1`
4. Inspect output `Debug` column.

</details>

<details>
<summary><strong>Debug column meanings</strong></summary>

- `matched`: score passed threshold.
- `url_fetch_error:*`: URL was not reachable.
- `url_non_image_content_type:*`: URL returned HTML/non-image.
- `ocr_engine_missing`: Tesseract not available.
- `ocr_no_text`: OCR could not read text from image.
- `name_not_detected:*`: text found but name extractor failed.
- `low_similarity:*`: OCR found text but score below threshold.

</details>

<details>
<summary><strong><code>uvicorn: command not found</code></strong></summary>

Run from activated virtual environment and use:

```bash
python -m uvicorn app.main:app --reload --port 8000
```

</details>

<details>
<summary><strong>Image URL opens webpage instead of image</strong></summary>

Use direct image URL if possible.  
If URL requires login/session cookies, server-side fetch will fail.

</details>

---

## Project Structure

```text
backend/
├── app/
│   ├── main.py           # FastAPI routes
│   ├── excel_service.py  # Excel parsing, image source resolution, matching
│   └── ocr_service.py    # OCR preprocessing + text/name extraction
├── requirements.txt
└── .env.example
```

---

## License

Internal project. Add your organization's license if needed.

