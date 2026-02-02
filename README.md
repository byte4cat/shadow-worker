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
DISCORD_TOKEN=your_account_token
TARGET_GUILD_ID=target_server_id
TODO_CHANNEL_ID=target_channel_id
```

## Content Preparation
Create a todo.txt file in the root directory and input the content you wish to send on schedule.
