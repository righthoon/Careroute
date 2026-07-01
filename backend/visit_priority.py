"""
방문 우선순위 모듈
- 규칙 기반으로 우선순위 점수/등급 계산
- SLM으로 간호사용 자연어 코멘트 생성
"""

import json
import re
import torch
from datetime import datetime
from patient_data import PatientData, compute_all_stats  # 공통 데이터 모듈


# ─────────────────────────────────────────────
# 1. 규칙 기반 우선순위 계산 (SLM 없이 동작)
# ─────────────────────────────────────────────

def compute_visit_priority(patient: PatientData, stats: dict) -> dict:
    """
    방문 우선순위 규칙:
      1. 감염병 환자 → 최하위
      2. 24시간 데이터 미전송 → 긴급
      3. 방문 주기 초과 → 점수 추가
      4. 혈압/혈당 위험 → 점수 추가
      5. 복약 불량 → 점수 추가
    """
    score = 0
    reasons = []

    if patient.is_infectious:
        return {
            "priority": "최하위",
            "score": -999,
            "reasons": [f"감염병 환자 ({patient.infectious_disease}) - 마지막 방문"],
        }

    if stats["data_transmission"]["no_data_24h"]:
        score += 100
        hours = stats["data_transmission"].get("hours_since_last_data", "?")
        reasons.append(f"데이터 미전송 {hours}시간")

    visit = stats["visit"]
    if visit.get("overdue"):
        overdue_d = visit.get("overdue_days", 0) or 0
        score += min(50, 20 + overdue_d)
        reasons.append(f"방문 주기 {overdue_d}일 초과")

    bp = stats.get("bp", {})
    if bp.get("high_bp_ratio", 0) >= 50:
        score += 30
        reasons.append(f"고혈압 측정 {bp['high_bp_ratio']}%")
    if bp.get("sys_cv", 0) >= 15:
        score += 20
        reasons.append(f"혈압 변동성 높음 (CV {bp['sys_cv']}%)")

    gl = stats.get("glucose", {})
    if gl.get("high_ratio", 0) >= 30:
        score += 25
        reasons.append(f"고혈당 {gl['high_ratio']}%")
    if gl.get("tir", 100) < 50:
        score += 20
        reasons.append(f"혈당 목표범위 미달 (TIR {gl['tir']}%)")

    med = stats.get("medication", {})
    if med.get("level") == "불량":
        score += 15
        reasons.append(f"복약 순응도 불량 ({med['rate']}%)")

    if score >= 100:
        priority = "긴급"
    elif score >= 60:
        priority = "높음"
    elif score >= 30:
        priority = "보통"
    else:
        priority = "낮음"

    return {"priority": priority, "score": score, "reasons": reasons}


# ─────────────────────────────────────────────
# 2. SLM으로 자연어 코멘트 생성
# ─────────────────────────────────────────────

PRIORITY_SYSTEM_PROMPT = """당신은 방문 간호사를 돕는 AI입니다.
환자의 방문 우선순위 근거를 바탕으로, 간호사가 바로 이해할 수 있는 짧은 한국어 코멘트를 작성하세요.
2~3문장, 수치 포함, 간결하게 작성하세요.
JSON 없이 자연어 문장만 출력하세요."""


def generate_priority_comment(patient: PatientData, priority: dict, tokenizer, model) -> str:
    """우선순위 근거 → SLM → 자연어 코멘트"""

    reasons_text = ", ".join(priority["reasons"]) if priority["reasons"] else "특이사항 없음"

    user_msg = (
        f"환자: {patient.name} ({patient.age}세 {patient.gender}성)\n"
        f"진단: {', '.join(patient.diagnosis)}\n"
        f"방문 우선순위: {priority['priority']}\n"
        f"근거: {reasons_text}\n\n"
        f"위 내용을 바탕으로 방문 간호사에게 전달할 코멘트를 작성하세요."
    )

    messages = [
        {"role": "system", "content": PRIORITY_SYSTEM_PROMPT},
        {"role": "user",   "content": user_msg},
    ]

    text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer([text], return_tensors="pt").to(model.device)

    with torch.no_grad():
        output_ids = model.generate(
            **inputs,
            max_new_tokens=150,
            temperature=0.3,
            do_sample=True,
            repetition_penalty=1.1,
            eos_token_id=tokenizer.eos_token_id,
            pad_token_id=tokenizer.eos_token_id,
        )

    new_ids  = output_ids[0][inputs["input_ids"].shape[-1]:]
    comment  = tokenizer.decode(new_ids, skip_special_tokens=True).strip()
    return comment


# ─────────────────────────────────────────────
# 3. 전체 환자 리스트 → 우선순위 정렬 + 코멘트
# ─────────────────────────────────────────────

def run_priority_pipeline(patients: list[PatientData], tokenizer, model) -> list[dict]:
    """
    1) 모든 환자 우선순위 계산
    2) SLM으로 코멘트 생성
    3) 우선순위 순으로 정렬해서 반환
    """
    results = []
    priority_order = {"긴급": 0, "높음": 1, "보통": 2, "낮음": 3, "최하위": 99}

    for patient in patients:
        stats    = compute_all_stats(patient)
        priority = compute_visit_priority(patient, stats)
        comment  = generate_priority_comment(patient, priority, tokenizer, model)

        results.append({
            "patient_id": patient.patient_id,
            "name":       patient.name,
            "priority":   priority["priority"],
            "score":      priority["score"],
            "reasons":    priority["reasons"],
            "comment":    comment,             # ← SLM이 생성한 자연어 코멘트
        })

    # 우선순위 높은 순 정렬 (감염병은 맨 뒤)
    results.sort(key=lambda r: (priority_order.get(r["priority"], 99), -r["score"]))
    return results


# ─────────────────────────────────────────────
# 테스트 실행
# ─────────────────────────────────────────────

if __name__ == "__main__":
    from patient_data import make_sample_patients
    from model_loader import load_model

    tokenizer, model = load_model()
    patients = make_sample_patients()
    results  = run_priority_pipeline(patients, tokenizer, model)

    print("\n📋 방문 우선순위 목록")
    print("=" * 50)
    for r in results:
        print(f"\n[{r['priority']}] {r['name']} ({r['patient_id']})")
        print(f"  근거: {', '.join(r['reasons'])}")
        print(f"  코멘트: {r['comment']}")
