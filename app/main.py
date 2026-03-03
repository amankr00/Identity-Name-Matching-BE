from io import BytesIO
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from .excel_service import process_workbook
from .ocr_service import NameOCRExtractor

app = FastAPI(
    title="ID Name Verification API",
    description="Upload an Excel sheet with Name + Image and receive Match Status output.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

ocr_probe = NameOCRExtractor()


@app.get("/api/health")
def health_check() -> dict[str, str]:
    return {"status": "ok", "ocr_engine": ocr_probe.engine_name}


@app.post("/api/process")
async def process_excel_file(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing file name.")

    if not file.filename.lower().endswith((".xlsx", ".xlsm", ".xltx", ".xltm")):
        raise HTTPException(
            status_code=400,
            detail="Only modern Excel formats are supported (.xlsx/.xlsm/.xltx/.xltm).",
        )

    source_bytes = await file.read()
    if not source_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    try:
        processed_bytes = process_workbook(source_bytes)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Processing failed: {exc}") from exc

    source_stem = Path(file.filename).stem
    output_name = f"{source_stem}_matched.xlsx"
    headers = {"Content-Disposition": f'attachment; filename="{output_name}"'}
    media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    return StreamingResponse(BytesIO(processed_bytes), media_type=media_type, headers=headers)
