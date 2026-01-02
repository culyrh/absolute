# 2025-2 전북대학교 SW 캡스톤디자인

해당 프로젝트는 **[한국국토정보공사(LX)](https://www.lx.or.kr/kor.do)** x **팀 앱솔루트**의 협력으로 진행되었습니다.
<br>
프론트 깃허브 링크 : [Front-End](https://github.com/gajaeup/absolute)

## 팀 앱솔루트

<div align="center">

<table>
  <tr>
    <td align="center">
      <a href="https://github.com/sjin02">
        <img src="https://avatars.githubusercontent.com/sjin02" width="120px" style="border-radius:50%;" /><br/>
        <sub><b>권서진</b></sub>
      </a>
    </td>
    <td align="center">
      <a href="https://github.com/gajaeup">
        <img src="https://avatars.githubusercontent.com/gajaeup" width="120px" style="border-radius:50%;" /><br/>
        <sub><b>김지애</b></sub>
      </a>
    </td>
    <td align="center">
      <a href="https://github.com/culyrh">
        <img src="https://avatars.githubusercontent.com/culyrh" width="120px" style="border-radius:50%;" /><br/>
        <sub><b>박소현</b></sub>
      </a>
    </td>
    <td align="center">
      <a href="https://github.com/JinHaeunn">
        <img src="https://avatars.githubusercontent.com/JinHaeunn" width="120px" style="border-radius:50%;" /><br/>
        <sub><b>진하은</b></sub>
      </a>
    </td>
  </tr>
</table>

</div>


---
## 주제
### GeoAI 기반 폐주유소 부지활용 의사결정 지원시스템 개발
---
## 목적
### 전기차 보급 확대와 에너지 전환 흐름으로 증가하고 있는 폐주유소 유휴부지에 대해 공간 데이터 기반 AI 분석을 수행하여 각 부지에 적합한 최적의 활용 유형을 추천하는 의사결정 지원 시스템을 구축한다.
---
## 필요성
* 폐주유소의 증가로 인한 **도시 미관 저해, 환경 오염, 안전사고 위험** 등 다양한 사회적 문제가 지속적으로 발생
* 현재는 폐주유소 활용 여부를 행정 담당자가 현장 조사와 주관적 판단에 의존해 결정하는 한계 존재
* 교통량, 인구, 상권, 관광 데이터 등 다양한 공공데이터가 축적되고 있음에도 이를 종합적으로 분석하여 활용하는 시스템 부족</br>
<img width="6600" height="3713" alt="image" src="https://github.com/user-attachments/assets/880fdc09-2e3c-4c6d-a9cb-1501ed6ab249" />

* 따라서 데이터 기반의 객관적인 폐주유소 활용 방안 추천 시스템이 필요함

---

## 1. 구현방법

### 데이터 구성 체계
<img width="1561" height="432" alt="image" src="https://github.com/user-attachments/assets/700a568f-34f2-40bb-bdb6-3f26df3bd194" />

### 활용방안 데이터 기준
<img width="1157" height="630" alt="image" src="https://github.com/user-attachments/assets/fbae7cb1-1b4a-46ff-9006-43cce5f6cbf6" />

<br>

### 알고리즘 설계

![alt text](docs/algorithm.png)

---

## 2. 수행내용

### 필지 데이터 분석 

<img width="1253" height="576" alt="image" src="https://github.com/user-attachments/assets/413cc2ec-6683-4b34-836a-b6813c1f79ff" />

* QGIS를 사용하여 공간 데이터 통합
* PostgreSQL DB에서 공간 데이터 베이스 구축
* PostGIS를 활용하여 공간 연산 

<img width="1355" height="520" alt="image" src="https://github.com/user-attachments/assets/dfdec09c-4721-4c7f-b642-e8bf55bfe1d6" />


### 모델 개선
<img width="1301" height="622" alt="image" src="https://github.com/user-attachments/assets/e5f896cd-5457-4015-8e9c-e296b5e9afc2" />

* 공간 분석으로 산출한 데이터 + 비공간 지표 => 학습 데이터셋 구성
* 랜덤 포레스트 분류기를 사용하여 도시 공간 패턴을 다수의 의사 결정 트리로 학습


### 모델 핵심 피처 변수

![alt text](docs/importance.png)


### 서비스 구조
<img width="1139" height="660" alt="image" src="https://github.com/user-attachments/assets/67b9764c-1342-4bf7-b031-5f7006590e34" />

---

## 3. 결과

<img width="2260" height="1243" alt="image" src="https://github.com/user-attachments/assets/73a1fba6-3769-447b-96bf-963846f5392a" />

* 주유소 마커 선택 시 표시되는 사이트 이미지

<img width="1380" height="632" alt="image" src="https://github.com/user-attachments/assets/345c9a80-88d6-47a0-87d1-8917bdf336cf" />

* 보고서 분석 결과 예시 (LLM 출력)
---

## Tech Stack

![Python](https://img.shields.io/badge/Python-3.10-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110-green.svg)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue.svg)
![PostGIS](https://img.shields.io/badge/PostGIS-3.3-green.svg)
![QGIS](https://img.shields.io/badge/QGIS-3.34-brightgreen.svg)
![Docker](https://img.shields.io/badge/Docker-Enabled-blue.svg)
![Kakao API](https://img.shields.io/badge/Kakao%20API-POI-yellow.svg)
![RandomForest](https://img.shields.io/badge/ML-RandomForest-orange.svg)
![Vercel](https://img.shields.io/badge/Vercel-Hosting-black.svg)
![AWS](https://img.shields.io/badge/AWS-EC2-orange.svg)

---
