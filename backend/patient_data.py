"""
공통 데이터 구조 및 통계 계산 모듈
visit_priority.py, chatbot.py 양쪽에서 import해서 사용
"""

import numpy as np
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Optional


# ─────────────────────────────────────────────
# 1. 데이터 구조
# ─────────────────────────────────────────────

@dataclass
class PatientData:
    patient_id: str
    name: str
    age: int
    gender: str
    diagnosis: list[str]

    bp_systolic: list[float]
    bp_diastolic: list[float]
    bp_timestamps: list[str]

    glucose: list[float]
    glucose_timestamps: list[str]

    medication_scheduled: int
    medication_taken: int
    medications: list[str]

    last_visit_date: Optional[str] = None
    visit_cycle_days: int = 30
    last_data_timestamp: Optional[str] = None

    is_infectious: bool = False
    infectious_disease: Optional[str] = None


# ─────────────────────────────────────────────
# 2. 통계 계산
# ─────────────────────────────────────────────

def compute_bp_stats(systolic, diastolic):
    if not systolic:
        return {}
    s = np.array(systolic)
    d = np.array(diastolic)
    return {
        "sys_mean":      round(float(np.mean(s)), 1),
        "sys_std":       round(float(np.std(s)), 1),
        "sys_cv":        round(float(np.std(s) / np.mean(s) * 100), 1),
        "dia_mean":      round(float(np.mean(d)), 1),
        "high_bp_ratio": round(float(np.mean(s >= 140) * 100), 1),
        "low_bp_ratio":  round(float(np.mean(s < 90) * 100), 1),
        "max_sys":       round(float(np.max(s)), 1),
        "min_sys":       round(float(np.min(s)), 1),
    }


def compute_glucose_stats(glucose):
    if not glucose:
        return {}
    g = np.array(glucose)
    return {
        "mean":            round(float(np.mean(g)), 1),
        "std":             round(float(np.std(g)), 1),
        "tir":             round(float(np.mean((g >= 70) & (g <= 180)) * 100), 1),
        "high_ratio":      round(float(np.mean(g > 180) * 100), 1),
        "low_ratio":       round(float(np.mean(g < 70) * 100), 1),
        "max":             round(float(np.max(g)), 1),
        "min":             round(float(np.min(g)), 1),
        "estimated_hba1c": round(float((np.mean(g) + 46.7) / 28.7), 1),
    }


def compute_medication_adherence(scheduled, taken):
    if scheduled == 0:
        return {"rate": None, "level": "데이터없음"}
    rate = round(taken / scheduled * 100, 1)
    return {
        "rate":      rate,
        "level":     "양호" if rate >= 80 else ("주의" if rate >= 60 else "불량"),
        "scheduled": scheduled,
        "taken":     taken,
    }


def compute_visit_status(last_visit_date, cycle_days):
    if not last_visit_date:
        return {"days_since_visit": None, "overdue": True, "overdue_days": None}
    last = datetime.strptime(last_visit_date, "%Y-%m-%d")
    days = (datetime.now() - last).days
    return {
        "days_since_visit": days,
        "overdue":          days > cycle_days,
        "overdue_days":     max(0, days - cycle_days),
    }


def compute_data_transmission_status(last_ts):
    if not last_ts:
        return {"hours_since_last_data": None, "no_data_24h": True}
    hours = (datetime.now() - datetime.fromisoformat(last_ts)).total_seconds() / 3600
    return {"hours_since_last_data": round(hours, 1), "no_data_24h": hours >= 24}


def compute_all_stats(patient: PatientData) -> dict:
    return {
        "bp":              compute_bp_stats(patient.bp_systolic, patient.bp_diastolic),
        "glucose":         compute_glucose_stats(patient.glucose),
        "medication":      compute_medication_adherence(patient.medication_scheduled, patient.medication_taken),
        "visit":           compute_visit_status(patient.last_visit_date, patient.visit_cycle_days),
        "data_transmission": compute_data_transmission_status(patient.last_data_timestamp),
    }


# ─────────────────────────────────────────────
# 3. 샘플 데이터 (테스트용)
# ─────────────────────────────────────────────

def make_sample_patients() -> list[PatientData]:
    return [
        PatientData(
            patient_id="PT-001", name="김영희", age=72, gender="여",
            diagnosis=["고혈압", "제2형 당뇨"],
            bp_systolic=[158,162,145,170,155,168,152,160,175,148],
            bp_diastolic=[92,95,88,100,90,98,87,94,102,85],
            bp_timestamps=[(datetime.now()-timedelta(days=i)).isoformat() for i in range(10)],
            glucose=[185,210,165,230,195,220,175,200,240,180],
            glucose_timestamps=[(datetime.now()-timedelta(days=i)).isoformat() for i in range(10)],
            medication_scheduled=30, medication_taken=18,
            medications=["암로디핀 5mg","메트포르민 500mg"],
            last_visit_date=(datetime.now()-timedelta(days=45)).strftime("%Y-%m-%d"),
            visit_cycle_days=30,
            last_data_timestamp=(datetime.now()-timedelta(hours=26)).isoformat(),
        ),
        PatientData(
            patient_id="PT-002", name="박철수", age=65, gender="남",
            diagnosis=["고혈압"],
            bp_systolic=[128,132,125,130,127,133,129,131,126,134],
            bp_diastolic=[80,82,78,83,79,84,81,82,77,85],
            bp_timestamps=[(datetime.now()-timedelta(days=i)).isoformat() for i in range(10)],
            glucose=[], glucose_timestamps=[],
            medication_scheduled=30, medication_taken=28,
            medications=["로사르탄 50mg"],
            last_visit_date=(datetime.now()-timedelta(days=20)).strftime("%Y-%m-%d"),
            visit_cycle_days=30,
            last_data_timestamp=(datetime.now()-timedelta(hours=2)).isoformat(),
        ),
        PatientData(
            patient_id="PT-003", name="이순자", age=80, gender="여",
            diagnosis=["고혈압","결핵"],
            bp_systolic=[142,138,145,140,143],
            bp_diastolic=[88,85,90,87,89],
            bp_timestamps=[(datetime.now()-timedelta(days=i)).isoformat() for i in range(5)],
            glucose=[165,170,160,175,168],
            glucose_timestamps=[(datetime.now()-timedelta(days=i)).isoformat() for i in range(5)],
            medication_scheduled=30, medication_taken=25,
            medications=["암로디핀 5mg","이소니아지드 300mg"],
            last_visit_date=(datetime.now()-timedelta(days=10)).strftime("%Y-%m-%d"),
            visit_cycle_days=30,
            last_data_timestamp=(datetime.now()-timedelta(hours=1)).isoformat(),
            is_infectious=True, infectious_disease="결핵",
        ),
    ]
