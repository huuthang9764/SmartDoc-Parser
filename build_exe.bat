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

echo [3/3] Dang bien dich thanh 1 file .exe duy nhat (Co the mat 1-2 phut)...
:: --onefile: Tao ra 1 file .exe duy nhat (De dang gui cho nguoi khac, chi can 1 file la chay ngay)
:: --add-data: Copy thu muc templates vao trong ban build
:: --console: Giu lai man hinh den de nguoi dung biet server dang chay
pyinstaller --noconfirm --onefile --console --name "SmartDoc-Parser" --add-data "templates;templates" app.py

echo.
echo ========================================
echo HOAN TAT!
echo File .exe duy nhat da duoc xuat ra tai: dist\SmartDoc-Parser.exe
echo Ban chi can copy dung file SmartDoc-Parser.exe nay gui cho nguoi dung!
echo ========================================
pause