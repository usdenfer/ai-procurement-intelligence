@echo off
cd /d "%~dp0"

set VENV_PY=.\.venv\Scripts\python.exe
set PORT=8000

if not exist "%VENV_PY%" (
    echo [ERROR] 未找到虚拟环境 %VENV_PY%
    echo 请先执行以下命令创建并安装依赖：
    echo   python -m venv .venv
    echo   .\.venv\Scripts\python.exe -m pip install -r requirements.txt -r requirements-dev.txt
    echo   .\.venv\Scripts\python.exe -m playwright install chromium
    pause
    exit /b 1
)

if not exist "..\web_keyword_catcher" (
    echo [ERROR] 未找到同级 web_keyword_catcher 仓库（..\web_keyword_catcher）
    echo 请先将其 clone 到本目录的上一级。
    pause
    exit /b 1
)

if not exist ".env" (
    echo [提示] 未找到 .env，入库/问答将因缺少 API Key 而失败。
    echo        请参考 .env 所需字段：EMBEDDING_API_KEY、EMBEDDING_MODEL、EMBEDDING_BASE_URL、DEEPSEEK_API_KEY
)

echo 正在启动 AI 采购情报服务，3 秒后自动打开浏览器 http://127.0.0.1:%PORT%
start "" powershell -NoProfile -Command "Start-Sleep -Seconds 3; Start-Process 'http://127.0.0.1:%PORT%'"
"%VENV_PY%" main.py serve --port %PORT%
pause
