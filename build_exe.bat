@echo off
chcp 65001 > nul
title Build SmartDoc Parser to EXE
color 0B

echo ========================================
echo   DONG GOI UNG DUNG THANH FILE .EXE
echo ========================================
echo.

echo [1/3] Kich hoat moi truong ao...
call venv\Scripts\activate

echo [2/3] Cai dat PyInstaller...
pip install pyinstaller -q

echo [3/3] Dang bien dich thanh .exe (Co the mat 1-2 phut)...
:: --onedir: Tao ra 1 thu muc chua exe va cac file phu tro (Giup chay nhanh hon onedir)
:: --add-data: Copy thu muc templates vao trong ban build
:: --console: Giu lai man hinh den de nguoi dung biet server dang chay
pyinstaller --noconfirm --onedir --console --name "SmartDoc-Parser" --add-data "templates;templates" app.py

echo.
echo ========================================
echo HOAN TAT!
echo Ung dung da duoc xuat ra tai thu muc: dist\SmartDoc-Parser
echo ========================================
pause