# scripts/add_prediction_to_station.py
import sys
import os
import pandas as pd
import numpy as np

# absolute-be root path 등록
CURRENT = os.path.abspath(__file__)
ROOT = os.path.dirname(os.path.dirname(CURRENT))
sys.path.insert(0, ROOT)

from app.services.geoai_config import GeoAIConfig
from app.services.geoai_model import GeoAIClassifier


# === 모델이 실제 학습에 사용하는 feature ===
USE_FEATURES = [
    "인구[명]",
    "교통량(AADT)",
    "숙박업소(관광지수)",
    "상권밀집도(비율)",
    "parcel_300m",
    "parcel_500m",
    "nearest_parcel_m",     # ※ train.csv에는 있으므로 유지
    "poi_store_300m",
    "poi_hotel_300m",
    "poi_restaurant_300m",
]


def clean_coord_columns(df):
    """위도/경도 중복 제거 (feature로는 쓰지 않음)"""
    if "_X" in df.columns:
        df["경도"] = df["_X"]
    if "_Y" in df.columns:
        df["위도"] = df["_Y"]
    df = df.loc[:, ~df.columns.duplicated()]
    df.columns = df.columns.str.strip()
    return df


def main():
    cfg = GeoAIConfig()

    # ================================================================
    # 1) train.csv 로드 → 아무것도 제거하지 말고 그대로 사용
    # ================================================================
    print("📂 train.csv 로드")
    train_df = pd.read_csv(cfg.train_csv)
    train_df = clean_coord_columns(train_df)

    # train.csv에는 nearest_parcel_m 이미 있음 → 건드리지 않는다
    train_ready = train_df[["대분류"] + USE_FEATURES]

    # ================================================================
    # 2) 모델 학습
    # ================================================================
    print("🤖 모델 학습")
    model = GeoAIClassifier()
    model.train(train_ready)

    # ================================================================
    # 3) station.csv 로드
    # ================================================================
    print("📂 station.csv 로드")
    station_path = cfg.station_csv
    station = pd.read_csv(station_path)
    station = clean_coord_columns(station)

    # ================================================================
    # 4) station.csv에만 nearest_parcel_m 추가 (기본값 0.0)
    # ================================================================
    if "nearest_parcel_m" not in station.columns:
        print("⚠️ station.csv: nearest_parcel_m 없음 → 0.0으로 생성")
        station["nearest_parcel_m"] = 0.0

    # ================================================================
    # 5) feature 선택
    # ================================================================
    station_feat = station[USE_FEATURES]

    # ================================================================
    # 6) 예측 (top-3)
    # ================================================================
    print("🔮 recommend1~3 생성")
    proba = model.clf.predict_proba(station_feat)
    classes = model.clf.classes_
    idx_sorted = np.argsort(proba, axis=1)

    station["recommend1"] = classes[idx_sorted[:, -1]]
    station["recommend2"] = classes[idx_sorted[:, -2]]
    station["recommend3"] = classes[idx_sorted[:, -3]]

    # ================================================================
    # 7) 저장
    # ================================================================
    station.to_csv(station_path, index=False, encoding="utf-8-sig")
    print("🎉 recommend1~3 갱신 완료!")
    print("🟢 station.csv에 nearest_parcel_m = 0.0 자동 추가 완성")


if __name__ == "__main__":
    main()
