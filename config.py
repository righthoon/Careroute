"""
config.py — 경로 및 API 설정 중앙 관리
모든 Part가 이 파일을 import해서 사용합니다.
"""

from pathlib import Path

# ── 기본 경로 ──────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent

DUR_DIR = (
    BASE_DIR
    / "건강보험심사평가원_의약품안전사용서비스(DUR) 의약품 목록_20260601 (1)"
    / "건강보험심사평가원_의약품안전사용서비스(DUR) 의약품 목록_202606"
)

CSV_ELDERLY       = DUR_DIR / "의약품안전사용서비스(DUR)_노인주의 품목리스트 2026.6.csv"
CSV_ANTIPYRETIC   = DUR_DIR / "의약품안전사용서비스(DUR)_노인주의(해열진통소염제) 품목리스트 2026.6.csv"
CSV_CONTRAINDICATED = DUR_DIR / "의약품안전사용서비스(DUR)_병용금기 품목리스트 2026.6.csv"

IMAGE_DIR  = BASE_DIR / "약봉투 사진"
DATASET_DIR = BASE_DIR / "dataset"
DATASET_DIR.mkdir(exist_ok=True)

PATIENT_CSV = DATASET_DIR / "patient_drug_review.csv"

# ── 네이버 CLOVA OCR API ───────────────────────────────────────────────
OCR_API_URL  = "https://sfwbi2tr26.apigw.ntruss.com/custom/v1/45209/aa4e0e33fcbd7898e2ae0ff9852a32fc2d818416b91a87b7db20d22d7189b4cc/general"
OCR_SECRET   = "TE9MUmZZbnJ1bmJyQ05jaFZIZE9WcktNeUF2elNBbU8="

# ── CSV 인코딩 ─────────────────────────────────────────────────────────
CSV_ENCODING = "cp949"
