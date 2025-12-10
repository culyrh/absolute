import os
import time
import requests
import psycopg2
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from psycopg2.extras import execute_values
from dotenv import load_dotenv

load_dotenv()

KAKAO_REST_API_KEY = os.getenv("KAKAO_KEY", "23f88060feff03f24c4dc64807d2201c")
TRAIN_CSV = "data/data_ready_final_ordered.csv"
RADIUS_M = 300
KAKAO_LOCAL_URL = "https://dapi.kakao.com/v2/local/search/category.json"

CATEGORY_CONFIG = {
    "CS2": "편의점",
    "AD5": "숙박시설",
    "FD6": "음식점",
}

PG_CONN_INFO = dict(
    host=os.getenv("POSTGRES_HOST"),
    port=os.getenv("POSTGRES_PORT"),
    dbname=os.getenv("POSTGRES_DB"),
    user=os.getenv("POSTGRES_USER"),
    password=os.getenv("POSTGRES_PASSWORD"),
)

# ---------------------------------------
# Kakao 캐싱 (같은 좌표일 때 API 재호출 방지)
# ---------------------------------------
_kakao_cache = {}

def kakao_category_search(lon, lat, category_code, radius=RADIUS_M):
    cache_key = (lon, lat, category_code)
    if cache_key in _kakao_cache:
        return _kakao_cache[cache_key]

    headers = {"Authorization": f"KakaoAK {KAKAO_REST_API_KEY}"}

    params = dict(
        category_group_code=category_code,
        x=lon,
        y=lat,
        radius=radius,
        page=1,
        size=15,
        sort="distance",
    )

    try:
        resp = requests.get(KAKAO_LOCAL_URL, headers=headers, params=params, timeout=3)
        data = resp.json()
        docs = data.get("documents", [])
    except Exception as e:
        print("API 오류:", e)
        docs = []

    _kakao_cache[cache_key] = docs
    time.sleep(0.01)  # API 너무 세게 때리지 않게
    return docs


# ---------------------------------------
# POI INSERT
# ---------------------------------------
def insert_poi_rows(conn, rows):
    if not rows:
        return

    sql = """
    INSERT INTO poi (station_id, src, category, name, address, lat, lon, geom)
    VALUES %s
    ON CONFLICT (category, lon, lat) DO NOTHING;
    """

    template = """
    (%s, %s, %s, %s, %s, %s, %s,
     ST_Transform(ST_SetSRID(ST_Point(%s, %s), 4326), 5186)
    )
    """

    values = [
        (
            r["station_id"], r["src"], r["category"],
            r["name"], r["address"], r["lat"], r["lon"],
            r["lon"], r["lat"]
        )
        for r in rows
    ]

    with conn.cursor() as cur:
        execute_values(cur, sql, values, template=template)

    conn.commit()


# ---------------------------------------
# 각 row 병렬 처리 함수
# ---------------------------------------
def process_station(rowdata):
    idx, row = rowdata
    lat = float(row["위도"])
    lon = float(row["경도"])
    station_id = idx

    results = []

    for code, cat_name in CATEGORY_CONFIG.items():
        docs = kakao_category_search(lon, lat, code)
        for d in docs:
            try:
                x = float(d["x"])
                y = float(d["y"])
            except:
                continue

            results.append(dict(
                station_id=station_id,
                src="kakao",
                category=cat_name,
                name=d.get("place_name", ""),
                address=d.get("road_address_name") or d.get("address_name") or "",
                lat=y,
                lon=x,
            ))

    return results


# ---------------------------------------
# 메인
# ---------------------------------------
def main():
    print("📂 CSV 로드 중...")
    df = pd.read_csv(TRAIN_CSV)

    conn = psycopg2.connect(**PG_CONN_INFO)
    all_results = []

    print(f"🔍 전체 대상: {len(df)}개")
    print("🚀 병렬 처리 시작 (5 threads)...")

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(process_station, item) for item in df.iterrows()]

        for i, f in enumerate(as_completed(futures)):
            rows = f.result()
            all_results.extend(rows)

            if i % 50 == 0:
                print(f"⏳ 진행중: {i}/{len(df)}")

    print("💾 DB INSERT 중...")
    insert_poi_rows(conn, all_results)

    conn.close()
    print("🎉 완료! 병렬 수집 종료.")


if __name__ == "__main__":
    main()
