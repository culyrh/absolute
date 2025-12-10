import pandas as pd
import re
import os
import math

# ============================================
# 0) 경로 설정
# ============================================
BASE = r"E:\pyt\absolute-be\data"
PATH_BJD = os.path.join(BASE, "법정동_코드_전체자료.csv")


# ============================================
# 1) 텍스트에서 마지막 동/읍/면 추출
#    (주소 / 법정동명 둘 다 여기 통일)
# ============================================
def extract_dong_unit(text: str):
    """
    ex)
      '서울 송파구 송파동 22-2'           -> '송파동'
      '서울 강동구 성내동 43-19'          -> '성내동'
      '서울특별시 송파구 송파동'          -> '송파동'
      '강원특별자치도 원주시 호저면 주산리 861' -> '호저면'
    """
    if not isinstance(text, str):
        return None

    # 전체 문자열에서 '...동' / '...읍' / '...면' 전부 찾고, 가장 마지막 것 사용
    matches = re.findall(r'([가-힣]+(?:동|읍|면))', text)
    if not matches:
        return None
    return matches[-1]


# ============================================
# 2) 법정동코드 정규화 (10자리)
#    (기존 FastAPI 코드 로직이랑 비슷하게 맞춤)
# ============================================
def normalize_bjd_code(code):
    if code is None:
        return None

    s = str(code).strip()
    if s.lower() == "nan":
        return None

    # float로 읽힌 경우 뒤에 .0 제거
    if s.endswith(".0"):
        s = s[:-2]

    # 숫자만 남기기
    s = "".join(ch for ch in s if ch.isdigit())

    if not s:
        return None

    # 8자리면 법정동 -> 10자리로
    if len(s) == 8:
        s += "00"

    # 모자라도 10자리까지 0 패딩
    if len(s) < 10:
        s = s.ljust(10, "0")

    # 10자리만 사용
    return s[:10]


# ============================================
# 3) 법정동명(동/읍/면) -> 코드 매핑 딕셔너리 생성
# ============================================
def build_dong_to_code_mapping():
    print("📂 법정동 코드 CSV 로딩:", PATH_BJD)

    if not os.path.exists(PATH_BJD):
        raise FileNotFoundError(f"❌ 법정동 코드 파일이 없습니다: {PATH_BJD}")

    bjd = pd.read_csv(PATH_BJD, dtype=str)
    bjd.columns = bjd.columns.str.strip()

    if "법정동명" not in bjd.columns or "법정동코드" not in bjd.columns:
        raise ValueError("❌ 법정동 코드 CSV에 '법정동명' 또는 '법정동코드' 컬럼이 없습니다.")

    # 동/읍/면 단위만 추출
    bjd["법정동단위"] = bjd["법정동명"].apply(extract_dong_unit)
    bjd["법정동코드_norm"] = bjd["법정동코드"].apply(normalize_bjd_code)

    # 유효한 것만 남기기
    bjd_valid = bjd.dropna(subset=["법정동단위", "법정동코드_norm"])

    # 동 이름(송파동, 자양동, 성내동, ...) -> 첫 번째 코드 사용
    mapping = {}
    for dong, sub in bjd_valid.groupby("법정동단위"):
        code = sub["법정동코드_norm"].iloc[0]
        mapping[dong] = code

    print(f"✅ 동/읍/면 단위 매핑 {len(mapping)}개 생성")
    # 예시 몇 개 찍어보기 (디버그용)
    sample_items = list(mapping.items())[:10]
    print("   예시 매핑:", sample_items)

    return mapping


# ============================================
# 4) 실제 df에 adm_cd2 붙이기
# ============================================
def attach_adm_cd2(df: pd.DataFrame) -> pd.DataFrame:
    # 1) 입력 df에서 동/읍/면 뽑기
    print("🧩 주소 → 법정동명(동/읍/면) 추출 중...")
    df["법정동명"] = df["지번주소 (읍/면/동)"].apply(extract_dong_unit)

    print("   추출 예시:")
    print(df[["지번주소 (읍/면/동)", "법정동명"]].head(5))

    # 2) 매핑 딕셔너리 생성
    mapping = build_dong_to_code_mapping()

    # 3) 매핑 적용
    print("🔗 동/읍/면 → adm_cd2 매핑 중...")
    df["adm_cd2"] = df["법정동명"].map(mapping)

    print("   매핑 결과 예시:")
    print(df[["지번주소 (읍/면/동)", "법정동명", "adm_cd2"]].head(10))

    return df


# ============================================
# 5) 메인 실행
# ============================================
if __name__ == "__main__":

    # 👉 여기 입력/출력 파일명만 네 상황에 맞게 써주면 됨
    INPUT = r"E:\pyt\absolute-be\scripts\data_with_coords.csv"
    OUTPUT = r"E:\pyt\absolute-be\data\data_with_adm.csv"

    print("📂 입력 CSV 로드:", INPUT)
    if not os.path.exists(INPUT):
        raise FileNotFoundError(f"❌ 입력 CSV 파일이 존재하지 않습니다: {INPUT}")

    df = pd.read_csv(INPUT)

    if "지번주소 (읍/면/동)" not in df.columns:
        raise ValueError("❌ CSV에 '지번주소 (읍/면/동)' 컬럼이 없습니다!")

    df_ready = attach_adm_cd2(df)

    print("💾 저장 중:", OUTPUT)
    df_ready.to_csv(OUTPUT, index=False, encoding="utf-8-sig")

    print("🎉 완료! data_with_adm.csv에 adm_cd2 컬럼이 붙었습니다.")
