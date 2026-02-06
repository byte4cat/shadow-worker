import discord
from discord.ext import commands, tasks
import asyncio
import random
import logging
import os
from datetime import datetime
from dotenv import load_dotenv
from typing import cast
from plyer import notification

# 環境設定
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
TARGET_GUILD_ID = int(os.getenv("TARGET_GUILD_ID", 0))
TODO_CHANNEL_ID = int(os.getenv("TODO_CHANNEL_ID", TARGET_GUILD_ID)) 
if not TOKEN:
    raise ValueError("❌ 錯誤: DISCORD_TOKEN 未在 .env 檔案中設定")

if not TARGET_GUILD_ID:
    raise ValueError("❌ 錯誤: TARGET_GUILD_ID 未在 .env 檔案中設定")

if not TODO_CHANNEL_ID:
    raise ValueError("❌ 錯誤: TODO_CHANNEL_ID 未在 .env 檔案中設定")

# 解析時間點設定 (例如 07:55)
_start_time_str = os.getenv("TODO_TIME", "07:50")
_end_time_str = os.getenv("TODO_END_TIME", "07:59")
START_H, START_M = map(int, _start_time_str.split(":"))
END_H, END_M = map(int, _end_time_str.split(":"))
# 解析工作日設定
_workdays_str = os.getenv("TODO_WORKDAYS", "0,1,2,3,4")
TODO_WORKDAYS = [int(d.strip()) for d in _workdays_str.split(",")]
# 解析自動回覆語句
_responses_str = os.getenv("REPLY_RESPONSES", "收到,了解,OK，收到,好的,我看一下")
REPLY_RESPONSES = [r.strip() for r in _responses_str.split(",")]
# 解析私訊回覆白名單
_dm_reply_str = os.getenv("DM_REPLY_LIST", "")
DM_REPLY_LIST = [int(i.strip()) for i in _dm_reply_str.split(",") if i.strip()]

Typing_Duration_Max = 60.0

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler("auto_reply.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

class ShadowWorker(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!", 
            self_bot=True, 
            help_command=None, 
        )
        self.target_guild_id = TARGET_GUILD_ID
        self.last_sent_date = ""
        self.dm_reply_list = DM_REPLY_LIST 

    def send_desktop_notification(self, title, message, timeout: int):
        """發送桌面通知 (Support Linux & Mac)"""
        try:
            notification.notify(
                title=title,
                message=message,
                app_name='ShadowWorker',
                timeout=timeout  # Seconds the notification stays on screen
            )
        except Exception as e:
            logging.error(f"桌面通知發送失敗: {e}")

    def calculate_typing_duration(self, text: str, mode: str = "long") -> float:
        """
        計算模擬打字所需時間
        """
        length = len(text)
        if mode == "short":
            duration = min(length * 0.5, 10.0)
        else:
            duration = max(min(length * 0.2, Typing_Duration_Max), 15.0)
        return duration * random.uniform(0.9, 1.1)

    async def on_ready(self):
        user = cast(discord.ClientUser, self.user)
        print("-" * 50)
        print(f"Shadow Worker 已啟動！登入帳號: {user.name}")
        guild = self.get_guild(self.target_guild_id)
        guild_name = guild.name if guild else "未知伺服器"
        print(f"監控目標: {guild_name} (ID: {self.target_guild_id})")

        self.send_desktop_notification(
            "🚀 Shadow Worker 啟動",
            f"帳號: {user.name}\n目標: {guild_name}",
            10
        )

        dm_names = []
        for uid in self.dm_reply_list:
            try:
                u = await self.fetch_user(uid)
                dm_names.append(f"{u.name}({uid})")
            except:
                dm_names.append(str(uid))
        print(f"DM Whitelist: {', '.join(dm_names)}")
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
                    print(f"💡 提示：發送 TODO 時將執行約 {typing_duration:.1f} 秒的「打字中」狀態。")
                else:
                    print("⚠️ 警告：todo.txt 內容為空！")
                    self.send_desktop_notification("⚠️ 警告", "todo.txt 內容為空，將不會發送任務。", 10)
            except Exception as e:
                print(f"❌ 讀取 todo.txt 時發生錯誤: {e}")
                self.send_desktop_notification("❌ 錯誤", "無法讀取 todo.txt 檔案！", 10)
        else:
            print("⚠️ 警告：找不到 todo.txt 檔案！")
            self.send_desktop_notification("❌ 錯誤", "找不到 todo.txt 檔案！", 10)
        
        if not self.daily_todo_task.is_running():
            self.daily_todo_task.start()
            weekdays_map = ["週一", "週二", "週三", "週四", "週五", "週六", "週日"]
            workdays_readable = ", ".join([weekdays_map[d] for d in TODO_WORKDAYS])
            print(f">>> 定時任務已啟動 執行日：{workdays_readable} (隨機時段: {_start_time_str} ~ {_end_time_str})")
        print("-" * 50)
        logging.info(f"系統已啟動...")

    @tasks.loop(minutes=1)
    async def daily_todo_task(self):
        now = datetime.now()
        today_str = now.strftime("%Y-%m-%d")

        # 檢查是否為工作日
        if now.weekday() not in TODO_WORKDAYS:
            return

        # 判斷是否在區間內
        current_total_min = now.hour * 60 + now.minute
        start_total_min = START_H * 60 + START_M
        end_total_min = END_H * 60 + END_M

        if start_total_min <= current_total_min <= end_total_min:
            # 檢查今天是否已經發過
            if self.last_sent_date != today_str:
                # 執行發送流程
                await self.process_daily_todo(end_total_min)
                # 發送成功後，更新日期標記
                self.last_sent_date = today_str
                logging.info(f"📆 今日任務完成標記已更新: {self.last_sent_date}")

    @daily_todo_task.before_loop
    async def before_daily_todo(self):
        """ 快進到下一個整分 0 秒啟動 """
        await self.wait_until_ready()
        now = datetime.now()
        seconds_until_next_minute = 60 - now.second
        if seconds_until_next_minute > 0:
            await asyncio.sleep(seconds_until_next_minute)

    async def process_daily_todo(self, end_total_min: int):
        todo_path = "./todo.txt"
        try:
            if not os.path.exists(todo_path): return
            with open(todo_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
            if not content: return

            # 計算模擬打字時長
            typing_duration = self.calculate_typing_duration(content, mode="long")
            
            # 計算從「現在」到「區間最後一秒」的總剩餘秒數
            now = datetime.now()
            # 建立該時段結束的 datetime (例如今天 07:59:59)
            end_dt = now.replace(hour=END_H, minute=END_M, second=59, microsecond=0)
            remaining_seconds = (end_dt - now).total_seconds()
            
            # 隨機延遲上限 = 剩餘總秒數 - 打字時間 - 緩衝5秒
            # 這樣就算隨機到最大值，訊息也能在區間結束前發出
            max_available_delay = max(0.0, remaining_seconds - typing_duration - 5.0)
            extra_delay = random.uniform(0.0, max_available_delay)

            # 獲取頻道名稱 
            channel = self.get_channel(TODO_CHANNEL_ID) or await self.fetch_channel(TODO_CHANNEL_ID)
            channel_name = getattr(channel, "name", "未知頻道")

            logging.info(
                f"⏰ 命中時段 ({_start_time_str}~{_end_time_str})\n"
                f"📍 目標頻道: #{channel_name}\n"
                f"📊 剩餘時間: {remaining_seconds:.1f}s | 預計打字: {typing_duration:.1f}s\n"
                f"🎲 決定延遲: {extra_delay:.1f}s 後開始輸入\n"
                f"📝 內容預覽:\n{content[:100]}{'...' if len(content) > 100 else ''}\n"
                f"---------------"
            ) 

            await asyncio.sleep(extra_delay)
            await self.send_todo_content(content, typing_duration)

        except Exception as e:
            logging.error(f"❌ 處理發送流程失敗: {e}")

    async def send_todo_content(self, content: str, duration: float):
        try:
            channel = self.get_channel(TODO_CHANNEL_ID) or await self.fetch_channel(TODO_CHANNEL_ID)
            if isinstance(channel, discord.abc.Messageable):
                channel_name = getattr(channel, "name", "未知頻道")
                logging.info(f"開始執行發送流程 | 頻道: #{channel_name}\n--- 內容 ---\n{content}\n-----------")

                async with channel.typing():
                    logging.info(f"⏳ [打字中] 模擬輸入中...")
                    await asyncio.sleep(duration)
                
                await channel.send(content)
                logging.info(f"✅ TODO 已成功發送至 #{channel_name}")

                self.send_desktop_notification(
                    "ShadowWorker: 📔 TODO Sent", 
                    f"Successfully sent to #{channel_name}",
                    30,
                )
        except Exception as e:
            logging.error(f"❌ 發送 TODO 過程中發生錯誤: {e}")

    async def get_username(self, user_id: int) -> str:
        try:
            # First, try to get from cache
            user = self.get_user(user_id)
            if not user:
                # If not in cache, fetch from API
                user = await self.fetch_user(user_id)
            return user.name
        except Exception as e:
            return f"Unknown User ({user_id})"

    async def on_message(self, message: discord.Message):
        user = cast(discord.ClientUser, self.user)
        # 排除自己與其他 Bot
        if message.author.id == user.id or message.author.bot:
            return

        logging.debug("msg author id: {}", message.author.id)

        is_dm = isinstance(message.channel, discord.DMChannel) and (message.author.id in self.dm_reply_list)
        is_mentioned = message.guild and message.guild.id == self.target_guild_id and user.mentioned_in(message)
        
        # 檢查伺服器與提及
        if is_mentioned or is_dm:
            delay = random.randint(5, 15) if is_dm else random.randint(10, 30)
            reply_content = random.choice(REPLY_RESPONSES)
            
            # 安全獲取頻道名稱 (修正 Pyright 報錯)
            channel_name = getattr(message.channel, "name", "私訊")

            # 輸出觸發提示
            source = f"私訊 (來自 {message.author.name})" if is_dm else f"頻道 #{getattr(message.channel, 'name', '未知')}"

            logging.info(f"偵測到 {source}，將於 {delay} 秒後自動回覆...")

            self.send_desktop_notification(
                f"📩 收到來自 {message.author.name} 的訊息",
                f"來源: {source}\n內容: {message.clean_content[:50]}",
                30,
            )

            await asyncio.sleep(delay)

            # 模擬打字過程
            # 基礎隨機打字時間 + 根據字數計算的時間
            typing_wait = random.uniform(1.5, 5.0) + self.calculate_typing_duration(reply_content, mode="short")
          
            try:
                async with message.channel.typing():
                    logging.info(f"⏳ [打字中] 正在模擬輸入內容，請稍候...")
                    await asyncio.sleep(typing_wait)
                    # 回覆並記錄 Log
                    if is_dm:
                        await message.channel.send(reply_content)
                    else:
                        await message.reply(reply_content)

                    self.send_desktop_notification(
                        "✅ 自動回覆已發送",
                        f"對象: {message.author.name}\n回覆內容: {reply_content}",
                        30,
                    )

                    logging.info(f"回覆成功 | 頻道: {channel_name} | 觸發者: {message.author.name} | 延遲: {delay}s | 內容: {reply_content}")
            except Exception as e:
                logging.error(f"回覆失敗: {e}")

# 啟動
if __name__ == "__main__":
    worker = ShadowWorker()
    worker.run(cast(str, TOKEN))
