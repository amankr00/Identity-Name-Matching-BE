# ID Name Verification Backend

FastAPI backend that reads an Excel file with `Name` and `Aadhaar URL/Image`, performs OCR on each ID image, matches OCR text against the given name, and returns a new Excel file with match results.

## What It Does

- Accepts an Excel file upload.
- Reads each row from the active sheet.
- Uses OCR (Tesseract) to extract text/name from the ID image.
- Compares extracted text with the provided name using fuzzy matching.
- Returns a processed Excel file with:
- `Match Status` (`Matched` / `Not Matched`)
- Optional debug columns to explain each row outcome.

## How It Works

1. Parse the uploaded workbook with `openpyxl`.
2. For each row (starting from row 2):
3. Read `Column A` as reference name.
4. Resolve `Column B` image source from:
- Embedded image
- Plain URL
- Excel hyperlink
- `HYPERLINK(...)` formula URL
- Local path (if accessible on server machine)
5. Download/decode image bytes.
6. Preprocess image variants with Pillow (upscale, grayscale, contrast, threshold).
7. Run OCR (`pytesseract`) using multiple PSM modes.
8. Compute similarity score:
- Name vs extracted name
- Name vs full OCR text windows
9. Write result in output workbook.
10. Return output as downloadable `.xlsx`.

## Input Excel Format

- `Column A`: Name
- `Column B`: Aadhaar URL/Image source
- Row 1 can be headers (recommended).

## Output Excel Format

- `Column C`: `Match Status` (`Matched` or `Not Matched`)
- `Column D`: `Extracted Name` (if debug enabled)
- `Column E`: `Similarity Score` (if debug enabled)
- `Column F`: `Debug` reason (if debug enabled)
- `Column G`: `OCR Preview` (if debug enabled)

## API Endpoints

### `GET /api/health`

Returns service health and OCR engine status.

Example response:
```json
{
  "status": "ok",
  "ocr_engine": "tesseract"
}
