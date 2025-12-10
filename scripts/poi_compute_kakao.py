import os
import asyncio
import aiohttp
import pandas as pd
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("KAKAO_REST_API_KEY")

INPUT = "data/station.csv"
OUTPUT = "data/station_with_poi.csv"

KAKAO_URL = "https://dapi.kakao.com/v2/local/search/keyword.json"
HEADERS = {"Authorization": f"KakaoAK {API_KEY}"}

# 한 번에 너무 많이 때리면 429 뜨므로 세마포어로 제어
SEM = asyncio.Semaphore(20)   # 동시 20개 → 3000건 5~7초 컷


async def fetch_poi(session, lat, lng, keyword):
    params = {
        "query": keyword,
        "y": lat,
        "x": lng,
        "radius": 300,
        "size": 15
    }
    async with SEM:
        async with session.get(KAKAO_URL, params=params, headers=HEADERS) as resp:
            if resp.status != 200:
                return 0
            data = await resp.json()
            return len(data.get("documents", []))


async def process_row(session, idx, lat, lng):
    store = await fetch_poi(session, lat, lng, "편의점")
    hotel = await fetch_poi(session, lat, lng, "호텔")
    restaurant = await fetch_poi(session, lat, lng, "맛집")

    return idx, store, hotel, restaurant


async def main_async():
    df = pd.read_csv(INPUT)

    df["poi_store_300m"] = 0
    df["poi_hotel_300m"] = 0
    df["poi_restaurant_300m"] = 0

    tasks = []
    async with aiohttp.ClientSession() as session:
        for idx, row in df.iterrows():
            lat, lng = row["위도"], row["경도"]
            tasks.append(process_row(session, idx, lat, lng))

        print("🚀 카카오 API 병렬 호출 시작...")
        results = await asyncio.gather(*tasks)

    for idx, store, hotel, restaurant in results:
        df.loc[idx, "poi_store_300m"] = store
        df.loc[idx, "poi_hotel_300m"] = hotel
        df.loc[idx, "poi_restaurant_300m"] = restaurant

    df.to_csv(OUTPUT, index=False)
    print("🎉 완료! →", OUTPUT)


def main():
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
