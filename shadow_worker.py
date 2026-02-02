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

Typing_Duration_Max = 60.0

# 日誌設定：統一時間戳記格式
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
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
        """
        length = len(text)
        if mode == "short":
            duration = min(length * 0.5, 10.0)
        else:
            duration = max(length * 0.5, Typing_Duration_Max)
        return duration * random.uniform(0.9, 1.1)

    async def on_ready(self):
        user = cast(discord.ClientUser, self.user)
        print("-" * 50)
        print(f"Shadow Worker 已啟動！登入帳號: {user.name}")
        guild = self.get_guild(self.target_guild_id)
        guild_name = guild.name if guild else "未知伺服器"
        print(f"監控目標: {guild_name} (ID: {self.target_guild_id})")
        todo_channel = self.get_channel(TODO_CHANNEL_ID)
        if not todo_channel:
            try:
                todo_channel = await self.fetch_channel(TODO_CHANNEL_ID)
            except:
                todo_channel = None
        
        todo_name = getattr(todo_channel, "name", "未知頻道/私訊")
        print(f"TODO 頻道: #{todo_name} (ID: {TODO_CHANNEL_ID})")

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
                    print("-" * 50)
                    print(f"💡 提示：發送時將執行約 {typing_duration:.1f} 秒的「打字中」狀態。")
                else:
                    print("⚠️ 警告：todo.txt 內容為空！")
            except Exception as e:
                print(f"❌ 讀取 todo.txt 時發生錯誤: {e}")
        else:
            print("⚠️ 警告：找不到 todo.txt 檔案！")
        
        if not self.daily_todo_task.is_running():
            self.daily_todo_task.start()
            print(">>> 定時任務已啟動 (週一至週五 07:50~07:58)")
        print("-" * 50)

    @tasks.loop(seconds=60)
    async def daily_todo_task(self):
        now = datetime.now()
        if now.weekday() >= 5: return
        
        # 07:50 ~ 07:58
        if (now.hour == 7 and 50 <= now.minute <= 58) and not self.todo_sent_today:
            extra_delay = random.randint(1, 40)
            logging.info(f"符合時間，等待 {extra_delay} 秒後發送 TODO...")
            await asyncio.sleep(extra_delay)
            await self.send_todo_content()
            self.todo_sent_today = True 

        if now.hour == 8:
            self.todo_sent_today = False

    async def send_todo_content(self):
        todo_path = "./todo.txt"
        try:
            with open(todo_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
            if not content: return

            channel = self.get_channel(TODO_CHANNEL_ID) or await self.fetch_channel(TODO_CHANNEL_ID)

            if isinstance(channel, discord.abc.Messageable):
                async with channel.typing():
                    duration = self.calculate_typing_duration(content, mode="long")
                    await asyncio.sleep(duration)
                await channel.send(content)
                logging.info("TODO 已發送")
        except Exception as e:
            logging.error(f"發送 TODO 失敗: {e}")

    async def on_message(self, message: discord.Message):
        user = cast(discord.ClientUser, self.user)
        # 排除自己與其他 Bot
        if message.author.id == user.id or message.author.bot:
            return
        
        # 檢查伺服器與提及
        if message.guild and message.guild.id == self.target_guild_id:
            if user.mentioned_in(message):
                delay = random.randint(10, 30)
                responses = ["收到", "了解", "OK，收到", "好的", "我看一下", "了解，處理中"]
                reply_content = random.choice(responses)
                
                # 安全獲取頻道名稱 (修正 Pyright 報錯)
                channel_name = getattr(message.channel, "name", "私訊")

                # 輸出觸發提示
                logging.info(f"偵測到 Tag (來自 {message.author.name})，將於 {delay} 秒後自動回覆...")
                
                # 等待隨機延遲
                await asyncio.sleep(delay)

                # 模擬打字過程
                # 基礎隨機打字時間 + 根據字數計算的時間
                typing_wait = random.uniform(1.5, 5.0) + self.calculate_typing_duration(reply_content, mode="short")
                
                try:
                    async with message.channel.typing():
                        await asyncio.sleep(typing_wait)
                    
                    # 回覆並記錄 Log
                    await message.reply(reply_content)
                    logging.info(f"回覆成功 | 頻道: {channel_name} | 觸發者: {message.author.name} | 延遲: {delay}s | 內容: {reply_content}")
                except Exception as e:
                    logging.error(f"回覆失敗: {e}")

# 啟動
if __name__ == "__main__":
    bot = MySelfBot()
    bot.run(TOKEN)
