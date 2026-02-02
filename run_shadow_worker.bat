@echo off
SET VENV_DIR=venv

IF NOT EXIST %VENV_DIR% (
    echo [!] 找不到虛擬環境，正在進行初始化...
    python -m venv %VENV_DIR%
    call %VENV_DIR%\Scripts\activate
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    echo [!] 初始化完成！
) ELSE (
    call %VENV_DIR%\Scripts\activate
)

echo [!] 正在啟動 Shadow Worker...
python shadow_worker.py
pause
