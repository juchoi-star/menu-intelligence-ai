"""DATABASE_URL 연결 테스트 (로컬에서 빠르게 확인용).

사용법 (backend 폴더에서):
    python check_db.py "postgresql://postgres.<ref>:<PW>@aws-0-...pooler.supabase.com:5432/postgres"

성공하면 OK 와 서버 버전을, 실패하면 원인(FAIL)을 즉시 보여줍니다.
Render 재배포(수 분)를 기다리지 않고 문자열이 맞는지 검증할 수 있습니다.
"""

from __future__ import annotations

import sys

from sqlalchemy import create_engine, text


def normalize(url: str) -> str:
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg2://", 1)
    if url.startswith("postgresql://") and "+psycopg2" not in url:
        return url.replace("postgresql://", "postgresql+psycopg2://", 1)
    return url


def main() -> int:
    if len(sys.argv) > 1:
        raw = sys.argv[1].strip()
    else:
        raw = input("DATABASE_URL 붙여넣기: ").strip()

    # 흔한 실수 자동 감지
    if "[" in raw or "]" in raw:
        print("⚠️  대괄호 [ ] 가 남아있습니다. [YOUR-PASSWORD] 를 실제 비밀번호로 바꾸세요.")
    if raw != raw.strip() or raw.startswith('"') or raw.startswith("'"):
        print("⚠️  앞뒤에 공백이나 따옴표가 있습니다. 제거하세요.")

    url = normalize(raw)
    try:
        engine = create_engine(url, connect_args={"connect_timeout": 10})
        with engine.connect() as conn:
            ver = conn.execute(text("select version()")).scalar()
        print("\n✅ 연결 성공! 이 문자열을 그대로 Render 의 DATABASE_URL 에 넣으면 됩니다.")
        print("   서버:", str(ver)[:60], "...")
        return 0
    except Exception as exc:  # noqa: BLE001
        print("\n❌ 연결 실패:")
        print("  ", str(exc).splitlines()[0])
        if "password authentication failed" in str(exc):
            print("   → 비밀번호가 틀렸습니다. Supabase 에서 리셋한 '새' 비밀번호가 문자열에 정확히 들어갔는지 확인하세요.")
        elif "could not translate host name" in str(exc) or "Name or service" in str(exc):
            print("   → 호스트 주소 오타입니다. ...pooler.supabase.com 인지 확인하세요.")
        elif "timeout" in str(exc).lower():
            print("   → 네트워크/포트 문제. Session pooler(5432) 문자열인지 확인하세요.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
