@echo off
chcp 65001 >nul
echo ============================================
echo   AI Research Radar - 一键部署脚本
echo ============================================
echo.

:: 1. 创建网站目录
echo [1/3] 创建网站目录...
if not exist "C:\ai-radar" mkdir "C:\ai-radar"
if not exist "C:\ai-radar\reports" mkdir "C:\ai-radar\reports"
echo       目录: C:\ai-radar

:: 2. 检查 Python
echo [2/3] 检查运行环境...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo       未检测到 Python，将使用 IIS 方案...
    echo       请参考下方手动步骤。
    goto :manual
)
echo       Python 已就绪

:: 3. 启动服务
echo [3/3] 启动 Web 服务（端口 80）...
echo.
echo ============================================
echo   部署完成！
echo   请把网站文件放到 C:\ai-radar 目录下
echo   然后访问: http://你的公网IP
echo ============================================
echo.
cd /d C:\ai-radar
python -m http.server 80
pause
