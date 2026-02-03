# Shadow Worker (Discord-Self-Bot)

[English] | [[繁體中文](README.zh-TW.md)]

A Python-based personal automation suite designed for Discord. This project integrates asynchronous event handling with background scheduling to perform automated channel maintenance and human-like interaction simulations.

> [!WARNING]
> **Disclaimer**: This project is for educational and research purposes only. Using a self-bot is a violation of the Discord Terms of Service (ToS) and may result in account termination. Use at your own risk.

## Core Features

- 🤖 Human-like Auto-Reply: Monitors mentions in specific guilds and responds after a randomized "thinking" delay and typing simulation.
- 📅 Scheduled Background Tasks: Automatically dispatches content from todo.txt during specified windows (Mon-Fri, 07:50 - 07:58) with randomized jitter.
- ⌨️ Dynamic Typing Simulation: Implements a sophisticated Typing... status based on message length, featuring distinct modes for short replies and long-form content.
- 🛠️ Environment Automation: Includes Makefile (Linux/macOS) and .bat (Windows) scripts for seamless one-click environment setup and deployment.

## 🚀 Quick Start

### Linux/macOS Users:

```bash
make setup  # Create venv and install dependencies
make run    # Start the assistant
```

### Windows Users:

```bash
./run_bot.bat
```

## Configuration

Create a .env file:
```
# Discord Account Token (Self-Bot)
DISCORD_TOKEN=your_account_token

# Target Server ID
TARGET_GUILD_ID=your_target_server_id

# Target Channel ID for sending TODOs
TODO_CHANNEL_ID=your_target_channel_id

# --- Schedule Settings (24-hour format) ---
# Start of the random window
TODO_TIME=07:50
# End of the random window
TODO_END_TIME=07:59

# --- Workday Settings ---
# 0=Mon, 1=Tue, 2=Wed, 3=Thu, 4=Fri, 5=Sat, 6=Sun
# Default: Mon-Fri
TODO_WORKDAYS=0,1,2,3,4

# --- Auto-Response Settings ---
# Comma-separated list of random replies for mentions (@me)
REPLY_RESPONSES=OK,Understood,Got it,On it,I will check it out
```

## Content Preparation
Create a todo.txt file in the root directory and input the content you wish to send on schedule.
