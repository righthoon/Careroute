"""
part3_dataset.py — 노인 약물 복용 / DUR 리뷰 결과 데이터셋 저장

저장 구조 (patient_drug_review.csv / .json):
    patient_id, image_path, recorded_at,
    drug_candidates,   # OCR 추출 약품명 (|로 구분)
    alert_count,
    alert_type,        # 경고 유형
    severity,          # HIGH / MEDIUM / 없음
    drugs_involved,    # 해당 약물 (|로 구분)
    matched_product,
    detail,
    extra,             # 기타 메타 (JSON)
    성분명,            # 단일: 성분명 / 병용금기: 성분명A / 성분명B
    효능군             # 효능군중복일 때만 값 있음
"""

import csv
import json
from datetime import datetime
from pathlib import Path

import pandas as pd

from config import PATIENT_CSV
from part2_dur_review import Alert


COLUMNS = [
    "patient_id",
    "image_path",
    "recorded_at",
    "drug_candidates",
    "alert_count",
    "alert_type",
    "severity",
    "drugs_involved",
    "matched_product",
    "detail",
    "extra",
    "성분명",
    "효능군",
]


def _extract_성분명(extra: dict) -> str:
    if "성분명" in extra:
        return str(extra["성분명"])
    parts = [extra.get("성분명A", ""), extra.get("성분명B", "")]
    return " / ".join(p for p in parts if p and p not in ("nan", "NaN", "None", ""))


def _extract_효능군(extra: dict) -> str:
    return str(extra.get("효능군", "")) if extra.get("효능군") else ""


class DatasetManager:

    def __init__(self, csv_path: Path | str = PATIENT_CSV):
        self.csv_path = Path(csv_path)
        self._ensure_header()

    def _ensure_header(self):
        if not self.csv_path.exists():
            with open(self.csv_path, "w", newline="", encoding="utf-8-sig") as f:
                csv.DictWriter(f, fieldnames=COLUMNS).writeheader()
            return
        # 기존 파일 컬럼이 다르면 백업 후 재생성
        try:
            existing = pd.read_csv(
                self.csv_path, encoding="utf-8-sig", nrows=0
            ).columns.tolist()
        except Exception:
            existing = []
        if existing != COLUMNS:
            backup = self.csv_path.with_suffix(".bak.csv")
            self.csv_path.rename(backup)
            print("[part3] 컬럼 변경 감지 -> 기존 파일 백업: " + backup.name)
            with open(self.csv_path, "w", newline="", encoding="utf-8-sig") as f:
                csv.DictWriter(f, fieldnames=COLUMNS).writeheader()

    def save_review(
        self,
        patient_id: str,
        drug_candidates: list,
        alerts: list,
        image_path: str = "",
    ) -> int:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        drugs_str = "|".join(drug_candidates)
        rows = []

        if not alerts:
            rows.append({
                "patient_id":      patient_id,
                "image_path":      str(image_path),
                "recorded_at":     now,
                "drug_candidates": drugs_str,
                "alert_count":     0,
                "alert_type":      "없음",
                "severity":        "-",
                "drugs_involved":  "",
                "matched_product": "",
                "detail":          "",
                "extra":           "",
                "성분명":          "",
                "효능군":          "",
            })
        else:
            for a in alerts:
                rows.append({
                    "patient_id":      patient_id,
                    "image_path":      str(image_path),
                    "recorded_at":     now,
                    "drug_candidates": drugs_str,
                    "alert_count":     len(alerts),
                    "alert_type":      a.alert_type,
                    "severity":        a.severity,
                    "drugs_involved":  "|".join(a.drugs),
                    "matched_product": a.matched_product,
                    "detail":          a.detail,
                    "extra":           json.dumps(a.extra, ensure_ascii=False),
                    "성분명":          _extract_성분명(a.extra),
                    "효능군":          _extract_효능군(a.extra),
                })

        with open(self.csv_path, "a", newline="", encoding="utf-8-sig") as f:
            csv.DictWriter(f, fieldnames=COLUMNS).writerows(rows)

        return len(rows)

    def load(self) -> pd.DataFrame:
        return pd.read_csv(self.csv_path, encoding="utf-8-sig")

    def get_patient(self, patient_id: str) -> pd.DataFrame:
        df = self.load()
        return df[df["patient_id"] == patient_id].reset_index(drop=True)

    def get_high_risk_patients(self) -> pd.DataFrame:
        df = self.load()
        return df[df["severity"] == "HIGH"].reset_index(drop=True)

    def summary(self) -> dict:
        df = self.load()
        return {
            "total_records":     len(df),
            "unique_patients":   df["patient_id"].nunique(),
            "high_risk_count":   int((df["severity"] == "HIGH").sum()),
            "medium_risk_count": int((df["severity"] == "MEDIUM").sum()),
            "alert_type_counts": df["alert_type"].value_counts().to_dict(),
        }

    def export_json(self, output_path: Path | str | None = None) -> Path:
        out = Path(output_path) if output_path else self.csv_path.with_suffix(".json")
        df = self.load()
        df.to_json(out, orient="records", force_ascii=False, indent=2)
        return out
