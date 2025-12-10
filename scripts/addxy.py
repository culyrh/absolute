"""
data.csv → 좌표 붙여서 data_with_coords.csv 생성
지번주소(읍/면/동) → 위도, 경도 변환
"""

import pandas as pd
import requests
import time

KAKAO_REST_KEY = "23f88060feff03f24c4dc64807d2201c"
KAKAO_ADDR_URL = "https://dapi.kakao.com/v2/local/search/address.json"

def get_coords(address: str):
    """
    주소 → (위도, 경도) 반환
    결과 없으면 (None, None)
    """
    headers = {"Authorization": f"KakaoAK {KAKAO_REST_KEY}"}
    params = {"query": address}

    try:
        r = requests.get(KAKAO_ADDR_URL, headers=headers, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()

        docs = data.get("documents", [])
        if not docs:
            return None, None

        x = docs[0].get("x")   # 경도
        y = docs[0].get("y")   # 위도
        return float(y), float(x)

    except Exception as e:
        print(f"[WARN] 주소 변환 실패: {address} → {e}")
        return None, None


def main():
    df = pd.read_csv("data.csv")

    lats = []
    lngs = []

    for idx, row in df.iterrows():
        addr = row["지번주소 (읍/면/동)"]

        print(f"[INFO] 주소 변환 중... {addr}")

        lat, lng = get_coords(addr)

        lats.append(lat)
        lngs.append(lng)

        time.sleep(0.1)  # 속도 너무 빠르면 카카오에서 rate-limit 걸림

    df["위도"] = lats
    df["경도"] = lngs

    df.to_csv("data_with_coords.csv", index=False, encoding="utf-8-sig")
    print("[INFO] 저장 완료 → data_with_coords.csv")


if __name__ == "__main__":
    main()
