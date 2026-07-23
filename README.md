# Menu Intelligence AI

멀티 브랜드 POS 매출 분석 **AI BI 플랫폼**. 첫 화면에서 브랜드를 선택합니다:
- **생전포차** (포차, 11개 가맹점): `.xlsx` "메뉴별 매출 순위 집계" — 가맹점×분류×메뉴, 주류/음식/기타 그룹, 할인·이익률.
- **피씨 (PC방)**: HTML(`.xls`) "매장통계 > 상품 > 순위" — 상품 매출·판매개수·객단가·순위·분류별 증감.

두 브랜드 모두 **월별 파일 2개 업로드 → 전월 대비 자동 비교 분석**.

아래는 원조 생전포차 기능 설명입니다.

---

외식 프랜차이즈(생전포차 체인) 메뉴개발팀을 위한 **AI 기반 메뉴 매출 분석 BI 플랫폼**.

매달 POS에서 추출한 **"메뉴별 매출 순위 집계"** 엑셀 파일 2개(전월·당월)를 업로드하면,
AI가 자동으로 성장률·감소율·순위변화·기여도·할인율·이익률·신규/중단 메뉴·가맹점별 특징을
분석하고 **스토리형 인사이트**와 **PDF 보고서**를 생성합니다.

> **첫 번째 목표(MVP): 월별 POS 파일 2개 업로드 → 자동 비교 분석** ✅ 완료

---

## ✨ 핵심 기능

| 영역 | 내용 |
|------|------|
| **자동 파싱** | 병합셀 Forward-Fill, Total/소계/총계/중복행 제거. 실제 총계블록과 100% reconcile 검증 |
| **자동 전/당월 판별** | 파일의 조회기간을 읽어 업로드 순서와 무관하게 전월/당월 자동 정렬 |
| **대시보드** | 총매출·전월대비·주문건수·이익률·판매메뉴수 + 분류별/기여도 차트 |
| **그룹 분리** | **주류 / 음식 / 기타**로 나눠 분석 — 순위·기여도는 그룹 내에서 계산, 인사이트도 그룹별 제공 |
| **메뉴 분석** | 그룹 탭(전체/주류/음식/기타) + 상승/하락 TOP10, 매출기여도, 주문증가율, 순위상승/하락, 신규/판매중단, **할인 없이 성장한 메뉴** |
| **메뉴 상세** | 전월 대비 주문·매출·순매출·이익·할인율·이익률 + 가맹점별 증감표 |
| **가맹점 분석** | 가맹점 TOP20: 매출·주문·증감률·이익률·할인율 |
| **AI 분석** | 숫자가 아닌 '스토리' — "할인은 줄었는데 매출이 늘었다 → 상품 경쟁력 상승 가능성" |
| **AI Report** | 7단 목차 PDF 보고서 (매출요약→메뉴성장→감소→순위→가맹점→AI분석→추천액션) |
| **외부요인** | Weather/News API 연동 예정 (플레이스홀더) |

---

## 🏗️ 기술 스택

- **Frontend**: Next.js 14 (App Router) · TailwindCSS · Recharts · TypeScript
- **Backend**: FastAPI · Python 3.11+ · Pandas/openpyxl · Pydantic
- **Database**: PostgreSQL (Supabase) — 미설정 시 SQLite 자동 폴백
- **AI**: OpenAI GPT (선택) — 미설정 시 규칙 기반(rule-based) 폴백
- **PDF**: reportlab (내장 CJK 폰트로 한글 렌더링)

---

## 📁 프로젝트 구조

```
menu-intelligence-ai/
├── backend/            # FastAPI 서버
│   ├── app/
│   │   ├── core/       # parser · analyzer · ai  (도메인 로직)
│   │   ├── models/     # Pydantic 스키마
│   │   ├── db/         # SQLAlchemy · Repository 패턴
│   │   ├── services/   # PDF 보고서
│   │   ├── api/routes/ # 엔드포인트
│   │   ├── config.py   # 환경변수 설정
│   │   └── main.py     # 앱 진입점
│   ├── tests/          # 파서 단위 테스트
│   └── requirements.txt
├── frontend/           # Next.js 앱 (7개 페이지)
│   └── src/{app,components,lib,types}
├── database/schema.sql # Supabase(PostgreSQL) 스키마
├── docs/               # PRD · architecture · data-format
└── README.md
```

---

## 🚀 실행 방법

### 1) 백엔드

```bash
cd backend
python -m venv .venv && source .venv/Scripts/activate   # Windows(Git Bash)
pip install -r requirements.txt
cp .env.example .env        # 필요 시 DATABASE_URL / OPENAI_API_KEY 설정
uvicorn app.main:app --reload --port 8000
```

- API 문서: http://localhost:8000/docs
- OpenAI 키 없이도 **규칙 기반 내러티브**로 완전히 동작합니다.

### 2) 프론트엔드

```bash
cd frontend
cp .env.local.example .env.local   # NEXT_PUBLIC_API_BASE 확인
npm install
npm run dev                        # http://localhost:3000
```

### 3) 사용

1. 대시보드 상단 업로드 패널에 **전월·당월 엑셀** 2개 선택 → **분석 실행**
2. Dashboard / 메뉴 분석 / 가맹점 분석 / AI Report 탐색
3. AI Report에서 **PDF 보고서 다운로드**

---

## 🧪 테스트

```bash
cd backend
pytest -q          # 파서 단위 테스트 (집계행 제거 · forward-fill · 결손행 보존)
```

> 실제 5월/6월 데이터로 파싱 결과가 POS 총계블록(총 주문건수·순매출·할인)과
> **정확히 일치**함을 검증했습니다. 자세한 포맷 규칙은 [docs/data-format.md](docs/data-format.md) 참고.

---

## 🌐 팀원 공유 (배포)

상시 접속 가능한 서버로 배포해 팀원과 공유하려면 **[docs/DEPLOY.md](docs/DEPLOY.md)** 참고.
스택: **Vercel(프론트) + Render(백엔드) + Supabase(DB)** — 무료 티어로 시작 가능.
루트의 `render.yaml`(Render Blueprint)과 프로덕션용 환경변수 처리가 준비되어 있습니다.

## 📌 다음 단계 (Roadmap)

- [ ] 외부요인: Weather/News API 연동 및 매출 상관 분석
- [ ] 3개월 이상 시계열 트렌드
- [ ] 가맹점 드릴다운 상세 페이지
- [ ] 사용자 인증 + Supabase RLS 멀티테넌시
- [ ] 원가 데이터 반영 시 정밀 이익률 분석
