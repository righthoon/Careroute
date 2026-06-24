"""
api.py -- FastAPI 서버

엔드포인트:
  POST /ocr                이미지 -> OCR 약품명 추출
  POST /review             약품명 목록(단일/다중 봉투 + 과 정보) -> DUR 리뷰
  POST /full-check         약봉투 이미지 여러 장 -> OCR + DUR 리뷰 + 저장
  GET  /status             서버 및 DB 로딩 상태
  GET  /patients           저장된 전체 환자 목록 (요약)
  GET  /patients/high-risk 병용금기(HIGH) 환자만
  GET  /patients/{id}      특정 환자 기록
  GET  /summary            전체 통계
  GET  /export/json        전체 데이터셋 JSON 다운로드
"""

import threading
import uvicorn
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated, List, Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from config import DATASET_DIR
from part1_ocr import extract_drug_names
from part2_dur_review import create_db, DURReviewer
from part3_dataset import DatasetManager


# -- 앱 초기화 --------------------------------------------------------------

_db = create_db()
_reviewer: DURReviewer | None = None
_dm: DatasetManager | None = None
_db_ready = False
_db_error: str | None = None


def _load_db_background():
    """DB를 백그라운드 스레드에서 로드 (서버 즉시 응답 가능하게)"""
    global _reviewer, _db_ready, _db_error
    try:
        _db.load()
        _reviewer = DURReviewer(db=_db)
        _db_ready = True
        print("✅ DUR DB 로드 완료. 서버 완전히 준비됨.")
    except Exception as e:
        _db_error = str(e)
        print("❌ DUR DB 로드 실패: " + str(e))


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _dm
    _dm = DatasetManager()
    # DB 로딩을 백그라운드 스레드로 실행 (서버는 즉시 시작)
    t = threading.Thread(target=_load_db_background, daemon=True)
    t.start()
    print("서버 시작 완료. DUR DB 백그라운드 로딩 중...")
    yield


app = FastAPI(
    title="약봉투 OCR + DUR 리뷰 API",
    version="1.1.0",
    description=(
        "약봉투 이미지 OCR 및 DUR 규칙 기반 약물 리뷰 API\n\n"
        "**주의**: 서버 시작 직후 `/status`에서 DB 로딩 완료 여부를 확인하세요.\n"
        "첫 실행 시 최대 30초, 이후 재시작은 캐시로 수 초면 완료됩니다."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# -- DB 준비 상태 가드 -------------------------------------------------------

def _require_db():
    if _db_error:
        raise HTTPException(status_code=500, detail="DB 로드 실패: " + _db_error)
    if not _db_ready:
        raise HTTPException(
            status_code=503,
            detail="DUR DB 로딩 중입니다. /status 엔드포인트로 진행 상황을 확인하세요.",
        )


# -- Pydantic 스키마 ---------------------------------------------------------

class ReviewRequest(BaseModel):
    drug_names: Optional[List[str]] = None
    drug_lists: Optional[List[List[str]]] = None
    departments: Optional[List[Optional[str]]] = None
    patient_age: Optional[int] = None
    patient_id: Optional[str] = None


class AlertOut(BaseModel):
    alert_type: str
    severity: str
    drugs: List[str]
    detail: str
    matched_product: str
    extra: dict


class ReviewResponse(BaseModel):
    patient_id: Optional[str]
    drug_names: List[str]
    alert_count: int
    alerts: List[AlertOut]
    report: str


# -- 헬퍼 -------------------------------------------------------------------

def _save_upload(upload: UploadFile) -> Path:
    tmp = DATASET_DIR / "tmp_uploads"
    tmp.mkdir(exist_ok=True)
    dest = tmp / upload.filename
    dest.write_bytes(upload.file.read())
    return dest


# -- 엔드포인트 --------------------------------------------------------------

@app.get("/status", summary="서버 및 DB 로딩 상태 확인")
async def status():
    """서버 시작 후 DB가 아직 로딩 중인지 확인합니다."""
    return {
        "server": "running",
        "db_ready": _db_ready,
        "db_error": _db_error,
        "message": (
            "준비 완료" if _db_ready
            else ("DB 로드 실패: " + _db_error if _db_error else "DB 로딩 중...")
        ),
    }


@app.post("/ocr", summary="이미지 -> OCR 약품명 추출")
async def ocr_endpoint(file: UploadFile = File(...)):
    img_path = _save_upload(file)
    try:
        result = extract_drug_names(img_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail="OCR 실패: " + str(e))
    finally:
        img_path.unlink(missing_ok=True)
    return result


@app.post("/review", response_model=ReviewResponse, summary="약품명 목록 -> DUR 리뷰")
async def review_endpoint(req: ReviewRequest):
    """
    다중 봉투 + 과 정보 (권장):
    { "drug_lists": [["약A","약B"], ["약A","약C"]], "departments": ["내과","정형외과"], "patient_age": 70 }

    단일 봉투 (하위 호환):
    { "drug_names": ["약A","약B"], "patient_age": 70 }
    """
    _require_db()
    if req.drug_lists:
        input_for_review = req.drug_lists
        all_drugs = [d for env in req.drug_lists for d in env]
    elif req.drug_names:
        input_for_review = req.drug_names
        all_drugs = req.drug_names
    else:
        raise HTTPException(status_code=422, detail="drug_names 또는 drug_lists 중 하나는 필수입니다.")

    alerts = _reviewer.review(input_for_review, patient_age=req.patient_age,
                              departments=req.departments)
    report = _reviewer.format_report(alerts)

    if req.patient_id:
        _dm.save_review(patient_id=req.patient_id, drug_candidates=all_drugs, alerts=alerts)

    return ReviewResponse(
        patient_id=req.patient_id,
        drug_names=all_drugs,
        alert_count=len(alerts),
        alerts=[AlertOut(**a.to_dict()) for a in alerts],
        report=report,
    )


@app.post(
    "/full-check",
    summary="약봉투 사진(여러 장) -> OCR + DUR 리뷰 + 저장",
    openapi_extra={
        "requestBody": {
            "required": True,
            "content": {
                "multipart/form-data": {
                    "schema": {
                        "type": "object",
                        "required": ["files"],
                        "properties": {
                            "files": {
                                "type": "array",
                                "items": {"type": "string", "format": "binary"},
                                "description": "약봉투 이미지 파일들 (여러 장 가능)",
                            },
                            "patient_id": {"type": "string", "default": "unknown"},
                            "patient_age": {"type": "integer"},
                        },
                    }
                }
            },
        }
    },
)
async def full_check_endpoint(
    files: List[UploadFile] = File(...),
    patient_id: Annotated[str, Form()] = "unknown",
    patient_age: Annotated[Optional[int], Form()] = None,
):
    _require_db()
    envelope_results = []
    drug_lists = []
    saved_paths = []
    extracted_departments = []

    for f in files:
        img_path = _save_upload(f)
        saved_paths.append(img_path)
        try:
            ocr_result = extract_drug_names(img_path)
        except Exception as e:
            for p in saved_paths:
                p.unlink(missing_ok=True)
            raise HTTPException(status_code=500, detail="OCR 실패 (" + f.filename + "): " + str(e))
        dept = ocr_result.get("department")
        envelope_results.append({
            "filename": f.filename,
            "department": dept,
            "drug_candidates": ocr_result["drug_candidates"],
        })
        drug_lists.append(ocr_result["drug_candidates"])
        extracted_departments.append(dept)

    for p in saved_paths:
        p.unlink(missing_ok=True)

    all_drugs = [d for env in drug_lists for d in env]
    alerts = _reviewer.review(drug_lists, patient_age=patient_age,
                              departments=extracted_departments)
    report = _reviewer.format_report(alerts)

    _dm.save_review(
        patient_id=patient_id,
        drug_candidates=all_drugs,
        alerts=alerts,
        image_path=", ".join(f.filename for f in files),
    )

    return {
        "patient_id": patient_id,
        "envelope_count": len(files),
        "envelopes": envelope_results,
        "all_drug_candidates": all_drugs,
        "alert_count": len(alerts),
        "alerts": [a.to_dict() for a in alerts],
        "report": report,
    }


@app.get("/patients", summary="저장된 전체 환자 목록")
async def get_patients():
    df = _dm.load()
    if df.empty:
        return []
    return (
        df.groupby("patient_id")
        .agg(
            last_recorded=("recorded_at", "max"),
            total_alerts=("alert_type", lambda x: (x != "없음").sum()),
            high_risk=("severity", lambda x: (x == "HIGH").any()),
        )
        .reset_index()
        .to_dict(orient="records")
    )


@app.get("/patients/high-risk", summary="병용금기(HIGH) 환자만 조회")
async def get_high_risk():
    df = _dm.get_high_risk_patients()
    return df.to_dict(orient="records")


@app.get("/patients/{patient_id}", summary="특정 환자 기록 조회")
async def get_patient(patient_id: str):
    df = _dm.get_patient(patient_id)
    if df.empty:
        raise HTTPException(status_code=404, detail="환자 " + patient_id + " 기록 없음")
    return df.to_dict(orient="records")


@app.get("/summary", summary="전체 통계")
async def get_summary():
    return _dm.summary()


@app.get("/export/json", summary="전체 데이터셋 JSON 다운로드")
async def export_json():
    json_path = _dm.export_json()
    return FileResponse(path=json_path, media_type="application/json",
                        filename="patient_drug_review.json")


# -- 실행 -------------------------------------------------------------------

if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
