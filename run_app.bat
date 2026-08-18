@echo off
chcp 65001 > nul
title PDF Data Hub - Dashboard
color 0A

echo ========================================
echo    KHOI DONG HE THONG PDF DATA HUB
echo ========================================
echo.
cd /d "%~dp0"

IF NOT EXIST "venv" (
    echo [1/3] Dang tao moi truong ao venv...
    python -m venv venv
)

echo [2/3] Dang kich hoat moi truong ao...
call venv\Scripts\activate

echo [3/3] Dang kiem tra va cai dat thu vien...
pip install Flask pandas pdfplumber xlsxwriter werkzeug openpyxl -q

if not exist "app.py" (
    echo LOI: Khong tim thay file app.py! Vui long kiem tra lai cau truc thu muc.
    pause
    exit /b
)

if not exist "modules" (
    echo LOI: Khong tim thay thu muc 'modules'! Vui long tao thu muc va them cac file module vao.
    pause
    exit /b
)

echo.
echo ========================================
echo Dashboard da san sang hoat dong!
echo Vui long mo trinh duyet va truy cap:
echo http://localhost:5000
echo ========================================
echo Nhan Ctrl+C de dung server.
echo.

python app.py
pause