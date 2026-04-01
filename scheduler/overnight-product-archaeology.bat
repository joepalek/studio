@echo off
cd /d "G:\My Drive\Projects\_studio"
if not exist "%~dp0logs" mkdir "%~dp0logs"
echo [%date% %time%] Product Archaeology starting >> "G:\My Drive\Projects\_studio\scheduler\logs\overnight-product-archaeology.log"
set PYTHONIOENCODING=utf-8
python "G:\My Drive\Projects\_studio\product_archaeology_run.py" >> "G:\My Drive\Projects\_studio\scheduler\logs\overnight-product-archaeology.log" 2>&1
echo [%date% %time%] Done >> "G:\My Drive\Projects\_studio\scheduler\logs\overnight-product-archaeology.log"
