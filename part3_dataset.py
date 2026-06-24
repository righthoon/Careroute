"""
part3_dataset.py — 노인 약물 복용 / DUR 리뷰 결과 데이터셋 저장
환자별 기록을 CSV에 누적 저장하고, 조회/내보내기 기능을 제공합니다.

저장 구조 (patient_drug_review.csv):
    patient_id, image_path, recorded_at,
    drug_candidates,          # OCR 추출 약품명 (|로 구분)
    alert_type,               # 경고 유형
    severity,                 # HIGH / MEDIUM / 없음
    drugs_involved,           # 해당 약물 (|로 구분)
    matched_product,
    detail                    # 상세정보

사용:
    from part3_dataset import DatasetManager
    dm = DatasetManager()
    dm.save_review(patient_id="P001", image_path="1.jpg",
                   drug_candidates=["타이레놀정"], alerts=[...])
    df = dm.load()
"""

import csv
import json
from datetime import datetime
from pathlib import Path

import pandas as pd

from config import PATIENT_CSV
from part2_dur_review import Alert


# ── 컬럼 정의 ─────────────────────────────────────────────────────────
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
]


class DatasetManager:
    """
    환자 약물 리뷰 결과를 CSV로 누적 저장·조회합니다.

    Parameters
    ----------
    csv_path : Path | str
        저장할 CSV 경로 (기본: config.PATIENT_CSV)
    """

    def __init__(self, csv_path: Path | str = PATIENT_CSV):
        self.csv_path = Path(csv_path)
        self._ensure_header()

    def _ensure_header(self):
        """CSV가 없으면 헤더 행을 먼저 씁니다."""
        if not self.csv_path.exists():
            with open(self.csv_path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.DictWriter(f, fieldnames=COLUMNS)
                writer.writeheader()

    # ── 저장 ─────────────────────────────────────────────────────────

    def save_review(
        self,
        patient_id: str,
        drug_candidates: list[str],
        alerts: list[Alert],
        image_path: str = "",
    ) -> int:
        """
        리뷰 결과를 CSV에 추가합니다.

        경고가 없으면 1행(alert_type='없음')으로, 있으면 경고별로 1행씩 저장.
        반환: 저장된 행 수
        """
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        drugs_str = "|".join(drug_candidates)
        rows = []

        if not alerts:
            rows.append({
                "patient_id": patient_id,
                "image_path": str(image_path),
                "recorded_at": now,
                "drug_candidates": drugs_str,
                "alert_count": 0,
                "alert_type": "없음",
                "severity": "-",
                "drugs_involved": "",
                "matched_product": "",
                "detail": "",
                "extra": "",
            })
        else:
            for a in alerts:
                rows.append({
                    "patient_id": patient_id,
                    "image_path": str(image_path),
                    "recorded_at": now,
                    "drug_candidates": drugs_str,
                    "alert_count": len(alerts),
                    "alert_type": a.alert_type,
                    "severity": a.severity,
                    "drugs_involved": "|".join(a.drugs),
                    "matched_product": a.matched_product,
                    "detail": a.detail,
                    "extra": json.dumps(a.extra, ensure_ascii=False),
                })

        with open(self.csv_path, "a", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=COLUMNS)
            writer.writerows(rows)

        return len(rows)

    # ── 조회 ─────────────────────────────────────────────────────────

    def load(self) -> pd.DataFrame:
        """전체 데이터셋을 DataFrame으로 반환"""
        return pd.read_csv(self.csv_path, encoding="utf-8-sig")

    def get_patient(self, patient_id: str) -> pd.DataFrame:
        """특정 환자의 기록만 반환"""
        df = self.load()
        return df[df["patient_id"] == patient_id].reset_index(drop=True)

    def get_high_risk_patients(self) -> pd.DataFrame:
        """병용금기(HIGH) 경고가 있는 환자만 반환"""
        df = self.load()
        return df[df["severity"] == "HIGH"].reset_index(drop=True)

    def summary(self) -> dict:
        """간단한 통계 요약"""
        df = self.load()
        return {
            "total_records": len(df),
            "unique_patients": df["patient_id"].nunique(),
            "high_risk_count": int((df["severity"] == "HIGH").sum()),
            "medium_risk_count": int((df["severity"] == "MEDIUM").sum()),
            "alert_type_counts": df["alert_type"].value_counts().to_dict(),
        }

    def export_json(self, output_path: Path | str | None = None) -> Path:
        """전체 데이터셋을 JSON으로 내보내기"""
        out = Path(output_path) if output_path else self.csv_path.with_suffix(".json")
        df = self.load()
        df.to_json(out, orient="records", force_ascii=False, indent=2)
        return out


# ── 테스트 ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from part2_dur_review import Alert

    # 임시 테스트용 CSV 경로
    from config import DATASET_DIR
    test_csv = DATASET_DIR / "test_dataset.csv"
    test_csv.unlink(missing_ok=True)

    dm = DatasetManager(csv_path=test_csv)

    # 케이스 1: 병용금기 경고
    alerts_1 = [
        Alert(
            alert_type="병용금기",
            severity="HIGH",
            drugs=["사이폴주", "로슈바정20mg"],
            detail="혈중농도 상승 및 근육병증/횡문근융해증 위험성 증가",
            matched_product="사이폴주(사이클로스포린) + 로슈바정20mg",
            extra={"성분명A": "cyclosporine", "성분명B": "rosuvastatin"},
        )
    ]
    saved = dm.save_review(
        patient_id="P001",
        drug_candidates=["사이폴주", "로슈바정20mg"],
        alerts=alerts_1,
        image_path="1.jpg",
    )
    print(f"P001 저장: {saved}행")

    # 케이스 2: 노인주의
    alerts_2 = [
        Alert(
            alert_type="노인주의(해열진통소염제)",
            severity="MEDIUM",
            drugs=["에이서캡슐"],
            detail="고령자는 중대한 위장관계 이상반응의 위험이 더 클 수 있음.",
            matched_product="에이서캡슐(아세클로페낙)",
            extra={"성분명": "aceclofenac"},
        )
    ]
    saved = dm.save_review(
        patient_id="P002",
        drug_candidates=["에이서캡슐", "타이레놀정"],
        alerts=alerts_2,
        image_path="2.jpg",
    )
    print(f"P002 저장: {saved}행")

    # 케이스 3: 정상
    saved = dm.save_review(
        patient_id="P003",
        drug_candidates=["아목시실린캡슐"],
        alerts=[],
        image_path="3.jpg",
    )
    print(f"P003 저장: {saved}행")

    print("\n=== 전체 요약 ===")
    summary = dm.summary()
    for k, v in summary.items():
        print(f"  {k}: {v}")

    print("\n=== P001 기록 ===")
    print(dm.get_patient("P001").to_string(index=False))

    print("\n=== 고위험 환자 ===")
    print(dm.get_high_risk_patients()[["patient_id", "alert_type", "detail"]].to_string(index=False))

    json_path = dm.export_json()
    print(f"\nJSON 내보내기: {json_path}")
    test_csv.unlink(missing_ok=True)
    json_path.unlink(missing_ok=True)
    print("테스트 완료 ✅")
