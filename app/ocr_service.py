import os
import re
from dataclasses import dataclass
from io import BytesIO
from typing import Optional

from PIL import Image, ImageEnhance, ImageFilter, ImageOps


@dataclass
class OCRExtraction:
    engine_name: str
    raw_text: str
    extracted_name: str


class NameOCRExtractor:
    def __init__(self) -> None:
        self.engine_name = "none"
        self._pytesseract = None
        self._lang = os.getenv("TESSERACT_LANG", "eng")
        try:
            import pytesseract  # type: ignore

            _ = pytesseract.get_tesseract_version()
            self._pytesseract = pytesseract
            self.engine_name = "tesseract"
        except Exception:
            self.engine_name = "none"

    def extract_name(self, image_bytes: Optional[bytes]) -> str:
        return self.extract_details(image_bytes).extracted_name

    def extract_details(self, image_bytes: Optional[bytes]) -> OCRExtraction:
        if not image_bytes or self._pytesseract is None:
            return OCRExtraction(
                engine_name=self.engine_name,
                raw_text="",
                extracted_name="",
            )

        image = self._decode_image(image_bytes)
        if image is None:
            return OCRExtraction(
                engine_name=self.engine_name,
                raw_text="",
                extracted_name="",
            )

        text_blocks: list[str] = []
        seen = set()
        for image_variant in self._build_variants(image):
            for config in ("--oem 3 --psm 6", "--oem 3 --psm 11", "--oem 3 --psm 3"):
                ocr_text = self._run_ocr(image_variant, config)
                compact = ocr_text.strip()
                if compact and compact not in seen:
                    seen.add(compact)
                    text_blocks.append(compact)

        raw_text = "\n".join(text_blocks)
        extracted_name = self._extract_name_from_text(raw_text) if raw_text else ""
        return OCRExtraction(
            engine_name=self.engine_name,
            raw_text=raw_text,
            extracted_name=extracted_name,
        )

    def _decode_image(self, image_bytes: bytes) -> Optional[Image.Image]:
        try:
            return Image.open(BytesIO(image_bytes)).convert("RGB")
        except Exception:
            return None

    def _build_variants(self, image: Image.Image) -> list[Image.Image]:
        base = image.copy()
        upscaled = base.resize((base.width * 2, base.height * 2), Image.Resampling.LANCZOS)

        gray = ImageOps.grayscale(upscaled)
        autocontrast = ImageOps.autocontrast(gray, cutoff=1)
        sharpened = autocontrast.filter(ImageFilter.SHARPEN)
        boosted = ImageEnhance.Contrast(sharpened).enhance(1.7)
        binary = boosted.point(lambda px: 255 if px > 150 else 0)

        return [upscaled, gray, autocontrast, boosted, binary]

    def _run_ocr(self, image: Image.Image, config: str) -> str:
        if self._pytesseract is None:
            return ""
        try:
            return self._pytesseract.image_to_string(
                image,
                lang=self._lang,
                config=config,
            )
        except Exception:
            return ""

    def _extract_name_from_text(self, text: str) -> str:
        cleaned_lines = []
        for raw_line in text.splitlines():
            cleaned = re.sub(r"[^A-Za-z .'-]", " ", raw_line)
            cleaned = re.sub(r"\s+", " ", cleaned).strip()
            if cleaned:
                cleaned_lines.append(cleaned)

        if not cleaned_lines:
            return ""

        joined = "\n".join(cleaned_lines)
        label_patterns = [
            r"(?:full\s*name|name)\s*[:\-]\s*([A-Za-z .'-]{3,})",
            r"(?:given\s*name|holder\s*name|surname)\s*[:\-]\s*([A-Za-z .'-]{3,})",
        ]
        for pattern in label_patterns:
            match = re.search(pattern, joined, flags=re.IGNORECASE)
            if match:
                candidate = self._normalize_candidate(match.group(1))
                if self._is_likely_name(candidate):
                    return candidate

        for i, line in enumerate(cleaned_lines[:-1]):
            if re.fullmatch(
                r"(?:full\s*name|name|given\s*name|holder\s*name|surname)",
                line,
                flags=re.IGNORECASE,
            ):
                candidate = self._normalize_candidate(cleaned_lines[i + 1])
                if self._is_likely_name(candidate):
                    return candidate

        candidates = []
        for line in cleaned_lines:
            candidate = self._normalize_candidate(line)
            if self._is_likely_name(candidate):
                candidates.append(candidate)

        if not candidates:
            return ""

        return max(candidates, key=self._candidate_score)

    def _normalize_candidate(self, text: str) -> str:
        only_letters = re.sub(r"[^A-Za-z ]", " ", text).upper()
        return re.sub(r"\s+", " ", only_letters).strip()

    def _is_likely_name(self, text: str) -> bool:
        if not text:
            return False

        tokens = text.split()
        if len(tokens) < 2 or len(tokens) > 5:
            return False

        if len("".join(tokens)) < 4:
            return False

        blocked = self._blocked_tokens()
        if any(token in blocked for token in tokens):
            return False

        return True

    def _candidate_score(self, text: str) -> int:
        tokens = text.split()
        score = len("".join(tokens))
        if 2 <= len(tokens) <= 4:
            score += 8

        blocked = self._blocked_tokens()
        score -= sum(20 for token in tokens if token in blocked)
        return score

    def _blocked_tokens(self) -> set[str]:
        return {
            "ADDRESS",
            "AUTHORITY",
            "BIRTH",
            "CARD",
            "DOB",
            "DRIVING",
            "FATHER",
            "FEMALE",
            "GOVERNMENT",
            "ID",
            "IDENTITY",
            "LICENSE",
            "LICENCE",
            "MALE",
            "MOTHER",
            "NATIONALITY",
            "PASSPORT",
            "SEX",
            "SIGNATURE",
            "STATE",
            "VALID",
        }

