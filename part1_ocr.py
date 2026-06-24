"""
part1_ocr.py -- 약봉투 이미지 OCR
네이버 CLOVA OCR API로 이미지에서 텍스트를 추출하고,
약물 상품명 후보와 처방 과(科)를 파싱해 반환합니다.

사용:
    from part1_ocr import extract_drug_names
    result = extract_drug_names("약봉투 사진/1.jpg")
    # result["drug_candidates"] : 약품명 후보 리스트
    # result["department"]      : 처방 과 (예: "종양혈액내과"), 없으면 None
"""

import json
import re
import time
import uuid
from pathlib import Path

import requests

from config import OCR_API_URL, OCR_SECRET

# ── 약품명 식별 패턴 ───────────────────────────────────────────────────
# 약품명 형태 접미사 (Python3에서 한글은 \w라 \b 제거)
DRUG_SUFFIX = re.compile(
    r"(정|캡슐|캡|시럽|주사|연고|크림|겔|패치|흡입|분말|과립|환|드롭|mg|ml|g)",
    re.IGNORECASE,
)
# "액"은 단독 처리: "~액" 형태 약품명 전용 (혈액/내과 오탐 방지)
DRUG_LIQUID = re.compile(r"[가-힣]{2,}액$")

# 약품명 행을 유도하는 라벨 키워드
LABEL_KEYWORDS = ("약품명", "품명", "의약품명", "투약명", "약명")

# 복용지시/날짜 노이즈
NOISE_PATTERN = re.compile(
    r"(복용|하루|아침식후|저녁식후|점심식후|식후|식전|취침|개월|주일"
    r"|\d{4}[-./]\d{1,2}[-./]\d{1,2}|^\d+$|^\d+씩$|^\d+회$|^\d+일$)"
)

# 약품명으로 오탐되는 의료기관/기타 단어
FALSE_POSITIVE_WORDS = (
    "병원", "의원", "약국", "과장", "병동",
    "센터", "클리닉", "의료원", "대학교", "대학병원",
)

# ── 처방 과(科) 식별 패턴 ──────────────────────────────────────────────
# "내과", "정형외과", "종양혈액내과" 등 의료 진료과 이름
# 조건: 한글로만 구성되고 "과"로 끝나는 단어, 최소 2자
DEPT_PATTERN = re.compile(r"^[가-힣]+과$")
DEPT_MIN_LEN = 2   # "내과"(2자) 포함


# ── OCR API 호출 ───────────────────────────────────────────────────────

def call_ocr_api(image_path: str | Path) -> dict:
    """네이버 CLOVA OCR API 호출 -> raw JSON 반환"""
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
    """OCR 결과에서 텍스트 블록 목록 추출."""
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


# ── 약품명 + 과 파싱 ───────────────────────────────────────────────────

def extract_drug_candidates(blocks: list[dict]) -> tuple[list[str], str | None]:
    """
    텍스트 블록에서 (약품명 후보 리스트, 처방 과) 를 추출합니다.

    처방 과 추출:
      - 한글로만 구성되고 "과"로 끝나는 텍스트 블록 (내과, 정형외과 등)
      - 여러 개 감지 시 가장 긴 이름(더 구체적) 선택
      - 해당 블록은 약품명 후보에서 제외

    약품명 후보 추출:
      1) "약품명:", "품명:" 등 라벨 바로 다음 텍스트
      2) 약품명 접미사(정, 캡슐, mg ...) 포함 텍스트
    """
    texts = [b["text"] for b in blocks]
    candidates: list[str] = []
    dept_candidates: list[str] = []

    for i, text in enumerate(texts):
        text_stripped = text.strip()

        # ── 처방 과 감지 (약품명 처리에서 제외) ────────────────────────
        if (DEPT_PATTERN.match(text_stripped)
                and len(text_stripped) >= DEPT_MIN_LEN):
            dept_candidates.append(text_stripped)
            continue

        # ── 전략 1: 라벨 키워드 바로 뒤 텍스트 ────────────────────────
        cleaned = re.sub(r"[:\s:]+", "", text_stripped)
        if any(kw in cleaned for kw in LABEL_KEYWORDS):
            after = re.sub(r"(약품명|품명|의약품명|투약명|약명)[:\s:]*", "", text_stripped).strip()
            if after:
                candidates.append(after)
            if i + 1 < len(texts):
                candidates.append(texts[i + 1].strip())
            continue

        # ── 전략 2: 약품명 접미사 + 최소 5자 + 필터 ───────────────────
        is_drug = (DRUG_SUFFIX.search(text_stripped) or DRUG_LIQUID.search(text_stripped))
        is_long_enough = len(text_stripped) >= 5
        is_noise = NOISE_PATTERN.search(text_stripped)
        is_false_positive = any(fp in text_stripped for fp in FALSE_POSITIVE_WORDS)

        if is_drug and is_long_enough and not is_noise and not is_false_positive:
            candidates.append(text_stripped)

    # 가장 긴(구체적인) 과 이름 선택
    department = max(dept_candidates, key=len) if dept_candidates else None

    return deduplicate(candidates), department


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
    검색용 정규화: 괄호/용량 제거 후 브랜드명만 추출.
    예) "판토록정40밀리그램(판토프라졸나트륨세" -> "판토록정"
    """
    name = re.sub(r"\s+", "", name)
    name = re.sub(r"\(.*", "", name)
    name = re.sub(r"_.*", "", name)
    name = re.sub(
        r"\d+(\.\d+)?(mg|ml|g|mcg|ug|IU|밀리그램|밀리그람|밀리리터|그람|그램)",
        "", name, flags=re.IGNORECASE
    )
    name = re.sub(r"[\d\.\,\;\:\*\#\@\!\?]+", "", name)
    return name.strip()


# ── 공개 API ───────────────────────────────────────────────────────────

def extract_drug_names(image_path: str | Path) -> dict:
    """
    이미지 경로를 받아 약물 상품명 후보 목록과 처방 과를 반환합니다.

    반환:
    {
        "image"          : str,
        "raw_texts"      : [str, ...],
        "drug_candidates": [str, ...],
        "normalized"     : [str, ...],
        "department"     : str | None,   # OCR로 추출한 처방 과
    }
    """
    ocr_result = call_ocr_api(image_path)
    blocks = parse_ocr_text_blocks(ocr_result)
    candidates, department = extract_drug_candidates(blocks)
    normalized = [normalize_drug_name(c) for c in candidates]

    return {
        "image": str(image_path),
        "raw_texts": [b["text"] for b in blocks],
        "drug_candidates": candidates,
        "normalized": normalized,
        "department": department,
    }


# ── 테스트 ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from config import IMAGE_DIR

    # 과 추출 로직 단위 테스트
    test_blocks = [
        {"text": "종양혈액내과", "x": 0, "y": 0, "height": 20},
        {"text": "신일폴산정_(1MG/1정)(정)", "x": 0, "y": 30, "height": 15},
        {"text": "판토록정40밀리그램(판토프라졸나트륨세", "x": 0, "y": 50, "height": 15},
        {"text": "아침식후", "x": 0, "y": 70, "height": 15},
        {"text": "정형외과", "x": 0, "y": 90, "height": 15},  # 과 여러 개일 때
    ]
    drugs, dept = extract_drug_candidates(test_blocks)
    print("=== 단위 테스트 ===")
    print("처방 과:", dept)
    print("약품명 후보:", drugs)
    assert dept == "종양혈액내과", "더 긴 과 이름 선택 실패"
    assert "신일폴산정_(1MG/1정)(정)" in drugs
    assert "아침식후" not in drugs
    print("PASS")

    # 실제 이미지 테스트
    test_images = sorted(IMAGE_DIR.glob("*.jpg"))
    if not test_images:
        print("\n약봉투 사진 폴더에 jpg 파일이 없습니다.")
    else:
        for img in test_images:
            print(f"\n{'='*50}")
            print(f"이미지: {img.name}")
            try:
                result = extract_drug_names(img)
                print(f"  처방 과: {result['department']}")
                print(f"  약품명 후보 ({len(result['drug_candidates'])}개):")
                for d in result["drug_candidates"]:
                    print(f"    ✔ {d}")
                print(f"  정규화:")
                for n in result["normalized"]:
                    print(f"    -> {n}")
            except Exception as e:
                print(f"  ERROR: {e}")
