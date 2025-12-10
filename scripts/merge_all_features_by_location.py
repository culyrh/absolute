import pandas as pd
import numpy as np
import os

BASE = r"E:\pyt\absolute-be\data"

PATH_MAIN = os.path.join(BASE, "data_with_adm.csv")
PATH_POP = os.path.join(BASE, "population.csv")
PATH_BUS = os.path.join(BASE, "business.csv")
PATH_TOUR = os.path.join(BASE, "tour.csv")
PATH_TRAFFIC = os.path.join(BASE, "2024년_도로종류별_교통량_및_XY좌표.csv")

OUTPUT = os.path.join(BASE, "data_ready_final.csv")

# ----------------------------------------
# Haversine
# ----------------------------------------
def haversine(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat/2)**2 + np.cos(lat1)*np.cos(lat2)*(np.sin(dlon/2)**2)
    return 6371 * 2 * np.arcsin(np.sqrt(a))

# ----------------------------------------
# 최근접 1개 매칭
# ----------------------------------------
def attach_nearest_feature(base_df, ref_df, feature_cols, suffix, to_int=False):
    base_df = base_df.copy()

    for col in feature_cols:
        base_df[f"{col}{suffix}"] = np.nan

    ref_lat = ref_df["lat"].astype(float).values
    ref_lon = ref_df["lon"].astype(float).values

    print("🔗 매칭:", feature_cols)
    for idx, row in base_df.iterrows():
        bl, bo = float(row["위도"]), float(row["경도"])
        d = haversine(bl, bo, ref_lat, ref_lon)
        nearest = d.argmin()
        ref_row = ref_df.iloc[nearest]

        for col in feature_cols:
            value = ref_row[col]

            if to_int:
                value = str(value).replace(",", "").strip()
                try:
                    value = int(float(value))
                except:
                    value = 0

            base_df.loc[idx, f"{col}{suffix}"] = value

    return base_df


# ----------------------------------------
# 실행
# ----------------------------------------
if __name__ == "__main__":
    df = pd.read_csv(PATH_MAIN)

    df["위도"] = df["위도"].astype(float)
    df["경도"] = df["경도"].astype(float)

    # --------------------------
    # 1) Population
    # --------------------------
    pop = pd.read_csv(PATH_POP)
    pop = pop.dropna(subset=["lat", "lon"])
    pop["lat"] = pop["lat"].astype(float)
    pop["lon"] = pop["lon"].astype(float)

    df = attach_nearest_feature(
        df, pop,
        feature_cols=["2023년 수(명)"],
        suffix="_인구",
        to_int=True
    )
    df = df.rename(columns={"2023년 수(명)_인구": "인구[명]"})


    # --------------------------
    # 2) Business (상권밀집도)
    # --------------------------
    bus = pd.read_csv(PATH_BUS)
    bus = bus.dropna(subset=["lat", "lon"])
    bus["lat"] = bus["lat"].astype(float)
    bus["lon"] = bus["lon"].astype(float)

    df = attach_nearest_feature(
        df, bus,
        feature_cols=["비율(%)"],
        suffix="_상권",
        to_int=False
    )

    # ⚠️ rename 정확히 수정
    df = df.rename(columns={"비율(%)_상권": "상권밀집도(비율)"})


    # --------------------------
    # 3) Tourism (숙박업소)
    # --------------------------
    tour = pd.read_csv(PATH_TOUR)
    tour = tour.dropna(subset=["lat", "lon"])
    tour["lat"] = tour["lat"].astype(float)
    tour["lon"] = tour["lon"].astype(float)

    df = attach_nearest_feature(
        df, tour,
        feature_cols=["숙박업소수"],
        suffix="_숙박",
        to_int=True
    )
    df = df.rename(columns={"숙박업소수_숙박": "숙박업소(관광지수)"})


    # --------------------------
    # 4) Traffic (AADT)
    # --------------------------
    tr = pd.read_csv(PATH_TRAFFIC)
    tr = tr.dropna(subset=["lat", "lon"])
    tr["lat"] = tr["lat"].astype(float)
    tr["lon"] = tr["lon"].astype(float)
    tr["AADT"] = tr["AADT"].astype(str).str.replace(",", "").str.strip()

    df = attach_nearest_feature(
        df, tr,
        feature_cols=["AADT"],
        suffix="_교통",
        to_int=True
    )
    df = df.rename(columns={"AADT_교통": "교통량(AADT)"})


    # ------------------------------------
    # 🔥 소수점 제거 — 강제 문자열 저장
    # ------------------------------------
    for col in ["인구[명]", "숙박업소(관광지수)", "교통량(AADT)"]:
        df[col] = df[col].astype(int).astype(str)   # ← 문자열로 저장하면 절대 .0 안 생김

    # 상권만 float 유지
    df["상권밀집도(비율)"] = df["상권밀집도(비율)"].astype(float)

    # ------------------------------------
    # 저장
    # ------------------------------------
    df.to_csv(OUTPUT, index=False, encoding="utf-8-sig")
    print("🎉 모든 지표가 소수점 없는 정수로 완벽 저장되었습니다!")

