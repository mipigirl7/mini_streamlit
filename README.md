# 📊 마케팅 채널 기여도 분석 & 예산 시뮬레이터

> 광고 채널 성과를 한눈에 비교하고, 예산 배분을 실시간으로 시뮬레이션하는 마케팅 의사결정 대시보드

**🔗 Live Demo:** [https://miniapp-kjkvfieyzwzbhbzd8zbvdp.streamlit.app/](https://miniapp-kjkvfieyzwzbhbzd8zbvdp.streamlit.app/)

---

## 📌 프로젝트 개요

마케터와 데이터 분석가가 실제 업무에서 겪는 핵심 질문에 답하는 도구입니다.

> *"어떤 채널에 예산을 더 써야 할까?"*  
> *"지금 가장 효율 나쁜 채널이 어디야?"*  
> *"예산을 이렇게 바꾸면 매출이 얼마나 달라질까?"*

Google · Meta · Instagram · Kakao Ads · Naver SA 5개 광고 채널의 12개월 성과 데이터를 분석하고, 슬라이더로 예산 비율을 조정하면 예상 매출이 실시간으로 계산됩니다.

---

## 🖥️ 화면 구성

| 페이지 | 내용 |
|--------|------|
| 🏠 **KPI 요약** | 총 광고비 · 매출 · ROAS · CAC · 전환율 + 즉시 액션 TOP 3 |
| 📈 **채널 성과** | 월별 ROAS 추이 / 광고비 vs 매출 / 전환율 / 기여도 비교 (Last Click vs Linear) |
| 🎛️ **예산 시뮬레이터** | 채널별 예산 비율 슬라이더 → 현재 vs 시뮬레이션 파이차트 + 예상 ROAS·매출 실시간 계산 |
| 💡 **인사이트** | 자동 패턴 탐지 (숨은 보석 / 성과 급락 / 예산 낭비 / Q4 시즌) + 채널 종합 점수 |

---

## ⚙️ 핵심 기능

### 1. 마케팅 KPI 계산
- **ROAS** (Return on Ad Spend) = 매출 ÷ 광고비
- **CAC** (Customer Acquisition Cost) = 광고비 ÷ 전환수
- **CVR** (Conversion Rate) = 전환수 ÷ 클릭수 × 100
- **CTR** (Click-Through Rate) = 클릭수 ÷ 노출수 × 100

### 2. 기여도 모델 비교
- **Last Click Attribution**: 마지막 클릭 채널에 전환 100% 귀속
- **Linear Attribution**: 광고비 비율 기준으로 전환 균등 배분
- 두 모델의 채널별 기여도 차이를 시각적으로 비교

### 3. 자동 인사이트 엔진
데이터 패턴을 자동으로 탐지해 액션 카드로 표시합니다.

| 인사이트 유형 | 탐지 로직 |
|--------------|-----------|
| 🔮 숨은 보석 | 예산 하위 30% & ROAS 상위 30%인 채널 |
| 📉 성과 급락 | 최근 3개월 vs 이전 3개월 ROAS 15% 이상 하락 |
| 💸 예산 낭비 | 예산 상위 40% & ROAS 전체 평균 미달 |
| 🎄 Q4 시즌 기회 | 11~12월 ROAS가 연간 평균 대비 10% 이상 높을 때 |

### 4. 예산 시뮬레이터
- 총 예산 고정 상태에서 채널별 배분 비율만 변경
- 변경 즉시 예상 매출·ROAS 계산 (채널별 과거 ROAS 기반)
- 현재 vs 시뮬레이션 파이차트 나란히 비교

### 5. 실시간 외부 API 연동
- **Exchange Rate API** (`open.er-api.com`) — 실시간 USD/KRW 환율 표시
- API 호출 실패 시 fallback 값으로 자동 대체 (오류 없이 동작 보장)
- `@st.cache_data(ttl=3600)` 로 1시간 캐싱

---

## 📁 프로젝트 구조

```
.
├── app.py                          # 메인 Streamlit 앱
├── requirements.txt                # 패키지 의존성
└── data/
    └── marketing_performance.csv   # 광고 채널 성과 데이터 (60행)
```

---

## 📊 데이터 설명

**파일:** `data/marketing_performance.csv`  
**구성:** 5개 채널 × 12개월 = 60행 (2024-01 ~ 2024-12)

| 컬럼 | 설명 |
|------|------|
| `month` | 연월 (YYYY-MM-DD) |
| `channel` | 광고 채널명 |
| `spend` | 광고비 (원) |
| `impressions` | 노출수 |
| `clicks` | 클릭수 |
| `conversions` | 전환수 (구매) |
| `revenue` | 매출 (원) |

**데이터에 심어진 의도적 패턴 (분석 연습용):**
- Instagram: 7~9월 ROAS 35% 급락 (크리에이티브 피로 시나리오)
- Kakao Ads: 예산 소규모이지만 ROAS 상위권 (숨은 보석 시나리오)
- Google Ads: 하반기 꾸준한 성과 상승 트렌드
- 전 채널 Q4(11~12월) 시즌 효과 반영

---

## 🛠️ 기술 스택

| 분류 | 기술 |
|------|------|
| 대시보드 | Streamlit |
| 시각화 | Plotly Express / Plotly Graph Objects |
| 데이터 처리 | Pandas, NumPy |
| 외부 API | Exchange Rate API (무료, 인증 불필요) |
| 배포 | Streamlit Cloud |

---

## 🚀 로컬 실행 방법

```bash
# 1. 레포지토리 클론
git clone https://github.com/mipigirl7/mini_streamlit.git
cd mini_streamlit

# 2. 패키지 설치
pip install -r requirements.txt

# 3. 실행
streamlit run app.py
```

브라우저에서 `http://localhost:8501` 접속

---

## 💡 사용 시나리오

1. **월간 마케팅 리뷰**: KPI 요약 페이지에서 전체 성과 파악 → 즉시 조치 필요 항목 확인
2. **채널 전략 수립**: 채널 성과 페이지에서 ROAS 추이 및 기여도 비교 → 집중 채널 선정
3. **예산 조정 회의**: 시뮬레이터로 여러 시나리오 즉석 비교 → 최적 배분안 확정
4. **보고서 작성**: 인사이트 페이지의 자동 진단 카드를 바탕으로 액션 아이템 도출
