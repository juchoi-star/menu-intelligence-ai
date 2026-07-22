# 배포 가이드 — 팀원 공유용 상시 서버

스택: **Vercel(프론트) + Render(백엔드) + Supabase(DB)** — 모두 무료 티어로 시작 가능.

> 구조: 팀원 브라우저 → Vercel(Next.js) → (API 호출) → Render(FastAPI) → Supabase(PostgreSQL)

전체 순서:
1. GitHub 에 코드 올리기
2. Supabase 에서 DB 만들기
3. Render 에 백엔드 배포
4. Vercel 에 프론트 배포
5. 백엔드 CORS 에 프론트 주소 등록 → 완성
6. Vercel 주소를 팀원에게 공유

소요: 처음이면 30~40분. 계정 3개(GitHub/Render/Vercel/Supabase) 필요(GitHub 로그인으로 대부분 가입 가능).

---

## 0. GitHub 에 코드 올리기

Vercel·Render 는 GitHub 저장소를 연결해 배포합니다. 프로젝트 폴더에서 터미널(Git Bash)로:

```bash
cd "C:/Users/cjwng/Desktop/menu-intelligence-ai"
git init
git add .
git commit -m "chore: initial commit for deploy"
```

그다음 https://github.com/new 에서 빈 저장소(예: `menu-intelligence-ai`, Private 권장)를 만들고, 안내에 나온 주소로:

```bash
git remote add origin https://github.com/<본인아이디>/menu-intelligence-ai.git
git branch -M main
git push -u origin main
```

> `.gitignore` 가 이미 있어 `.env`·`node_modules`·`*.db` 등 민감/불필요 파일은 올라가지 않습니다.

---

## 1. Supabase — 데이터베이스

1. https://supabase.com → **New project** (이름/비밀번호 설정, 리전은 `Northeast Asia (Seoul)` 권장).
2. 생성 후 **Project Settings → Database → Connection string → URI** 복사.
   - 형태: `postgresql://postgres:[YOUR-PASSWORD]@db.xxxx.supabase.co:5432/postgres`
   - `[YOUR-PASSWORD]` 부분을 프로젝트 생성 시 정한 비밀번호로 바꿉니다.
3. 이 문자열을 **DATABASE_URL** 로 다음 단계(Render)에서 사용합니다.

> 테이블은 백엔드가 처음 켜질 때 자동 생성됩니다(`init_db`). 별도 SQL 실행 불필요.
> (원하면 `database/schema.sql` 을 SQL Editor 에 붙여 인덱스까지 미리 만들 수도 있습니다.)

---

## 2. Render — 백엔드(FastAPI)

1. https://render.com → GitHub 로 로그인 → **New + → Blueprint**.
2. 방금 올린 저장소 선택 → 루트의 `render.yaml` 을 자동 인식합니다.
3. 배포 전 **환경변수(Environment)** 입력:
   | 키 | 값 |
   |----|----|
   | `DATABASE_URL` | (1단계 Supabase URI) |
   | `CORS_ORIGINS` | 일단 `*` 로 두었다가 4단계 후 Vercel 주소로 교체 |
   | `OPENAI_API_KEY` | (선택) 없으면 비워두기 |
4. **Apply / Deploy** → 빌드 완료 후 백엔드 URL 확인.
   - 예: `https://menu-intelligence-backend.onrender.com`
5. 브라우저에서 `https://<백엔드URL>/health` 열어 `{"status":"ok"}` 확인.

> 무료 플랜은 15분 미사용 시 잠들고, 다음 접속 때 30~60초 깨어나는 지연이 있습니다(내부 도구엔 무난).

---

## 3. Vercel — 프론트엔드(Next.js)

1. https://vercel.com → GitHub 로 로그인 → **Add New… → Project** → 저장소 선택.
2. **Root Directory** 를 `frontend` 로 지정(중요! 모노레포라서 하위 폴더 지정 필요).
3. Framework 는 자동으로 **Next.js** 감지됨. 그대로 둡니다.
4. **Environment Variables** 에 추가:
   | 키 | 값 |
   |----|----|
   | `NEXT_PUBLIC_API_BASE` | 2단계 백엔드 URL (예: `https://menu-intelligence-backend.onrender.com`) |
5. **Deploy** → 완료 후 프론트 URL 확인.
   - 예: `https://menu-intelligence-ai.vercel.app`  ← **이게 팀원에게 공유할 주소**

---

## 4. CORS 연결 (마지막 필수 단계)

프론트 주소가 나왔으니, 백엔드가 그 주소의 요청을 허용하도록:

1. Render → 백엔드 서비스 → **Environment** → `CORS_ORIGINS` 값을 Vercel 주소로 변경.
   - 예: `https://menu-intelligence-ai.vercel.app`
   - 여러 개면 콤마로: `https://a.vercel.app,https://b.vercel.app`
2. 저장하면 백엔드가 자동 재배포됩니다.

---

## 5. 확인 & 공유

1. 팀원에게 **Vercel 주소** 공유.
2. 접속 → 전월·당월 엑셀 2개 업로드 → **분석 실행** 이 동작하면 성공.
3. 안 되면 아래 문제 해결 참고.

---

## 문제 해결

| 증상 | 원인/해결 |
|------|-----------|
| 분석 실행 시 네트워크 오류 | Vercel `NEXT_PUBLIC_API_BASE` 오타 또는 Render `CORS_ORIGINS` 미설정. 값 확인 후 재배포 |
| 첫 요청이 느림 | Render 무료 플랜 콜드스타트(정상). 한 번 깨우면 빨라짐 |
| `/health` 500/DB 오류 | `DATABASE_URL` 오타 또는 비밀번호 미치환. Supabase URI 재확인 |
| Vercel 빌드 실패 | Root Directory 가 `frontend` 인지 확인 |
| 파일 업로드 413 | 20MB 초과. `MAX_UPLOAD_MB` 환경변수로 상향 가능 |

## 비용 / 유지

- 세 서비스 모두 **무료 티어**로 소규모 팀 사용에 충분합니다.
- 상시 빠른 응답이 필요하면 Render 백엔드만 유료(약 $7/월)로 올리면 콜드스타트가 사라집니다.
- 코드 수정 후 `git push` 하면 Vercel·Render 가 **자동 재배포**합니다.
