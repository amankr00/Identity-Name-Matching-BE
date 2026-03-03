ID Name Verification Backend
FastAPI backend that reads an Excel file with Name and Aadhaar URL/Image, performs OCR on each ID image, compares with the provided name, and returns a processed Excel file with match results.

What This Service Does
Accepts an Excel file upload.
Reads rows from the active worksheet.
Uses OCR (Tesseract) to read text from each ID image.
Compares OCR output with the input name using fuzzy matching.
Returns a new Excel with:
Match Status (Matched / Not Matched)
Optional debug columns for troubleshooting.
How It Works
Parse uploaded workbook with openpyxl.
For each row from row 2:
Read Column A as reference name.
Resolve image from Column B.
Supported image source types:
Embedded image in Excel cell.
Plain image URL.
Excel hyperlink cell.
=HYPERLINK("url","text") formula.
Local file path (if backend machine can access it).
Download/decode image bytes.
Preprocess image with Pillow (resize, grayscale, contrast, threshold variants).
Run OCR with Tesseract (pytesseract) using multiple page segmentation modes.
Compute final similarity score using:
Input name vs extracted name.
Input name vs OCR full-text windows.
Write result and debug info into output workbook.
Return processed .xlsx as download.
Input Excel Format
Column A: Name
Column B: Aadhaar URL or image source
Row 1 can contain headers (recommended)
Output Excel Format
Column C: Match Status
Column D: Extracted Name (if debug enabled)
Column E: Similarity Score (if debug enabled)
Column F: Debug (if debug enabled)
Column G: OCR Preview (if debug enabled)
API Endpoints
GET /api/health
Returns backend health and OCR engine status.

Example response:

{
  "status": "ok",
  "ocr_engine": "tesseract"
}
POST /api/process
Processes uploaded Excel and returns processed Excel.

Method: POST
Content type: multipart/form-data
Field name: file
Supported file extensions: .xlsx, .xlsm, .xltx, .xltm
Example:

curl -X POST "http://localhost:8000/api/process" \
  -F "file=@input.xlsx" \
  -o output_matched.xlsx
Run Locally (After Cloning)
1) Clone repo and open backend folder
git clone <YOUR_REPO_URL>
cd <YOUR_REPO_NAME>/backend
2) Install Tesseract (system dependency)
macOS:

brew install tesseract
Ubuntu/Debian:

sudo apt-get update
sudo apt-get install -y tesseract-ocr tesseract-ocr-eng tesseract-ocr-hin
3) Create virtual environment and install Python packages
Python 3.12 or 3.13 is recommended.

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
If your default Python causes dependency issues, use Python 3.12 explicitly:

brew install python@3.12
/opt/homebrew/bin/python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
4) Configure environment variables
cp .env.example .env
Recommended Aadhaar config in .env:

MATCH_THRESHOLD=80
OUTPUT_DEBUG_COLUMNS=1
TESSERACT_LANG=eng+hin
5) Start backend server
python -m uvicorn app.main:app --reload --port 8000
6) Verify backend
curl http://localhost:8000/api/health
Expected: ocr_engine should be tesseract.

Environment Variables
MATCH_THRESHOLD: Match cutoff score from 0 to 100.
OUTPUT_DEBUG_COLUMNS: 1 to include debug columns, 0 to disable.
TESSERACT_LANG: OCR language packs. Use eng+hin for Aadhaar cards with Hindi + English text.
Troubleshooting
If all rows are Not Matched, first check:
GET /api/health and confirm ocr_engine is tesseract.
If debug column shows url_fetch_error:*, URL is not reachable.
If debug shows url_non_image_content_type:*, URL is returning HTML/page, not image bytes.
If debug shows ocr_no_text, OCR could not read text from image.
If debug shows low_similarity:*, reduce MATCH_THRESHOLD (example 75).
Keep OUTPUT_DEBUG_COLUMNS=1 while tuning quality.
Project Structure
main.py: FastAPI routes and response handling.
excel_service.py: Excel parsing, image resolution, matching logic, output writing.
ocr_service.py: OCR preprocessing and name extraction.
requirements.txt: Python dependencies.
.env.example: Sample environment configuration.
License
Internal project. Add your organization’s license section if needed.
