import pandas as pd

INPUT = "data/test_data_with_parcel.csv"
OUTPUT = "data/test_data_final.csv"

print("📂 파일 로드:", INPUT)
df = pd.read_csv(INPUT)

# -------------------------------
# 1) parcel/poi 중복 컬럼 식별
# -------------------------------
cols = df.columns.tolist()

# 각 컬럼 등장 위치 찾기
p1 = cols.index("parcel_300m")                 # 첫 parcel
p1_end = p1 + 3                                 # parcel 3개

poi1_start = p1_end
poi1_end = poi1_start + 3                       # poi 3개

# 두 번째 parcel 위치 찾기 (뒤에서 찾음)
p2 = len(cols) - 6                              # parcel_300m 실제 계산본 시작
p2_end = p2 + 3

# 마지막 poi (지워야 함)
poi2_start = p2_end
poi2_end = poi2_start + 3

# -------------------------------
# 2) 필요한 컬럼만 남기기
# -------------------------------
keep_cols = (
    cols[0:10]              # 대분류 ~ adm_cd2 기본 정보
    + cols[p2:p2_end]       # 두 번째 parcel set (살림)
    + cols[poi1_start:poi1_end]  # 첫 번째 poi set (살림)
)

df2 = df[keep_cols]

# -------------------------------
# 3) train.csv 컬럼 순서로 정렬
# -------------------------------
TRAIN_COLUMNS = [
    "대분류",
    "지번주소 (읍/면/동)",
    "관할주소",
    "인구[명]",
    "교통량(AADT)",
    "숙박업소(관광지수)",
    "상권밀집도(비율)",
    "위도",
    "경도",
    "adm_cd2",
    "parcel_300m",
    "parcel_500m",
    "nearest_parcel_m",
    "poi_store_300m",
    "poi_hotel_300m",
    "poi_restaurant_300m",
]

df2 = df2[TRAIN_COLUMNS]

# -------------------------------
# 저장
# -------------------------------
df2.to_csv(OUTPUT, index=False)
print("🎉 완료:", OUTPUT)
