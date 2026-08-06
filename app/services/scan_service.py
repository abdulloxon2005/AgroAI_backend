from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import UploadFile

from app.db.models import Scan as ScanResult
from app.core.exceptions import NotFoundException, BadRequestException, ForbiddenException
from app.core.config import settings
import google.generativeai as genai
from PIL import Image
from pathlib import Path
import uuid
import json
import io

genai.configure(api_key=settings.GEMINI_API_KEY)

UPLOAD_DIR = Path(settings.UPLOAD_DIR)
UPLOAD_DIR.mkdir(exist_ok=True)

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}


class ScanService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.model = genai.GenerativeModel(settings.GEMINI_MODEL)

    async def analyze_plant(self, file: UploadFile, user_id: int) -> ScanResult:
        if file.content_type not in ALLOWED_TYPES:
            raise BadRequestException(
                "Faqat JPEG, PNG yoki WebP formatdagi rasmlar qabul qilinadi"
            )

        content = await file.read()
        if len(content) > settings.MAX_FILE_SIZE:
            raise BadRequestException("Fayl hajmi 10MB dan oshmasligi kerak")

        # Save image
        filename = f"{uuid.uuid4()}.jpg"
        filepath = UPLOAD_DIR / filename

        image = Image.open(io.BytesIO(content))
        try:
            image = image.convert("RGB")
            image.thumbnail((1024, 1024))
            image.save(filepath, "JPEG", quality=85)
        finally:
            image.close()

        # Analyze with AgroAI
        prompt = """Sen AgroAI — ilmiy va tajribali sun'iy intellekt agronomisiz.
Ushbu rasmda ko'rsatilgan o'simlik bargini tahlil qil.
1. O'simlik va bargning O'ZBEKCHA VA LOTINCHA ILMIY NOMINI aniq ko'rsat (masalan: "Pomidor bargi (Solanum lycopersicum)", "G'o'za bargi (Gossypium hirsutum)", "Bodring bargi (Cucumis sativus)").
2. Kasallik bor-yo'qligini, turi va og'irlik darajasini aniqla.
3. FAQAT QUYIDAGI JSON formatda javob ber:
{
    "plant_name": "O'simlik va bargning aniq nomi (masalan: Pomidor bargi (Solanum lycopersicum))",
    "disease_name": "Kasallik nomi yoki null",
    "confidence": 0.95,
    "description": "Batafsil agronomik tahlil tavsifi",
    "treatment": "Davolash va parvarish choralari",
    "severity": "low/medium/high/none",
    "is_healthy": true/false
}
Faqat JSON formatda javob ber, boshqa matn yozma."""

        try:
            # Re-open image for AgroAI
            analysis_image = Image.open(filepath)
            try:
                response = await self.model.generate_content_async([prompt, analysis_image])
            finally:
                analysis_image.close()

            result_text = response.text.strip()

            # Clean markdown code blocks
            if result_text.startswith("```"):
                lines = result_text.split("\n")
                inner_lines = []
                started = False
                for line in lines:
                    if line.strip().startswith("```") and not started:
                        started = True
                        continue
                    if line.strip() == "```":
                        break
                    if started:
                        inner_lines.append(line)
                result_text = "\n".join(inner_lines).strip()

            analysis = json.loads(result_text)
        except Exception:
            analysis = {
                "plant_name": "Aniqlanmadi",
                "disease_name": "Tahlil xatosi",
                "confidence": 0.0,
                "description": "Rasmni tahlil qilishda xatolik yuz berdi",
                "treatment": "",
                "severity": "none",
                "is_healthy": False,
            }

        scan = ScanResult(
            user_id=user_id,
            image_url=f"/uploads/{filename}",
            plant_name=analysis.get("plant_name") or analysis.get("detected_crop_name", "Aniqlanmadi"),
            disease_name=analysis.get("disease_name"),
            confidence=analysis.get("confidence"),
            description=analysis.get("description"),
            treatment=analysis.get("treatment"),
            severity=analysis.get("severity"),
            is_healthy=analysis.get("is_healthy", False),
        )
        self.db.add(scan)
        await self.db.flush()
        await self.db.refresh(scan)

        return scan

    async def get_history(
        self, user_id: int, skip: int = 0, limit: int = 20
    ) -> list:
        result = await self.db.execute(
            select(ScanResult)
            .where(ScanResult.user_id == user_id)
            .order_by(ScanResult.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_scan(self, scan_id: int, user_id: int) -> ScanResult:
        result = await self.db.execute(
            select(ScanResult).where(ScanResult.id == scan_id)
        )
        scan = result.scalar_one_or_none()

        if not scan:
            raise NotFoundException("Skan natijasi topilmadi")
        if scan.user_id != user_id:
            raise ForbiddenException("Bu natijaga ruxsat yo'q")

        return scan

    async def delete_scan(self, scan_id: int, user_id: int):
        scan = await self.get_scan(scan_id, user_id)

        # Delete image file
        filepath = UPLOAD_DIR / scan.image_url.split("/")[-1]
        if filepath.exists():
            filepath.unlink()

        await self.db.delete(scan)
