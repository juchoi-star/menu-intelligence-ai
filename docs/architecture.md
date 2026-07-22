# Architecture — Menu Intelligence AI

## 시스템 개요

```
┌─────────────────────┐        multipart/form-data         ┌──────────────────────────┐
│   Next.js (App)     │  ── POST /analysis/compare ──────▶ │   FastAPI (Backend)       │
│   - Dashboard       │        (prev.xlsx, curr.xlsx)      │                           │
│   - 메뉴/가맹점/AI    │ ◀── AnalysisResult (JSON) ───────  │  core.parser  (엑셀 파싱) │
│   - Recharts        │                                    │  core.analyzer(비교 분석) │
│   Context+localStorage                                   │  core.ai      (내러티브)  │
└─────────────────────┘  ── GET /analysis/{id}/report.pdf ─│  services.report (PDF)    │
                                                           │  db.repository(영속화)    │
                                                           └────────────┬──────────────┘
                                                                        │ SQLAlchemy
                                                              ┌─────────▼─────────┐
                                                              │ PostgreSQL/SQLite │
                                                              │  analyses(JSONB)  │
                                                              └───────────────────┘
                                                    OpenAI GPT (선택) ◀── core.ai
```

## 백엔드 계층 (관심사 분리)

| 계층 | 모듈 | 책임 |
|------|------|------|
| **Domain** | `core/parser.py` | 엑셀 → 정규화 `MenuRecord[]` (병합/집계행 처리) |
| | `core/analyzer.py` | 전월/당월 비교 → `AnalysisResult` 구성 |
| | `core/ai.py` | 스토리형 내러티브(GPT 또는 규칙 기반) |
| **Contract** | `models/schemas.py` | Pydantic 응답 스키마 (프론트 타입과 1:1) |
| **Persistence** | `db/models.py`, `db/repository.py` | ORM + Repository 패턴 |
| **Service** | `services/report.py` | PDF 보고서 렌더링(reportlab) |
| **API** | `api/routes/*.py` | HTTP 엔드포인트, 검증, 의존성 주입 |
| **Config** | `config.py` | 환경변수(pydantic-settings) |

### 데이터 흐름 (compare)

```
UploadFile x2
  → parser.parse_excel()  x2        # 각 파일 → ParsedFile(records, period)
  → _order_by_period()              # 조회기간으로 (prev, curr) 정렬
  → analyzer.analyze(prev, curr)    # 메뉴/가맹점/대시보드/인사이트
  → ai.generate_ai_report()         # summary/narratives/recommendations
  → repository.create()             # JSONB 저장
  → UploadResponse(analysis_id, result)
```

## 설계 결정 (ADR 요약)

- **결과 전체를 JSONB로 저장**: 상세 스키마가 넓고 재현이 쉬워 정규화 이득이 적음.
  목록/필터용 핵심 지표만 컬럼으로 승격. (repository에서 캡슐화)
- **AI는 폴백 우선**: 키 없이도 동작해야 하므로 규칙 기반을 1차 시민으로 두고,
  OpenAI는 성공 시 대체·실패 시 자동 폴백.
- **SQLite 폴백**: `DATABASE_URL` 미설정 시 로컬 파일 DB로 MVP 즉시 실행.
- **집계행 제외 방식 파싱**: 이름 기준 화이트리스트 대신 "집계행 블랙리스트"로
  판별해 데이터 결손 행(매출 O·이름 X)도 보존 → 총계와 정확히 일치.

## 프론트엔드 구조

- **App Router** 페이지 7개(Dashboard/메뉴/메뉴상세/가맹점/Report/외부요인/설정).
- 분석 결과는 `AnalysisProvider`(Context + localStorage)에 보관 →
  페이지 이동/새로고침에도 유지, 상세 페이지는 컨텍스트에서 조회.
- `lib/api.ts` API 클라이언트, `lib/format.ts` 표기 유틸, `types/` 백엔드 계약 미러.
- 디자인 토큰(Tailwind)으로 다크 BI 테마 일관 적용.

## 확장 포인트

- `core/ai.py` 프롬프트/모델 교체로 내러티브 품질 향상.
- `external` 라우트/페이지에 Weather·News 수집 파이프라인 추가.
- Repository 인터페이스 유지 → 저장소 교체(예: Supabase RLS) 용이.
