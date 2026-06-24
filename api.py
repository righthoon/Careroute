"""
api.py — FastAPI 서버
JavaScript(또는 어떤 클라이언트)에서 HTTP로 호출합니다.

엔드포인트:
  POST /ocr                이미지 업로드 → OCR 약품명 추출
  POST /review             약품명 목록 → DUR 리뷰
  POST /full-check         이미지 업로드 → OCR + DUR 리뷰 + 데이터셋 저장
  GET  /patients           저장된 전체 환자 목록 (요약)
  GET  /patients/{id}      특정 환자 기록
  GET  /patients/high-risk 병용금기(HIGH) 환자만
  GET  /summary            전체 통계
  GET  /export/json        전체 데이터셋 JSON 다운로드

실행:
  pip install fastapi uvicorn python-multipart
  python api.py
  또는: uvicorn api:app --reload --port 8000
"""

import uvicorn
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from config import DATASET_DIR
from part1_ocr import extract_drug_names
from part2_dur_review import DURDatabase, DURReviewer
from part3_dataset import DatasetManager


# ── 앱 초기화 ──────────────────────────────────────────────────────────

# DUR DB는 서버 시작 시 1회만 로드
_db = DURDatabase()
_reviewer: DURReviewer | None = None
_dm: DatasetManager | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _reviewer, _dm
    _db.load()
    _reviewer = DURReviewer(db=_db)
    _dm = DatasetManager()
    print("✅ DUR DB 로드 완료. 서버 준비됨.")
    yield


app = FastAPI(
    title="약봉투 OCR + DUR 리뷰 API",
    version="1.0.0",
    description="약봉투 이미지 OCR 및 DUR 규칙 기반 약물 리뷰 API",
    lifespan=lifespan,
)

# CORS — 모든 origin 허용 (개발/해커톤 환경)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Pydantic 스키마 ────────────────────────────────────────────────────

class ReviewRequest(BaseModel):
    drug_names: list[str]
    patient_age: int | None = None
    patient_id: str | None = None


class AlertOut(BaseModel):
    alert_type: str
    severity: str
    drugs: list[str]
    detail: str
    matched_product: str
    extra: dict


class ReviewResponse(BaseModel):
    patient_id: str | None
    drug_names: list[str]
    alert_count: int
    alerts: list[AlertOut]
    report: str


# ── 헬퍼 ──────────────────────────────────────────────────────────────

def _save_upload(upload: UploadFile) -> Path:
    """업로드 파일을 임시 경로에 저장하고 Path 반환"""
    tmp = DATASET_DIR / "tmp_uploads"
    tmp.mkdir(exist_ok=True)
    dest = tmp / upload.filename
    dest.write_bytes(upload.file.read())
    return dest


# ── 엔드포인트 ─────────────────────────────────────────────────────────

@app.post("/ocr", summary="이미지 → OCR 약품명 추출")
async def ocr_endpoint(file: UploadFile = File(...)):
    """
    약봉투 이미지를 업로드하면 OCR로 텍스트를 추출하고
    약품명 후보 목록을 반환합니다.
    """
    img_path = _save_upload(file)
    try:
        result = extract_drug_names(img_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR 실패: {e}")
    finally:
        img_path.unlink(missing_ok=True)
    return result


@app.post("/review", response_model=ReviewResponse, summary="약품명 목록 → DUR 리뷰")
async def review_endpoint(req: ReviewRequest):
    """
    약품명 목록과 환자 나이를 입력하면 DUR 규칙 기반 경고를 반환합니다.

    - **병용금기**: severity=HIGH, 약물 쌍 + 상세정보
    - **노인주의**: severity=MEDIUM, 개별 약물 + 약품상세정보
    - **노인주의(해열진통소염제)**: severity=MEDIUM, 별도 카테고리
    """
    alerts = _reviewer.review(req.drug_names, patient_age=req.patient_age)
    report = _reviewer.format_report(alerts)

    if req.patient_id:
        _dm.save_review(
            patient_id=req.patient_id,
            drug_candidates=req.drug_names,
            alerts=alerts,
        )

    return ReviewResponse(
        patient_id=req.patient_id,
        drug_names=req.drug_names,
        alert_count=len(alerts),
        alerts=[AlertOut(**a.to_dict()) for a in alerts],
        report=report,
    )


@app.post("/full-check", summary="이미지 업로드 → OCR + DUR 리뷰 + 저장")
async def full_check_endpoint(
    file: UploadFile = File(...),
    patient_id: Annotated[str, Form()] = "unknown",
    patient_age: Annotated[int | None, Form()] = None,
):
    """
    이미지를 업로드하면 OCR → DUR 리뷰 → 데이터셋 저장을 한 번에 처리합니다.
    """
    img_path = _save_upload(file)
    try:
        ocr_result = extract_drug_names(img_path)
    except Exception as e:
        img_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=f"OCR 실패: {e}")

    drug_names = ocr_result["drug_candidates"]
    alerts = _reviewer.review(drug_names, patient_age=patient_age)
    report = _reviewer.format_report(alerts)

    _dm.save_review(
        patient_id=patient_id,
        drug_candidates=drug_names,
        alerts=alerts,
        image_path=file.filename,
    )

    img_path.unlink(missing_ok=True)

    return {
        "patient_id": patient_id,
        "ocr": ocr_result,
        "drug_candidates": drug_names,
        "alert_count": len(alerts),
        "alerts": [a.to_dict() for a in alerts],
        "report": report,
    }


@app.get("/patients", summary="저장된 전체 환자 목록")
async def get_patients():
    """환자 ID별 마지막 기록 시간과 경고 건수를 반환합니다."""
    df = _dm.load()
    if df.empty:
        return []
    result = (
        df.groupby("patient_id")
        .agg(
            last_recorded=("recorded_at", "max"),
            total_alerts=("alert_type", lambda x: (x != "없음").sum()),
            high_risk=("severity", lambda x: (x == "HIGH").any()),
        )
        .reset_index()
        .to_dict(orient="records")
    )
    return result


@app.get("/patients/high-risk", summary="병용금기(HIGH) 환자만 조회")
async def get_high_risk():
    df = _dm.get_high_risk_patients()
    return df.to_dict(orient="records")


@app.get("/patients/{patient_id}", summary="특정 환자 기록 조회")
async def get_patient(patient_id: str):
    df = _dm.get_patient(patient_id)
    if df.empty:
        raise HTTPException(status_code=404, detail=f"환자 {patient_id} 기록 없음")
    return df.to_dict(orient="records")


@app.get("/summary", summary="전체 통계")
async def get_summary():
    return _dm.summary()


@app.get("/export/json", summary="전체 데이터셋 JSON 다운로드")
async def export_json():
    json_path = _dm.export_json()
    return FileResponse(
        path=json_path,
        media_type="application/json",
        filename="patient_drug_review.json",
    )


# ── 실행 ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
