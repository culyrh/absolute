import os
import psycopg2
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

INPUT_CSV = "data/test_data.csv"
OUTPUT_CSV = "data/test_data_with_poi.csv"

PG_CONN_INFO = dict(
    host=os.getenv("POSTGRES_HOST"),
    port=os.getenv("POSTGRES_PORT"),
    dbname=os.getenv("POSTGRES_DB"),
    user=os.getenv("POSTGRES_USER"),
    password=os.getenv("POSTGRES_PASSWORD"),
)

POI_SQL = """
SELECT
    station_id,
    COUNT(*) FILTER (WHERE category = '편의점') AS poi_store_300m,
    COUNT(*) FILTER (WHERE category = '숙박시설') AS poi_hotel_300m,
    COUNT(*) FILTER (WHERE category = '음식점') AS poi_restaurant_300m
FROM poi
GROUP BY station_id
ORDER BY station_id;
"""

def main():
    print("📂 CSV 로드...")
    df = pd.read_csv(INPUT_CSV)

    # 🚫 기존 poi 컬럼 제거
    drop_cols = ["poi_store_300m", "poi_hotel_300m", "poi_restaurant_300m"]
    df = df.drop(columns=drop_cols, errors="ignore")

    # station_id = index 그대로
    df["station_id"] = df.index

    print("🗄️ DB에서 poi 집계 조회 중...")
    conn = psycopg2.connect(**PG_CONN_INFO)
    df_poi = pd.read_sql(POI_SQL, conn)
    conn.close()

    print("🔗 CSV + POI 병합 중...")
    df_merged = df.merge(df_poi, on="station_id", how="left")

    # poi 값 정수로 변환
    for col in ["poi_store_300m", "poi_hotel_300m", "poi_restaurant_300m"]:
        df_merged[col] = df_merged[col].fillna(0).astype(int)

    # station_id 제거
    df_merged = df_merged.drop(columns=["station_id"])

    print(f"💾 저장: {OUTPUT_CSV}")
    df_merged.to_csv(OUTPUT_CSV, index=False)

    print("🎉 완료! 기존 값 지우고 정확한 poi 붙였습니다.")


if __name__ == "__main__":
    main()
