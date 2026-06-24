"""
part2_dur_review.py -- DUR Rule-based 약물 리뷰
세 가지 규칙을 검사합니다:
  - 병용금기:               약물 쌍 -> 경고(HIGH) + 상세정보
  - 노인주의:               단일 약물 -> 주의(MEDIUM) + 약품상세정보
  - 노인주의(해열진통소염제): 단일 약물 -> 주의(MEDIUM) + 약품상세정보 (별도 카테고리)

사용:
    from part2_dur_review import DURReviewer
    reviewer = DURReviewer()
    alerts = reviewer.review(["타이레놀정500mg", "이부프로펜정"])
"""

import re
from dataclasses import dataclass, field, asdict

import pandas as pd

from config import CSV_ANTIPYRETIC, CSV_CONTRAINDICATED, CSV_ELDERLY, CSV_ENCODING


# -- 데이터 클래스 ----------------------------------------------------------

@dataclass
class Alert:
    alert_type: str       # '병용금기' | '노인주의' | '노인주의(해열진통소염제)'
    severity: str         # 'HIGH' | 'MEDIUM'
    drugs: list           # 해당 약품명 목록
    detail: str           # 상세정보 원문
    matched_product: str  # DB에서 매칭된 제품명
    extra: dict = field(default_factory=dict)

    def to_dict(self):
        return asdict(self)


# -- 정규화 -----------------------------------------------------------------

def _normalize(name: str) -> str:
    """비교용 정규화: 공백/괄호/숫자단위 제거, 소문자화"""
    name = re.sub(r"\s+", "", name)
    name = re.sub(r"\(.*?\)", "", name)
    name = re.sub(r"\d+(\.\d+)?(mg|ml|g|mcg|ug|IU|밀리그램|밀리리터)", "", name, flags=re.IGNORECASE)
    return name.lower().strip()


# -- DB 로드 및 인덱스 -------------------------------------------------------

class DURDatabase:
    """DUR CSV 3종을 로드하고 검색 인덱스를 구축합니다."""

    def __init__(self):
        self._loaded = False
        self._elderly_df = None
        self._antipyretic_df = None
        self._contraind_df = None
        self._elderly_index = {}
        self._antipyretic_index = {}
        self._contraind_norms_A = []
        self._contraind_norms_B = []

    def load(self):
        if self._loaded:
            return
        print("DUR DB 로딩 중...")

        self._elderly_df = pd.read_csv(CSV_ELDERLY, encoding=CSV_ENCODING)
        self._elderly_df["_norm"] = self._elderly_df["제품명"].apply(_normalize)
        self._elderly_index = {row["_norm"]: i for i, row in self._elderly_df.iterrows()}

        self._antipyretic_df = pd.read_csv(CSV_ANTIPYRETIC, encoding=CSV_ENCODING)
        self._antipyretic_df["_norm"] = self._antipyretic_df["제품명"].apply(_normalize)
        self._antipyretic_index = {row["_norm"]: i for i, row in self._antipyretic_df.iterrows()}

        self._contraind_df = pd.read_csv(CSV_CONTRAINDICATED, encoding=CSV_ENCODING)
        self._contraind_df["_normA"] = self._contraind_df["제품명A"].apply(_normalize)
        self._contraind_df["_normB"] = self._contraind_df["제품명B"].apply(_normalize)
        self._contraind_norms_A = self._contraind_df["_normA"].tolist()
        self._contraind_norms_B = self._contraind_df["_normB"].tolist()

        self._loaded = True
        print(
            "  노인주의: " + str(len(self._elderly_df)) + "건 | "
            + "해열: " + str(len(self._antipyretic_df)) + "건 | "
            + "병용금기: " + str(len(self._contraind_df)) + "건"
        )

    def _match_index(self, query_norm, index):
        if query_norm in index:
            return [index[query_norm]]
        return [idx for key, idx in index.items() if query_norm in key or key in query_norm]

    def find_elderly(self, query_norm):
        return [self._elderly_df.iloc[i] for i in self._match_index(query_norm, self._elderly_index)]

    def find_antipyretic(self, query_norm):
        return [self._antipyretic_df.iloc[i] for i in self._match_index(query_norm, self._antipyretic_index)]

    def find_contraindicated(self, norm_a, norm_b):
        results = []
        for i, (na, nb) in enumerate(zip(self._contraind_norms_A, self._contraind_norms_B)):
            match_ab = (norm_a in na or na in norm_a) and (norm_b in nb or nb in norm_b)
            match_ba = (norm_b in na or na in norm_b) and (norm_a in nb or nb in norm_a)
            if match_ab or match_ba:
                results.append(self._contraind_df.iloc[i])
        return results


# -- 리뷰어 -----------------------------------------------------------------

class DURReviewer:
    """
    약물명 목록을 받아 DUR 경고를 반환합니다.

    Parameters
    ----------
    db : DURDatabase | None
    patient_age : int  노인주의 기준 나이 (기본 65)
    """

    def __init__(self, db=None, patient_age=65):
        self.db = db or DURDatabase()
        self.db.load()
        self.age_threshold = patient_age

    def review(self, drug_names, patient_age=None):
        """
        Parameters
        ----------
        drug_names   : 약물 상품명 목록
        patient_age  : 환자 나이 (None이면 항상 노인주의 체크)

        Returns
        -------
        alerts : Alert 목록 (중복 제거됨)
        """
        age = patient_age if patient_age is not None else self.age_threshold
        norm_names = [(_normalize(n), n) for n in drug_names]
        alerts = []
        seen = set()

        def _add(alert):
            key = (alert.alert_type, frozenset(alert.drugs), alert.detail)
            if key not in seen:
                seen.add(key)
                alerts.append(alert)

        # Rule 1: 병용금기
        n = len(norm_names)
        for i in range(n):
            for j in range(i + 1, n):
                na, orig_a = norm_names[i]
                nb, orig_b = norm_names[j]
                for row in self.db.find_contraindicated(na, nb):
                    _add(Alert(
                        alert_type="병용금기",
                        severity="HIGH",
                        drugs=[orig_a, orig_b],
                        detail=str(row.get("상세정보", "")),
                        matched_product=str(row.get("제품명A", "")) + " + " + str(row.get("제품명B", "")),
                        extra={
                            "성분명A": str(row.get("성분명A", "")),
                            "성분명B": str(row.get("성분명B", "")),
                            "고시번호": str(row.get("고시번호", "")),
                            "고시일자": str(row.get("고시일자", "")),
                        },
                    ))

        # Rule 2 & 3: 노인주의 (나이 기준 이상)
        if age >= self.age_threshold:
            for norm, orig in norm_names:
                # 노인주의(해열진통소염제) -- 먼저 체크 (더 구체적)
                for row in self.db.find_antipyretic(norm):
                    _add(Alert(
                        alert_type="노인주의(해열진통소염제)",
                        severity="MEDIUM",
                        drugs=[orig],
                        detail=str(row.get("약품상세정보", "")),
                        matched_product=str(row.get("제품명", "")),
                        extra={
                            "성분명": str(row.get("성분명", "")),
                            "성분코드": str(row.get("성분코드", "")),
                        },
                    ))
                # 노인주의 일반
                for row in self.db.find_elderly(norm):
                    _add(Alert(
                        alert_type="노인주의",
                        severity="MEDIUM",
                        drugs=[orig],
                        detail=str(row.get("약품상세정보", "")),
                        matched_product=str(row.get("제품명", "")),
                        extra={
                            "성분명": str(row.get("성분명", "")),
                            "성분코드": str(row.get("성분코드", "")),
                            "공고번호": str(row.get("공고번호", "")),
                        },
                    ))

        return alerts

    def format_report(self, alerts):
        """경고 목록을 가독성 있는 텍스트 리포트로 변환"""
        if not alerts:
            return "DUR 검토 결과: 이상 없음"

        lines = ["DUR 검토 결과: " + str(len(alerts)) + "건 발견\n"]
        for i, a in enumerate(alerts, 1):
            icon = "[HIGH]" if a.severity == "HIGH" else "[MEDIUM]"
            lines.append(icon + " [" + str(i) + "] " + a.alert_type)
            lines.append("   대상 약물: " + " + ".join(a.drugs))
            lines.append("   매칭 제품: " + a.matched_product)
            lines.append("   상세 정보: " + a.detail)
            for k, v in a.extra.items():
                if v and v not in ("nan", "NaN", ""):
                    lines.append("   " + k + ": " + v)
            lines.append("")
        return "\n".join(lines)


# -- 테스트 -----------------------------------------------------------------

if __name__ == "__main__":
    reviewer = DURReviewer()

    tests = [
        ("병용금기 -- 사이클로스포린 + 로수바스타틴", ["사이폴주", "로슈바정20mg"], 70),
        ("노인주의(해열) -- 아세클로페낙",            ["에이서캡슐", "타이레놀정500mg"], 68),
        ("노인주의 일반 -- 솔리페나신",               ["요시케어정5밀리그램"], 72),
        ("정상 케이스 (경고 없음)",                   ["아목시실린캡슐"], 40),
    ]

    for desc, drugs, age in tests:
        print("\n" + "=" * 60)
        print("테스트: " + desc)
        print("입력 약물: " + str(drugs) + "  나이: " + str(age))
        alerts = reviewer.review(drugs, patient_age=age)
        print(reviewer.format_report(alerts))
