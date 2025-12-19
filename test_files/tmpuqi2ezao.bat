@echo off
cd /d "%~dp0"
mkdir "01-文档资料" 2>nul
mkdir "02-图片素材" 2>nul
move "test_doc.docx" "01-文档资料" >nul 2>nul
move "test_image.jpg" "02-图片素材" >nul 2>nul