.PHONY: setup run clean

# 變數設定
VENV = venv
PYTHON = $(VENV)/bin/python
PIP = $(VENV)/bin/pip

# 預設動作：顯示說明
help:
	@echo "使用方法:"
	@echo "  make setup  - 建立虛擬環境並安裝依賴"
	@echo "  make run    - 啟動 Self-bot"
	@echo "  make clean  - 移除虛擬環境與 Log"

# 建立環境
setup:
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

# 執行
run:
	$(PYTHON) self_bot.py

# 清理
clean:
	rm -rf $(VENV)
	rm -f auto_reply.log
	find . -type d -name "__pycache__" -exec rm -rf {} +
