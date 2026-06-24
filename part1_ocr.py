"""
part1_ocr.py — 약봉투 이미지 OCR
네이버 CLOVA OCR API로 이미지에서 텍스트를 추출하고,
약물 상품명 후보를 파싱해 반환합니다.

사용:
    from part1_ocr import extract_drug_names
    drugs = extract_drug_names("약봉투 사진/1.jpg")
"""

import json
import re
import time
import uuid
from pathlib import Path

import requests

from config import OCR_API_URL, OCR_SECRET

# ── 약품명 식별에 사용할 키워드/패턴 ──────────────────────────────────
# 약봉투에서 약품명 뒤에 오는 단위 접미사
DRUG_SUFFIX = re.compile(
    r"(정|캡슐|캡|시럽|액|주사|연고|크림|겔|패치|흡입|분말|과립|환|드롭|mg|ml|g)\b",
    re.IGNORECASE,
)

# 약품명 행을 유도하는 라벨 키워드
LABEL_KEYWORDS = ("약품명", "품명", "의약품명", "투약명", "약명")

# 약봉투에서 무시할 노이즈 패턴 (날짜, 용량지시, 병원명 등)
NOISE_PATTERN = re.compile(
    r"(복용|하루|아침|저녁|점심|식후|식전|취침|전|후|회|일|번|씩|개월|주일|\d{4}[-./]\d{1,2}[-./]\d{1,2})"
)


# ── OCR API 호출 ───────────────────────────────────────────────────────

def call_ocr_api(image_path: str | Path) -> dict:
    """네이버 CLOVA OCR API 호출 → raw JSON 반환"""
    image_path = Path(image_path)

    request_json = {
        "images": [{"format": image_path.suffix.lstrip(".").lower(), "name": "drug_bag"}],
        "requestId": str(uuid.uuid4()),
        "version": "V2",
        "timestamp": int(round(time.time() * 1000)),
    }

    with open(image_path, "rb") as f:
        response = requests.post(
            OCR_API_URL,
            headers={"X-OCR-SECRET": OCR_SECRET},
            data={"message": json.dumps(request_json).encode("UTF-8")},
            files=[("file", f)],
            timeout=30,
        )

    response.raise_for_status()
    return response.json()


def parse_ocr_text_blocks(ocr_result: dict) -> list[dict]:
    """
    OCR 결과에서 텍스트 블록 목록 추출.
    반환: [{"text": str, "x": float, "y": float, "height": float}, ...]
    """
    blocks = []
    for image in ocr_result.get("images", []):
        for field in image.get("fields", []):
            text = field.get("inferText", "").strip()
            if not text:
                continue
            verts = field.get("boundingPoly", {}).get("vertices", [])
            if verts:
                xs = [v.get("x", 0) for v in verts]
                ys = [v.get("y", 0) for v in verts]
                height = max(ys) - min(ys)
                x, y = min(xs), min(ys)
            else:
                x = y = height = 0
            blocks.append({"text": text, "x": x, "y": y, "height": height})
    return blocks


# ── 약품명 후보 파싱 ───────────────────────────────────────────────────

def extract_drug_candidates(blocks: list[dict]) -> list[str]:
    """
    텍스트 블록 목록에서 약품명 후보를 추출합니다.

    전략:
      1) "약품명:", "품명:" 등 라벨 바로 다음에 오는 텍스트
      2) 약품명 접미사(정, 캡슐, mg …)를 포함하는 텍스트
      3) 복용지시/날짜 노이즈가 없는 한글 텍스트
    """
    texts = [b["text"] for b in blocks]
    candidates: list[str] = []

    for i, text in enumerate(texts):
        # 전략 1: 라벨 키워드 바로 뒤 텍스트
        cleaned = re.sub(r"[:\s：]+", "", text)
        if any(kw in cleaned for kw in LABEL_KEYWORDS):
            # 같은 블록에서 라벨 이후 내용 파싱
            after = re.sub(r"(약품명|품명|의약품명|투약명|약명)[:\s：]*", "", text).strip()
            if after:
                candidates.append(after)
            # 다음 블록도 후보
            if i + 1 < len(texts):
                candidates.append(texts[i + 1].strip())
            continue

        # 전략 2: 약품명 접미사 포함
        if DRUG_SUFFIX.search(text):
            # 노이즈 필터
            if not NOISE_PATTERN.search(text):
                candidates.append(text.strip())

    return deduplicate(candidates)


def deduplicate(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result = []
    for item in items:
        norm = item.strip()
        if norm and norm not in seen:
            seen.add(norm)
            result.append(norm)
    return result


def normalize_drug_name(name: str) -> str:
    """
    검색용 정규화: 공백·괄호·용량 단위 제거, 소문자화.
    예) "타이레놀정 500mg" → "타이레놀정"
    """
    name = re.sub(r"\s+", "", name)               # 공백 제거
    name = re.sub(r"\(.*?\)", "", name)            # 괄호 내용 제거
    name = re.sub(r"\d+(\.\d+)?(mg|ml|g|mcg|ug|IU)", "", name, flags=re.IGNORECASE)
    return name.strip()


# ── 공개 API ───────────────────────────────────────────────────────────

def extract_drug_names(image_path: str | Path) -> dict:
    """
    이미지 경로를 받아 약물 상품명 후보 목록을 반환합니다.

    반환:
    {
        "image": str,
        "raw_texts": [str, ...],          # OCR 전체 텍스트
        "drug_candidates": [str, ...],    # 약품명 후보
        "normalized": [str, ...],         # 검색용 정규화 이름
    }
    """
    ocr_result = call_ocr_api(image_path)
    blocks     = parse_ocr_text_blocks(ocr_result)
    candidates = extract_drug_candidates(blocks)
    normalized = [normalize_drug_name(c) for c in candidates]

    return {
        "image": str(image_path),
        "raw_texts": [b["text"] for b in blocks],
        "drug_candidates": candidates,
        "normalized": normalized,
    }


# ── 테스트 ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from config import IMAGE_DIR

    test_images = sorted(IMAGE_DIR.glob("*.jpg"))
    if not test_images:
        print("약봉투 사진 폴더에 jpg 파일이 없습니다.")
    else:
        for img in test_images:
            print(f"\n{'='*50}")
            print(f"이미지: {img.name}")
            try:
                result = extract_drug_names(img)
                print(f"  전체 OCR 텍스트 ({len(result['raw_texts'])}개):")
                for t in result["raw_texts"]:
                    print(f"    · {t}")
                print(f"  약품명 후보 ({len(result['drug_candidates'])}개):")
                for d in result["drug_candidates"]:
                    print(f"    ✔ {d}")
                print(f"  정규화:")
                for n in result["normalized"]:
                    print(f"    → {n}")
            except Exception as e:
                print(f"  ERROR: {e}")
