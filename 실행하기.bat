@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ============================================
echo   Menu Intelligence AI  실행 중...
echo ============================================
echo.
echo  - 백엔드(FastAPI)와 프론트엔드(Next.js)를 각각 새 창에서 켭니다.
echo  - 서버가 완전히 준비되면 브라우저가 자동으로 열립니다.
echo  - 종료하려면 열린 두 개의 검은 창을 닫으세요.
echo.

REM 1) 백엔드 서버 (포트 8000)
start "Menu Intelligence - Backend (8000)" /D "%~dp0backend" cmd /k python -m uvicorn app.main:app --port 8000

REM 2) 프론트엔드 서버 (포트 3000)
start "Menu Intelligence - Frontend (3000)" /D "%~dp0frontend" cmd /k npm run dev

REM 3) 프론트엔드(3000)가 실제로 응답할 때까지 기다렸다가 브라우저 열기 (최대 약 90초)
echo  서버 준비를 기다리는 중입니다... (첫 실행은 30초~1분 걸릴 수 있어요)
set /a tries=0
:waitloop
set /a tries+=1
if %tries% gtr 45 goto giveup
timeout /t 2 >nul
curl -s -o nul http://localhost:3000
if errorlevel 1 (
  echo    ... 준비 중 (%tries%)
  goto waitloop
)

echo.
echo  준비 완료! 브라우저를 엽니다.
start http://localhost:3000
goto done

:giveup
echo.
echo  [알림] 서버가 예상보다 늦게 켜지고 있습니다.
echo  잠시 후 브라우저 주소창에 직접 입력해 보세요:  http://localhost:3000
echo  그래도 안 되면 "Frontend (3000)" 검은 창의 오류 메시지를 확인하세요.
start http://localhost:3000

:done
echo.
echo  (이 창은 닫아도 됩니다. 서버는 나머지 두 창에서 계속 실행됩니다.)
pause
