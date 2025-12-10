"""
Kakao Local API sampler — 정확히 N개(기본 30개) 수집 + 맞춤 CSV 포맷 버전
- 느린 원인:
  * 불필요하게 많은 page를 끝까지 조회
  * 결과가 없어도 is_end 확인 안 하고 계속 요청
- 개선:
  * meta["is_end"] == True 이면 즉시 해당 키워드 탐색 종료
  * max_pages 기본 40으로 축소 (옵션으로 조정 가능)
"""

import re
import time
import html
import random
import argparse
from typing import List, Dict, Any, Optional

import requests
import pandas as pd

# ────────────────────────────────────────────────
# Kakao REST API KEY 하드코딩
# ────────────────────────────────────────────────
KAKAO_REST_KEY = "23f88060feff03f24c4dc64807d2201c"
KAKAO_SEARCH_URL = "https://dapi.kakao.com/v2/local/search/keyword.json"


def get_env(key: str) -> str:
    # env 안 쓰고 하드코딩된 키 그대로 사용
    return KAKAO_REST_KEY


def clean_text(s: Optional[str]) -> str:
    if s is None:
        return ""
    s = html.unescape(s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def kakao_search_keyword(query: str, size: int = 15, page: int = 1) -> Dict[str, Any]:
    # Kakao Local API 요청
    headers = {"Authorization": f"KakaoAK {get_env('KAKAO_REST_KEY')}"}
    # size 최대 15, page 최대 45 (카카오 스펙)
    size = max(1, min(size, 15))
    page = max(1, min(page, 45))
    params = {"query": query, "size": size, "page": page}
    r = requests.get(KAKAO_SEARCH_URL, headers=headers, params=params, timeout=10)
    r.raise_for_status()
    return r.json()


# ─────────────────────────────────────────────
# 카테고리 → 키워드
# ─────────────────────────────────────────────
CATEGORY_KEYWORDS: Dict[str, List[str]] = {
    "근린생활시설": ["카페", "드라이브스루", "편의점", "베이커리"],
    "공동주택": ["다가구주택", "다세대주택", "빌라", "연립주택", "도심형생활주택"],
    "자동차관련시설": ["자동차 정비소", "카센터", "세차장"],
    "업무시설": ["소형 오피스", "지식산업센터", "소규모 사무실", "공유오피스", "스타트업 오피스"],
    "판매시설": ["가구 매장", "인테리어 매장", "중고가전 매장", "자동차용품 매장", "생활용품점"],
    "공장": ["소규모 공장", "목공소", "인쇄소", "철공소", "공방", "제과제빵소", "식품가공소"],
    "숙박시설": ["모텔", "소형 호텔", "게스트하우스", "호스텔"],
    "가설건축물": [
        "컨테이너",
        "컨테이너 사무실",
        "컨테이너 하우스",
        "컨테이너 창고",
        "컨테이너 임대",
        "조립식 건물",
        "조립식 사무실",
        "조립식 창고",
        "임시 건물",
        "임시 사무실",
        "임시 창고",
        "임시 숙소",
        "이동식 건물",
        "이동식 사무실",
        "이동식 창고",
        "이동식 화장실",
        "모듈러 건축",
        "모듈러 하우스",
        "모듈러 사무실",
        "가건물",
        "가설 사무실",
        "현장 사무소",
        "공사 현장",
        "공사용 컨테이너",
        "모델하우스",
        "가설건축물"
    ],
    "기타": ["LPG충전소", "전기차충전소", "소형 창고", "공영주차장", "공공화장실"],
}

# 시도 리스트
PROVINCES: List[str] = [
    "서울특별시",
    "경기도",
    "인천광역시",
    "강원특별자치도",
    "충청북도",
    "충청남도",
    "대전광역시",
    "경상북도",
    "경상남도",
    "대구광역시",
    "울산광역시",
    "부산광역시",
    "전북특별자치도",
    "전라남도",
    "광주광역시",
    "제주특별자치도",
]


# ─────────────────────────────────────────────
# 중복 제거용 키
# ─────────────────────────────────────────────
def normalize_key(name: str, addr: str, x: Any, y: Any):
    name = (name or "").replace(" ", "").lower()
    addr = (addr or "").replace(" ", "").lower()
    try:
        x_val = round(float(x), 5)
        y_val = round(float(y), 5)
    except Exception:
        x_val, y_val = None, None
    return (name, addr, x_val, y_val)


# ─────────────────────────────────────────────
# 대규모 공장/산단 제외
# ─────────────────────────────────────────────
def is_large_factory_like(place_name: str, category_name: str, address: str) -> bool:
    text = f"{place_name} {category_name} {address}"
    big = [
        "산업단지",
        "일반산업단지",
        "국가산업단지",
        "산단",
        "공단",
        "제철소",
        "정유공장",
        "발전소",
        "물류단지",
    ]
    return any(w in text for w in big)


# ─────────────────────────────────────────────
# ★ 정확히 target개(기본 30개)를 채울 때까지 검색
#  - meta["is_end"]를 활용해서 불필요한 page 탐색 중단
#  - max_pages 기본 40 (너무 크면 느려짐)
# ─────────────────────────────────────────────
def collect_exact_n(
    region: str,
    category: str,
    size: int = 15,
    max_pages: int = 40,
    target: int = 30,
    sleep_sec: float = 0.1,
) -> Optional[List[Dict[str, Any]]]:
    pool: List[Dict[str, Any]] = []
    seen = set()

    for kw in CATEGORY_KEYWORDS[category]:
        # 페이지를 1~max_pages까지, 하지만 target 채우면 바로 종료
        for pg in range(1, max_pages + 1):
            if len(pool) >= target:
                break

            q = f"{region} {kw}"

            try:
                data = kakao_search_keyword(q, size=size, page=pg)
            except Exception as e:
                print(f"[WARN] {q} page={pg}: {e}")
                continue

            docs = data.get("documents", [])
            meta = data.get("meta", {})

            # 결과가 없으면 이 키워드에 대해 더 이상 찾지 않음
            if not docs:
                break

            for d in docs:
                place = clean_text(d.get("place_name"))
                catname = clean_text(d.get("category_name"))
                addr = clean_text(d.get("address_name"))
                x, y = d.get("x"), d.get("y")

                # 공장 필터링
                if category == "공장" and is_large_factory_like(place, catname, addr):
                    continue

                key = normalize_key(place, addr, x, y)
                if key in seen or not place:
                    continue

                seen.add(key)
                pool.append(
                    {
                        "대분류": category,
                        "지번주소(읍/면/동)": addr,
                        "관할주소": region,
                    }
                )

                if len(pool) >= target:
                    break

            # 카카오 meta의 is_end가 True면 이 키워드에 대해 더 이상 페이지 탐색 안 함
            if meta.get("is_end", False):
                break

            time.sleep(sleep_sec)

        if len(pool) >= target:
            break

    if len(pool) < target:
        print(f"[ERROR] {region} / {category}: {target}개 채우지 못함 (현재 {len(pool)}개)")
        return None

    # 랜덤 셔플 후 정확히 target개만 반환
    random.shuffle(pool)
    return pool[:target]


# ─────────────────────────────────────────────
# 전체 실행 루프
# ─────────────────────────────────────────────
def run_sampler(
    n_per_combo: int = 30,
    seed: int = 123,
    max_pages: int = 40,
    size: int = 15,
    sleep_sec: float = 0.1,
) -> pd.DataFrame:
    random.seed(seed)
    rows: List[Dict[str, Any]] = []

    for region in PROVINCES:
        for category in CATEGORY_KEYWORDS.keys():
            print(f"[INFO] {region} / {category} → {n_per_combo}개 수집 중...")

            result = collect_exact_n(
                region=region,
                category=category,
                size=size,
                max_pages=max_pages,
                target=n_per_combo,
                sleep_sec=sleep_sec,
            )

            if result is None:
                print(f"[WARN] {region}/{category} → 부족, 스킵됨")
                continue

            rows.extend(result)

    return pd.DataFrame(rows)


# ─────────────────────────────────────────────
# main
# ─────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--outfile", type=str, default="data.csv")
    ap.add_argument("--xlsx", type=str, default="")
    ap.add_argument("--n", type=int, default=30, help="시도×대분류 조합당 개수")
    ap.add_argument("--seed", type=int, default=123)
    ap.add_argument(
        "--max-pages",
        type=int,
        default=10,
        help="키워드별 최대 페이지 수 (기본 10, 너무 크면 느려짐)",
    )
    ap.add_argument(
        "--size",
        type=int,
        default=15,
        help="페이지당 요청 size (카카오 최대 15)",
    )
    ap.add_argument(
        "--sleep",
        type=float,
        default=0.1,
        help="요청 사이 대기 시간(초). 너무 줄이면 rate limit 걸릴 수 있음.",
    )
    args = ap.parse_args()

    df = run_sampler(
        n_per_combo=args.n,
        seed=args.seed,
        max_pages=args.max_pages,
        size=args.size,
        sleep_sec=args.sleep,
    )

    # 원하는 형식으로 저장 (대분류, 지번주소(읍/면/동), 관할주소)
    df.to_csv(args.outfile, index=False, encoding="utf-8-sig")
    print(f"[INFO] CSV 저장 완료 → {args.outfile}")

    if args.xlsx.strip():
        with pd.ExcelWriter(args.xlsx) as w:
            df.to_excel(w, index=False, sheet_name="전체")
            for cat in CATEGORY_KEYWORDS.keys():
                df[df["대분류"] == cat].to_excel(w, index=False, sheet_name=cat)
        print(f"[INFO] XLSX 저장 완료 → {args.xlsx}")


if __name__ == "__main__":
    main()
