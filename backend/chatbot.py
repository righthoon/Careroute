"""
간호사용 환자 챗봇 모듈
- 태블릿 현장에서 간호사가 환자에 대해 질문
- SLM이 환자 데이터 기반으로 답변 생성
- 멀티턴 대화 이력 관리
"""

import torch
from patient_data import PatientData, compute_all_stats


# ─────────────────────────────────────────────
# 1. 시스템 프롬프트
# ─────────────────────────────────────────────

def build_chatbot_system_prompt(patient: PatientData, stats: dict) -> str:
    """환자 데이터를 컨텍스트로 넣은 시스템 프롬프트"""

    bp  = stats.get("bp", {})
    gl  = stats.get("glucose", {})
    med = stats.get("medication", {})
    vis = stats.get("visit", {})
    dat = stats.get("data_transmission", {})

    context = f"""당신은 방문 간호사를 돕는 AI 어시스턴트입니다.
아래 환자 데이터를 바탕으로 간호사의 질문에 짧고 명확하게 한국어로 답하세요.
수치를 근거로 답하고, 모르는 건 "데이터 없음"이라고 하세요.

## 환자 정보
- 이름: {patient.name} | {patient.age}세 {patient.gender}성
- 진단: {', '.join(patient.diagnosis)}
- 복용약: {', '.join(patient.medications) if patient.medications else '없음'}

## 최근 혈압 ({len(patient.bp_systolic)}회 측정)
- 평균: {bp.get('sys_mean', '?')}/{bp.get('dia_mean', '?')} mmHg
- 변동성(CV): {bp.get('sys_cv', '?')}%
- 고혈압(≥140) 비율: {bp.get('high_bp_ratio', '?')}%
- 최고/최저: {bp.get('max_sys', '?')}/{bp.get('min_sys', '?')} mmHg

## 최근 혈당 ({len(patient.glucose)}회 측정)
- 평균: {gl.get('mean', '데이터없음')} mg/dL
- 목표범위내(TIR): {gl.get('tir', '?')}%
- 고혈당(>180) 비율: {gl.get('high_ratio', '?')}%
- 추정 HbA1c: {gl.get('estimated_hba1c', '?')}%

## 복약
- 순응도: {med.get('rate', '?')}% ({med.get('level', '?')})
- 예정 {med.get('scheduled', '?')}회 중 {med.get('taken', '?')}회 복약

## 방문
- 마지막 방문: {patient.last_visit_date or '미상'} ({vis.get('days_since_visit', '?')}일 전)
- 방문 주기 초과: {'예' if vis.get('overdue') else '아니오'}

## 데이터 전송
- 마지막 전송: {dat.get('hours_since_last_data', '?')}시간 전
- 감염병: {'예 - ' + (patient.infectious_disease or '') if patient.is_infectious else '아니오'}
"""
    return context


# ─────────────────────────────────────────────
# 2. 챗봇 세션 클래스
# ─────────────────────────────────────────────

class PatientChatbot:
    """
    환자 1명에 대한 챗봇 세션.
    대화 이력을 유지하면서 멀티턴 대화 지원.

    사용법:
        bot = PatientChatbot(patient, tokenizer, model)
        reply = bot.chat("이 환자 혈압 어때요?")
        reply = bot.chat("복약은요?")
        bot.reset()  # 대화 초기화
    """

    def __init__(self, patient: PatientData, tokenizer, model, max_history: int = 10):
        self.patient     = patient
        self.tokenizer   = tokenizer
        self.model       = model
        self.max_history = max_history  # 최대 유지할 대화 턴 수

        stats = compute_all_stats(patient)
        self.system_prompt = build_chatbot_system_prompt(patient, stats)
        self.history: list[dict] = []   # {"role": "user"/"assistant", "content": "..."}

    def chat(self, user_input: str, max_new_tokens: int = 200) -> str:
        """사용자 입력 → 모델 답변 반환"""

        # 대화 이력 추가
        self.history.append({"role": "user", "content": user_input})

        # 너무 길어지면 오래된 이력 제거 (시스템 프롬프트는 유지)
        if len(self.history) > self.max_history * 2:
            self.history = self.history[-(self.max_history * 2):]

        messages = [
            {"role": "system", "content": self.system_prompt},
            *self.history,
        ]

        text = self.tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        inputs = self.tokenizer([text], return_tensors="pt").to(self.model.device)

        with torch.no_grad():
            output_ids = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=0.4,
                do_sample=True,
                repetition_penalty=1.1,
                eos_token_id=self.tokenizer.eos_token_id,
                pad_token_id=self.tokenizer.eos_token_id,
            )

        new_ids = output_ids[0][inputs["input_ids"].shape[-1]:]
        reply   = self.tokenizer.decode(new_ids, skip_special_tokens=True).strip()

        # 모델 답변도 이력에 저장
        self.history.append({"role": "assistant", "content": reply})
        return reply

    def reset(self):
        """대화 이력 초기화 (환자 컨텍스트는 유지)"""
        self.history = []
        print(f"[INFO] {self.patient.name} 환자 대화 초기화")

    def switch_patient(self, new_patient: PatientData):
        """다른 환자로 전환"""
        self.patient = new_patient
        stats = compute_all_stats(new_patient)
        self.system_prompt = build_chatbot_system_prompt(new_patient, stats)
        self.history = []
        print(f"[INFO] 환자 전환: {new_patient.name}")


# ─────────────────────────────────────────────
# 3. 스트리밍 출력 (태블릿 응답 속도 개선용)
# ─────────────────────────────────────────────

def chat_stream(bot: PatientChatbot, user_input: str):
    """
    스트리밍 방식으로 토큰 하나씩 출력.
    태블릿에서 응답이 빠르게 보이는 효과.

    사용법:
        for token in chat_stream(bot, "혈압 어때요?"):
            print(token, end="", flush=True)
    """
    from transformers import TextIteratorStreamer
    from threading import Thread

    bot.history.append({"role": "user", "content": user_input})

    messages = [
        {"role": "system", "content": bot.system_prompt},
        *bot.history,
    ]

    text   = bot.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = bot.tokenizer([text], return_tensors="pt").to(bot.model.device)

    streamer = TextIteratorStreamer(bot.tokenizer, skip_prompt=True, skip_special_tokens=True)

    gen_kwargs = dict(
        **inputs,
        streamer=streamer,
        max_new_tokens=200,
        temperature=0.4,
        do_sample=True,
        repetition_penalty=1.1,
        eos_token_id=bot.tokenizer.eos_token_id,
        pad_token_id=bot.tokenizer.eos_token_id,
    )

    thread = Thread(target=bot.model.generate, kwargs=gen_kwargs)
    thread.start()

    full_reply = ""
    for token in streamer:
        full_reply += token
        yield token

    thread.join()
    bot.history.append({"role": "assistant", "content": full_reply})


# ─────────────────────────────────────────────
# 테스트 실행
# ─────────────────────────────────────────────

if __name__ == "__main__":
    from patient_data import make_sample_patients
    from model_loader import load_model

    tokenizer, model = load_model()
    patient = make_sample_patients()[0]   # 첫 번째 샘플 환자

    bot = PatientChatbot(patient, tokenizer, model)

    print(f"\n💬 {patient.name} 환자 챗봇 시작 (종료: 'quit')\n")

    # 일반 chat() 테스트
    test_questions = [
        "이 환자 혈압 상태 어때요?",
        "복약은 잘 하고 있나요?",
        "오늘 방문해야 하나요?",
    ]

    for q in test_questions:
        print(f"간호사: {q}")
        reply = bot.chat(q)
        print(f"AI: {reply}\n")

    # 스트리밍 테스트
    print("간호사: 혈당 요약해줘 (스트리밍)")
    print("AI: ", end="")
    for token in chat_stream(bot, "혈당 요약해줘"):
        print(token, end="", flush=True)
    print()
