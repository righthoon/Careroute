"""
FastAPI 백엔드 서버
- 방문 우선순위 API
- 챗봇 API
RunPod에서 실행, Vercel 프론트에서 호출
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from contextlib import asynccontextmanager
import uvicorn

from model_loader import load_model
from patient_data import PatientData, compute_all_stats
from visit_priority import compute_visit_priority, generate_priority_comment, run_priority_pipeline
from chatbot import PatientChatbot

# ─────────────────────────────────────────────
# 1. 모델 전역 로드 (서버 시작할 때 한 번만)
# ─────────────────────────────────────────────

tokenizer = None
model = None
chatbot_sessions = {}  # patient_id → PatientChatbot

@asynccontextmanager
async def lifespan(app: FastAPI):
    global tokenizer, model
    print("[INFO] 모델 로딩 중...")
    tokenizer, model = load_model()
    print("[INFO] 서버 준비 완료")
    yield
    print("[INFO] 서버 종료")

app = FastAPI(title="환자 관리 SLM API", lifespan=lifespan)

# CORS 설정 (Vercel 프론트에서 호출 허용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 배포 시 Vercel 도메인으로 교체
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────────
# 2. 요청/응답 스키마 정의
# ─────────────────────────────────────────────

class PatientRequest(BaseModel):
    """프론트에서 넘겨주는 환자 데이터"""
    patient_id: str
    name: str
    age: int
    gender: str
    diagnosis: list[str]

    bp_systolic: list[float]
    bp_diastolic: list[float]
    bp_timestamps: list[str]

    glucose: list[float] = []
    glucose_timestamps: list[str] = []

    medication_scheduled: int
    medication_taken: int
    medications: list[str] = []

    last_visit_date: Optional[str] = None
    visit_cycle_days: int = 30
    last_data_timestamp: Optional[str] = None

    is_infectious: bool = False
    infectious_disease: Optional[str] = None


class ChatRequest(BaseModel):
    """챗봇 메시지 요청"""
    patient_id: str
    message: str


class ChatResetRequest(BaseModel):
    """챗봇 대화 초기화 요청"""
    patient_id: str


# ─────────────────────────────────────────────
# 3. 유틸: 요청 → PatientData 변환
# ─────────────────────────────────────────────

def request_to_patient(req: PatientRequest) -> PatientData:
    return PatientData(
        patient_id=req.patient_id,
        name=req.name,
        age=req.age,
        gender=req.gender,
        diagnosis=req.diagnosis,
        bp_systolic=req.bp_systolic,
        bp_diastolic=req.bp_diastolic,
        bp_timestamps=req.bp_timestamps,
        glucose=req.glucose,
        glucose_timestamps=req.glucose_timestamps,
        medication_scheduled=req.medication_scheduled,
        medication_taken=req.medication_taken,
        medications=req.medications,
        last_visit_date=req.last_visit_date,
        visit_cycle_days=req.visit_cycle_days,
        last_data_timestamp=req.last_data_timestamp,
        is_infectious=req.is_infectious,
        infectious_disease=req.infectious_disease,
    )


# ─────────────────────────────────────────────
# 4. API 엔드포인트
# ─────────────────────────────────────────────

@app.get("/health")
def health_check():
    """서버 상태 확인 (프론트에서 연결 테스트용)"""
    return {"status": "ok", "model_loaded": model is not None}


@app.post("/priority")
def get_visit_priority(patients: list[PatientRequest]):
    """
    방문 우선순위 API
    - 여러 환자 데이터를 받아서 우선순위 순으로 정렬해서 반환
    - 감염병 환자는 맨 뒤
    
    요청: POST /priority
    [
        { patient_id, name, age, ... },
        { patient_id, name, age, ... },
    ]
    
    응답:
    [
        { rank, patient_id, name, priority, score, reasons, comment },
        ...
    ]
    """
    if model is None:
        raise HTTPException(status_code=503, detail="모델 로딩 중입니다. 잠시 후 다시 시도하세요.")

    try:
        patient_list = [request_to_patient(p) for p in patients]
        results = run_priority_pipeline(patient_list, tokenizer, model)

        # 순위 번호 추가
        ranked = []
        rank = 1
        for r in results:
            r["rank"] = rank if r["priority"] != "최하위" else None
            if r["priority"] != "최하위":
                rank += 1
            ranked.append(r)

        return ranked

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat")
def chat(req: ChatRequest, patient: PatientRequest):
    """
    챗봇 API
    - 환자 데이터 + 메시지를 받아서 SLM 답변 반환
    - 대화 이력 세션으로 유지 (patient_id 기준)
    
    요청: POST /chat
    {
        "patient_id": "PT-001",
        "message": "이 환자 혈압 어때요?",
        "patient": { ... }
    }
    
    응답:
    {
        "patient_id": "PT-001",
        "reply": "김영희 환자의 혈압은 ..."
    }
    """
    if model is None:
        raise HTTPException(status_code=503, detail="모델 로딩 중입니다. 잠시 후 다시 시도하세요.")

    try:
        # 세션 없으면 새로 생성, 있으면 재사용
        if req.patient_id not in chatbot_sessions:
            patient_data = request_to_patient(patient)
            chatbot_sessions[req.patient_id] = PatientChatbot(patient_data, tokenizer, model)

        bot = chatbot_sessions[req.patient_id]
        reply = bot.chat(req.message)

        return {"patient_id": req.patient_id, "reply": reply}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat/reset")
def reset_chat(req: ChatResetRequest):
    """
    챗봇 대화 초기화 API
    - 환자 전환할 때 호출
    
    요청: POST /chat/reset
    { "patient_id": "PT-001" }
    """
    if req.patient_id in chatbot_sessions:
        chatbot_sessions[req.patient_id].reset()
        return {"status": "ok", "message": f"{req.patient_id} 대화 초기화 완료"}
    return {"status": "ok", "message": "세션 없음"}


# ─────────────────────────────────────────────
# 5. 서버 실행
# ─────────────────────────────────────────────

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
