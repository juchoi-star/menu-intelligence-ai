-- ============================================================
-- Menu Intelligence AI - PostgreSQL(Supabase) 스키마
-- ============================================================
-- 백엔드는 개발 편의를 위해 SQLite 로 폴백 실행되지만,
-- 운영에서는 아래 스키마로 Supabase(PostgreSQL)를 사용한다.
--
-- 설계 원칙:
--   - 한 번의 비교 분석 결과 전체를 JSONB(result_json)로 보관(재현/재표시 용이).
--   - 대시보드 목록/필터에 필요한 핵심 지표만 컬럼으로 승격.
-- ============================================================

create extension if not exists "pgcrypto";  -- gen_random_uuid()

create table if not exists analyses (
    id                  uuid primary key default gen_random_uuid(),
    created_at          timestamptz not null default now(),

    prev_label          varchar(16) not null,   -- 예: '2026-05'
    curr_label          varchar(16) not null,   -- 예: '2026-06'
    curr_period_start   date,
    curr_period_end     date,
    scope               varchar(64),            -- 예: '전체 가맹점'

    store_count         integer not null default 0,
    menu_count_curr     integer not null default 0,
    total_sales_curr    numeric(16, 2) not null default 0,
    sales_delta_pct     numeric(8, 2),
    ai_provider         varchar(32) not null default 'rule-based',

    result_json         jsonb not null,         -- 전체 AnalysisResult

    prev_filename       text,
    curr_filename       text
);

comment on table analyses is '월별 POS 비교 분석 결과(전월 vs 당월)';
comment on column analyses.result_json is 'AnalysisResult 전체 직렬화(JSONB)';

-- 최근 목록 조회 최적화
create index if not exists idx_analyses_created_at on analyses (created_at desc);
create index if not exists idx_analyses_curr_label on analyses (curr_label);

-- result_json 내부 탐색(예: 특정 메뉴 코드 포함 분석 찾기) 대비 GIN 인덱스
create index if not exists idx_analyses_result_gin on analyses using gin (result_json);

-- ============================================================
-- (선택) Row Level Security 예시 - Supabase 멀티테넌시 확장 대비
-- ============================================================
-- alter table analyses enable row level security;
-- create policy "read own analyses" on analyses
--   for select using (auth.role() = 'authenticated');
