import discord
from discord.ext import commands, tasks
import asyncio
import random
import logging
import os
from datetime import datetime
from dotenv import load_dotenv
from typing import cast

# 環境設定
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    raise ValueError("環境變數 DISCORD_TOKEN 未設定")

_GUILD_ID_STR = os.getenv("TARGET_GUILD_ID")
if not _GUILD_ID_STR:
    raise ValueError("環境變數 TARGET_GUILD_ID 未設定")
TARGET_GUILD_ID = int(_GUILD_ID_STR)

TODO_CHANNEL_ID = int(os.getenv("TODO_CHANNEL_ID", TARGET_GUILD_ID)) 

Typing_Duration_Max = 30.0

# 日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    handlers=[
        logging.FileHandler("auto_reply.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

class MySelfBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!", 
            self_bot=True, 
            help_command=None, 
        )
        self.target_guild_id = TARGET_GUILD_ID
        self.todo_sent_today = False 

    def calculate_typing_duration(self, text: str, mode: str = "long") -> float:
        """
        計算模擬打字所需時間
        mode "long": 每字 0.05s, 上限 30s (適合 todo.txt)
        mode "short": 每字 0.5s, 上限 10s (適合自動回覆)
        """
        length = len(text)
        
        if mode == "short":
            # 短內容：打字較慢但總時長短
            duration = min(length * 0.5, 10.0)
        else:
            # 長內容：打字較快但總時長長
            duration = min(length * 0.05, Typing_Duration_Max)
            
        # 加入一點隨機浮動 (±10%)，避免每次打字時間都精確到跟機器人一樣
        return duration * random.uniform(0.9, 1.1)

    async def on_ready(self):
        user = cast(discord.ClientUser, self.user)
        print("-" * 50)
        print(f"Self-bot 已啟動！登入帳號: {user.name}")
        guild = self.get_guild(self.target_guild_id)
        guild_name = guild.name if guild else "未知伺服器"
        print(f"監控目標: {guild_name} (ID: {self.target_guild_id})")
        print("-" * 50)

        # 檢查 todo.txt
        todo_path = "./todo.txt"
        if os.path.exists(todo_path):
            try:
                with open(todo_path, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                if content:
                    typing_duration = self.calculate_typing_duration(content, mode="long")
                    print(f"【預讀 todo.txt 成功】內容如下：\n{content}")
                    print(f"💡 提示：發送時將執行約 {typing_duration:.1f} 秒的「打字中」狀態 (上限 {Typing_Duration_Max:.1f}s)。")
                else:
                    print("⚠️ 警告：todo.txt 存在，但是內容是空的！")
            except Exception as e:
                print(f"❌ 讀取 todo.txt 時發生錯誤: {e}")
        else:
            print("⚠️ 警告：找不到 todo.txt 檔案！定時任務將無法發送訊息。")
        
        # 啟動背景定時任務
        if not self.daily_todo_task.is_running():
            self.daily_todo_task.start()
            print(">>> 定時發送 todo.txt 任務已啟動 (週一至週五 07:55~07:59)")
        print("-" * 50)

    @tasks.loop(seconds=60)
    async def daily_todo_task(self):
        now = datetime.now()
        
        # 週一至週五 (0-4)
        if now.weekday() >= 5: 
            return

        # 07:50 ~ 07:58
        target_time = (now.hour == 7 and 50 <= now.minute <= 58)

        if target_time and not self.todo_sent_today:
            extra_delay = random.randint(1, 40)
            logging.info(f"符合時間，等待 {extra_delay} 秒後發送 TODO...")
            await asyncio.sleep(extra_delay)
            
            await self.send_todo_content()
            self.todo_sent_today = True 

        # 每天 08:00 重置
        if now.hour == 8:
            self.todo_sent_today = False

    async def send_todo_content(self):
        todo_path = "./todo.txt"
        if not os.path.exists(todo_path):
            logging.warning(f"找不到 {todo_path}")
            return

        try:
            with open(todo_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
            
            if not content:
                return

            # 先嘗試從快取拿頻道，拿不到再 fetch
            channel = self.get_channel(TODO_CHANNEL_ID)
            if not channel:
                channel = await self.fetch_channel(TODO_CHANNEL_ID)

            if isinstance(channel, discord.abc.Messageable):
                # typing
                async with channel.typing():
                    duration = self.calculate_typing_duration(content, mode="long")
                    await asyncio.sleep(duration)

                await channel.send(content)
                logging.info(f"[{datetime.now()}] TODO 已發送")
        except Exception as e:
            logging.error(f"發送 TODO 失敗: {e}")

    async def on_message(self, message: discord.Message):
        user = cast(discord.ClientUser, self.user)
        if message.author.id == user.id or message.author.bot:
            return
        
        if message.guild and message.guild.id == self.target_guild_id:
            if user.mentioned_in(message):
                delay = random.randint(10, 30)
                logging.info(f"偵測到 Tag (來自 {message.author.name})")
                await asyncio.sleep(delay)

                responses = ["收到", "了解", "OK，收到", "好的", "我看一下"]
                reply = random.choice(responses)
                
                # typing
                async with message.channel.typing():
                    await asyncio.sleep(random.uniform(1.5, 10)+self.calculate_typing_duration(reply, mode="short"))
                try:
                    await message.reply(reply)
                    logging.info(f"回覆成功 | 觸發者: {message.author.name}")
                except Exception as e:
                    logging.error(f"回覆失敗: {e}")

# 啟動
bot = MySelfBot()
bot.run(TOKEN)
