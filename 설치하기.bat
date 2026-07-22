@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ============================================
echo   Menu Intelligence AI  최초 설치 (1회만)
echo ============================================
echo.

REM --- Python 확인 ---
where python >nul 2>nul
if errorlevel 1 (
  echo [필수] Python 이 설치되어 있지 않습니다.
  echo   https://www.python.org/downloads/  에서 설치하세요.
  echo   설치 화면에서 "Add Python to PATH" 를 반드시 체크하세요!
  echo.
  pause
  exit /b 1
)

REM --- Node.js 확인 ---
where node >nul 2>nul
if errorlevel 1 (
  echo [필수] Node.js 가 설치되어 있지 않습니다.
  echo   https://nodejs.org/  에서 LTS 버전을 설치한 뒤 다시 실행하세요.
  echo.
  pause
  exit /b 1
)

echo [1/2] 백엔드(FastAPI) 패키지 설치 중... (몇 분 걸릴 수 있어요)
python -m pip install -r "%~dp0backend\requirements.txt"
if errorlevel 1 (
  echo.
  echo [오류] 백엔드 패키지 설치 실패. 인터넷 연결을 확인하세요.
  pause
  exit /b 1
)

echo.
echo [2/2] 프론트엔드(Next.js) 패키지 설치 중...
pushd "%~dp0frontend"
call npm install
popd
if errorlevel 1 (
  echo.
  echo [오류] 프론트엔드 패키지 설치 실패. 인터넷 연결을 확인하세요.
  pause
  exit /b 1
)

echo.
echo ============================================
echo   설치 완료!
echo   이제 "실행하기.bat" 을 더블클릭하면 웹앱이 켜집니다.
echo ============================================
pause
