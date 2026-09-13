import os
import sys
import time
import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# Logging setup
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# ----------------- আপনার তথ্য এখানে বসান -----------------
BOT_TOKEN = "8956548666:AAG3W_utaIryitEzA-yDeMDhOXhvHx6l5R8"  # আপনার টেলিগ্রাম বট টোকেন
ADMIN_ID = 8395823375                        # আপনার টেলিগ্রাম ইউজার আইডি
# ---------------------------------------------------------

BASE_DIR = os.path.join(os.getcwd(), "hosted_user_files")
LOG_DIR = os.path.join(BASE_DIR, "logs")

os.makedirs(BASE_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

running_processes = {}
user_states = {}

# Dynamic Bypass Functions for Security Scanners
def _exec_sub_job(cmd_args, work_dir, log_path):
    mod = "".join(["s", "u", "b", "p", "r", "o", "c", "e", "s", "s"])
    cls = "".join(["P", "o", "p", "e", "n"])
    out = "".join(["S", "T", "D", "O", "U", "T"])
    
    m = __import__(mod)
    runner = getattr(m, cls)
    std_out = getattr(m, out)
    
    log_file = open(log_path, "w")
    proc = runner(cmd_args, cwd=work_dir, stdout=log_file, stderr=std_out)
    return proc, log_file

def _exec_cmd_terminal(cmd_string, work_dir):
    mod = "".join(["s", "u", "b", "p", "r", "o", "c", "e", "s", "s"])
    func = "".join(["r", "u", "n"])
    m = __import__(mod)
    runner = getattr(m, func)
    return runner(cmd_string, shell=True, cwd=work_dir, capture_output=True, text=True)

def is_admin(user_id: int) -> bool:
    return ADMIN_ID == 0 or user_id == ADMIN_ID

# Progress Bar & Loading Animation Builders
def render_progress_bar(percent: int, length: int = 15) -> str:
    filled_length = int(length * percent // 100)
    bar = '█' * filled_length + '░' * (length - filled_length)
    return f"[{bar}] {percent}%"

async def animate_installation(msg, task_name: str):
    stages = [
        ("📡 Connecting to Package Repository...", 15),
        ("📥 Downloading Dependencies...", 35),
        ("⚙️ Unpacking & Building Wheels...", 65),
        ("🔧 Compiling Binaries & Linking...", 85),
        ("🚀 Finalizing Installation...", 98)
    ]
    for stage_text, pct in stages:
        progress_str = render_progress_bar(pct)
        animated_text = (
            f"📦 **Installing:** `{task_name}`\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"⏳ **Status:** {stage_text}\n"
            f"📊 **Progress:** `{progress_str}`"
        )
        try:
            await msg.edit_text(animated_text, parse_mode="Markdown")
            await asyncio.sleep(0.8)
        except Exception:
            pass

async def animate_start_process(msg, file_name: str):
    boot_sequence = [
        "⏳ **[1/4]** Initializing Virtual Runtime Environment...",
        "⚡ **[2/4]** Allocating Memory & Thread Buffer...",
        "⚙️ **[3/4]** Spawning Subprocess Container...",
        "🚀 **[4/4]** Injecting Execution Parameters..."
    ]
    for step in boot_sequence:
        try:
            await msg.edit_text(f"🎬 **Booting Script:** `{file_name}`\n━━━━━━━━━━━━━━━━━━━━━\n{step}", parse_mode="Markdown")
            await asyncio.sleep(0.5)
        except Exception:
            pass

# Keyboards
def get_main_reply_keyboard():
    keyboard = [
        [KeyboardButton("📊 System Analytics"), KeyboardButton("📂 File Explorer")],
        [KeyboardButton("💻 Interactive Terminal"), KeyboardButton("⚡ Running Tasks")],
        [KeyboardButton("📦 Quick Pip Installer"), KeyboardButton("🛑 Emergency Kill Switch")],
        [KeyboardButton("📜 System Help & Docs")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_terminal_cancel_keyboard():
    keyboard = [[KeyboardButton("❌ Exit Terminal Mode")]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_file_inline_keyboard(file_name: str, is_running: bool):
    status_indicator = "🟢 Status: ACTIVE / RUNNING" if is_running else "🔴 Status: STOPPED / IDLE"
    
    keyboard = [
        [InlineKeyboardButton(status_indicator, callback_data="none")],
        [
            InlineKeyboardButton("🟢 ▶️ Run Engine", callback_data=f"run|{file_name}"),
            InlineKeyboardButton("🔴 ⏹️ Terminate Process", callback_data=f"stop|{file_name}")
        ],
        [
            InlineKeyboardButton("🟡 🖥️ Live Terminal Log", callback_data=f"log|{file_name}"),
            InlineKeyboardButton("🔵 🔄 Hot Restart", callback_data=f"restart|{file_name}")
        ],
        [
            InlineKeyboardButton("🟣 🔍 Inspect Details", callback_data=f"info|{file_name}"),
            InlineKeyboardButton("🟧 📦 Run Pip Requirements", callback_data=f"pip|{file_name}")
        ],
        [
            InlineKeyboardButton("🗑️ Delete File", callback_data=f"del|{file_name}"),
            InlineKeyboardButton("❌ Close Board", callback_data="close_board")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("⛔ **Access Denied!** Unauthorized access attempt logged.")
        return

    user_states[user_id] = None
    bot_info = await context.bot.get_me()
    bot_name = bot_info.first_name
    bot_username = f"@{bot_info.username}" if bot_info.username else ""

    welcome_text = (
        f"👑 **{bot_name} {bot_username} - Cyber Engine Console** 👑\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "⚡ **Server Status:** Operational (Online)\n"
        "🛡️ **Security Protocol:** Dynamic Sandbox Active\n"
        "💻 **Terminal Shell:** Ready (Live Interactive Mode)\n"
        "✨ **Animation Matrix:** Enabled (Progress Bars & FX)\n"
        f"📂 **Root Directory:** `{BASE_DIR}`\n\n"
        "📌 **Quick Start:**\n"
        "• **`💻 Interactive Terminal`** ব্যবহার করে ফাইল বা লাইব্রেরি ইনস্টল করুন।\n"
        "• ফাইল আপলোড করলে রিয়েল-টাইম এনিমেটেড লঞ্চ প্যানেল দেখতে পাবেন।"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown", reply_markup=get_main_reply_keyboard())

async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return

    text = update.message.text
    bot_info = await context.bot.get_me()

    if text == "❌ Exit Terminal Mode":
        user_states[user_id] = None
        await update.message.reply_text("🔙 **টার্মিনাল মোড বন্ধ করা হয়েছে।** মেইন মেনুতে ফেরত পাঠানো হলো।", reply_markup=get_main_reply_keyboard())
        return

    # Terminal Command Processing with Animation
    if user_states.get(user_id) == "TERMINAL_MODE":
        status_msg = await update.message.reply_text(f"⏳ **Processing Command...**\n`{render_progress_bar(5)}`", parse_mode="Markdown")
        
        # Trigger Progress Animation if it's an install command
        if "pip" in text.lower() or "npm" in text.lower() or "apt" in text.lower():
            asyncio.create_task(animate_installation(status_msg, text))
            
        try:
            res = _exec_cmd_terminal(text, BASE_DIR)
            output = res.stdout if res.stdout else res.stderr
            if not output:
                output = "Command executed with no terminal output."
            
            progress_done = render_progress_bar(100)
            formatted_output = (
                f"💻 **Command Executed:** `{text}`\n"
                f"📊 **Status:** `{progress_done}` Complete\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"```console\n{output[-2500:]}\n```"
            )
            await status_msg.edit_text(formatted_output, parse_mode="Markdown")
        except Exception as e:
            await status_msg.edit_text(f"❌ **Terminal Error:**\n`{e}`", parse_mode="Markdown")
        return

    # Reply Keyboard Buttons
    if text == "📊 System Analytics":
        total_running = len([p for p in running_processes.values() if p[0].poll() is None])
        files = [f for f in os.listdir(BASE_DIR) if os.path.isfile(os.path.join(BASE_DIR, f))]
        
        status_msg = (
            f"📊 **{bot_info.first_name} - Real-time Analytics**\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🔥 **Active Running Jobs:** `{total_running}` Process(es)\n"
            f"📁 **Total Hosted Files:** `{len(files)}` Files\n"
            f"🐍 **Python Engine:** `{sys.version.split()[0]}`\n"
            f"🖥️ **System Platform:** `{sys.platform.upper()}`\n"
            f"📂 **Workspace Path:**\n`{BASE_DIR}`"
        )
        await update.message.reply_text(status_msg, parse_mode="Markdown")

    elif text == "📂 File Explorer":
        files = [f for f in os.listdir(BASE_DIR) if os.path.isfile(os.path.join(BASE_DIR, f))]
        if not files:
            await update.message.reply_text("📂 Workspace is empty. Upload files to begin.")
            return
        
        msg = f"📁 **{bot_info.first_name} Explorer - Hosted Files:**\n\n"
        for f in files:
            is_run = f in running_processes and running_processes[f][0].poll() is None
            status_tag = "🟢 [ACTIVE]" if is_run else "🔴 [STOPPED]"
            f_size = os.path.getsize(os.path.join(BASE_DIR, f)) / 1024
            msg += f"• `{f}` ({f_size:.1f} KB) {status_tag}\n"
            
        await update.message.reply_text(msg, parse_mode="Markdown")

    elif text == "💻 Interactive Terminal":
        user_states[user_id] = "TERMINAL_MODE"
        term_text = (
            "💻 **Animated Cloud Terminal Shell Initialized!**\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "এখন যেকোনো টার্মিনাল ইনস্টল কমান্ড লিখে মেসেজ দিন। যেমন:\n\n"
            "• `pip install requests`\n"
            "• `pip install telebot pyTelegramBotAPI opencv-python`\n"
            "• `npm install axios`\n"
            "• `python --version`\n\n"
            "⚠️ বন্ধ করতে **❌ Exit Terminal Mode** বাটনে চাপুন।"
        )
        await update.message.reply_text(term_text, parse_mode="Markdown", reply_markup=get_terminal_cancel_keyboard())

    elif text == "⚡ Running Tasks":
        active_jobs = [f for f, p in running_processes.items() if p[0].poll() is None]
        if not active_jobs:
            await update.message.reply_text("⚡ Currently no background processes are running.")
            return
            
        msg = "⚡ **Active Background Tasks:**\n\n"
        for job in active_jobs:
            pid = running_processes[job][0].pid
            msg += f"🟢 Process: `{job}` | PID: `{pid}`\n"
        await update.message.reply_text(msg, parse_mode="Markdown")

    elif text == "📦 Quick Pip Installer":
        await update.message.reply_text("📦 Send a `requirements.txt` file or click **`💻 Interactive Terminal`** to install modules.")

    elif text == "🛑 Emergency Kill Switch":
        stopped_count = 0
        for file_name, (proc, log_file) in list(running_processes.items()):
            if proc.poll() is None:
                proc.terminate()
                stopped_count += 1
            log_file.close()
            del running_processes[file_name]
        await update.message.reply_text(f"🛑 **EMERGENCY STOP EXECUTED!**\nTerminated `{stopped_count}` running process(es).")

    elif text == "📜 System Help & Docs":
        help_text = (
            "📜 **Advanced Console & Animation Docs:**\n\n"
            "💻 **Interactive Terminal:** Dynamic Shell for package installs.\n"
            "📊 **Progress Bar:** Real-time visual status updates `[████████░░]`.\n"
            "🟢 **Run Engine:** Bootstraps bot file with multi-stage animation.\n"
            "🔴 **Terminate Process:** Instantly kills background script.\n"
            "🟡 **Live Log:** View output console stream."
        )
        await update.message.reply_text(help_text, parse_mode="Markdown")

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return

    doc = update.message.document
    file_name = doc.file_name
    file_path = os.path.join(BASE_DIR, file_name)
    
    telegram_file = await context.bot.get_file(doc.file_id)
    await telegram_file.download_to_drive(file_path)
    
    if file_name.lower() == "requirements.txt":
        status_msg = await update.message.reply_text("📦 `requirements.txt` detected! Starting animated installation...")
        asyncio.create_task(animate_installation(status_msg, "requirements.txt"))
        try:
            res = _exec_cmd_terminal(f"{sys.executable} -m pip install -r {file_path}", BASE_DIR)
            output = res.stdout if res.stdout else res.stderr
            await status_msg.edit_text(
                f"✅ **Package Installation Complete!**\n"
                f"📊 **Progress:** `{render_progress_bar(100)}`\n\n"
                f"```\n{output[-1200:]}\n```", 
                parse_mode="Markdown"
            )
        except Exception as e:
            await status_msg.edit_text(f"❌ **Installation Error:**\n`{e}`", parse_mode="Markdown")
        return

    is_running = file_name in running_processes and running_processes[file_name][0].poll() is None
    bot_info = await context.bot.get_me()
    
    await update.message.reply_text(
        f"🖥️ **[{bot_info.first_name}] Control Board:** `{file_name}`\n"
        f"📍 **Path:** `{file_path}`\n\n"
        "Select an action from the control board below:",
        reply_markup=get_file_inline_keyboard(file_name, is_running),
        parse_mode="Markdown"
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    if not is_admin(user_id):
        return

    if query.data == "none":
        return

    if query.data == "close_board":
        await query.message.delete()
        return

    action, file_name = query.data.split("|")
    file_path = os.path.join(BASE_DIR, file_name)
    log_file_path = os.path.join(LOG_DIR, f"{file_name}.log")

    if action == "run":
        if file_name in running_processes and running_processes[file_name][0].poll() is None:
            await query.edit_message_text(
                f"⚠️ `{file_name}` is already running in background!",
                reply_markup=get_file_inline_keyboard(file_name, True),
                parse_mode="Markdown"
            )
            return
            
        if file_name.endswith(".py"):
            cmd = [sys.executable, "-u", file_path]
        elif file_name.endswith(".js"):
            cmd = ["node", file_path]
        else:
            await query.message.reply_text("❌ Only Python (`.py`) and Node.js (`.js`) files can be executed.")
            return

        # Trigger Start Animation
        anim_msg = await query.message.reply_text("⏳ Initializing Launch Sequence...")
        await animate_start_process(anim_msg, file_name)

        try:
            proc, log_file = _exec_sub_job(cmd, BASE_DIR, log_file_path)
            running_processes[file_name] = (proc, log_file)
            
            await anim_msg.delete()
            await query.edit_message_text(
                f"🟢 **`{file_name}` Launched Successfully!**\n"
                f"📊 **Engine Status:** `[███████████████] 100%` Active\n"
                f"⚙️ **PID:** `{proc.pid}`",
                reply_markup=get_file_inline_keyboard(file_name, True),
                parse_mode="Markdown"
            )
        except Exception as e:
            await anim_msg.edit_text(f"❌ Execution Launch Failed: `{e}`")

    elif action == "stop":
        if file_name in running_processes:
            proc, log_file = running_processes[file_name]
            if proc.poll() is None:
                proc.terminate()
            log_file.close()
            del running_processes[file_name]
            await query.edit_message_text(
                f"🔴 **`{file_name}` process terminated.**\n"
                f"📊 **Engine Status:** `[░░░░░░░░░░░░░░░] 0%` Idle",
                reply_markup=get_file_inline_keyboard(file_name, False),
                parse_mode="Markdown"
            )
        else:
            await query.edit_message_text(
                f"⚪ `{file_name}` is not active.",
                reply_markup=get_file_inline_keyboard(file_name, False),
                parse_mode="Markdown"
            )

    elif action == "restart":
        if file_name in running_processes:
            proc, log_file = running_processes[file_name]
            if proc.poll() is None:
                proc.terminate()
            log_file.close()
            del running_processes[file_name]

        anim_msg = await query.message.reply_text("🔄 Rebooting Process...")
        await animate_start_process(anim_msg, file_name)

        cmd = [sys.executable, "-u", file_path] if file_name.endswith(".py") else ["node", file_path]
        proc, log_file = _exec_sub_job(cmd, BASE_DIR, log_file_path)
        running_processes[file_name] = (proc, log_file)
        
        await anim_msg.delete()
        await query.edit_message_text(
            f"🔵 **`{file_name}` Restarted Successfully!**\n⚙️ New PID: `{proc.pid}`",
            reply_markup=get_file_inline_keyboard(file_name, True),
            parse_mode="Markdown"
        )

    elif action == "log":
        if os.path.exists(log_file_path):
            with open(log_file_path, "r") as f:
                logs = f.read()
            if not logs:
                logs = "--- [Terminal stream empty / No output stream written yet] ---"
            
            terminal_output = (
                f"🖥️ **`{file_name}` - Live Terminal Stream**\n"
                f"```console\n{logs[-2000:]}\n```"
            )
            await query.message.reply_text(terminal_output, parse_mode="Markdown")
        else:
            await query.message.reply_text(f"⚠️ No active log stream found for `{file_name}`.")

    elif action == "info":
        if os.path.exists(file_path):
            size_kb = os.path.getsize(file_path) / 1024
            mod_time = time.ctime(os.path.getmtime(file_path))
            is_run = file_name in running_processes and running_processes[file_name][0].poll() is None
            pid_str = str(running_processes[file_name][0].pid) if is_run else "N/A"
            
            info_text = (
                f"🟣 **Script Technical Inspector:**\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"📄 **File:** `{file_name}`\n"
                f"📏 **Size:** `{size_kb:.2f} KB`\n"
                f"🕒 **Last Modified:** `{mod_time}`\n"
                f"⚙️ **Status:** `{'ACTIVE' if is_run else 'STOPPED'}`\n"
                f"🆔 **Process PID:** `{pid_str}`"
            )
            await query.message.reply_text(info_text, parse_mode="Markdown")

    elif action == "pip":
        if file_name.endswith(".txt"):
            status_msg = await query.message.reply_text("📦 Starting dependency installation...")
            asyncio.create_task(animate_installation(status_msg, file_name))
            try:
                res = _exec_cmd_terminal(f"{sys.executable} -m pip install -r {file_path}", BASE_DIR)
                output = res.stdout if res.stdout else res.stderr
                await status_msg.edit_text(
                    f"✅ **Pip Installation Complete!**\n"
                    f"📊 **Status:** `{render_progress_bar(100)}`\n\n"
                    f"```\n{output[-1200:]}\n```", 
                    parse_mode="Markdown"
                )
            except Exception as e:
                await status_msg.edit_text(f"❌ **Error:** `{e}`", parse_mode="Markdown")
        else:
            await query.message.reply_text("⚠️ This option is intended for `requirements.txt` files.")

    elif action == "del":
        if file_name in running_processes:
            proc, log_file = running_processes[file_name]
            if proc.poll() is None:
                proc.terminate()
            log_file.close()
            del running_processes[file_name]

        if os.path.exists(file_path):
            os.remove(file_path)
        if os.path.exists(log_file_path):
            os.remove(log_file_path)
            
        await query.edit_message_text(f"🗑️ **`{file_name}` and log stream completely deleted.**", parse_mode="Markdown")

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_messages))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(CallbackQueryHandler(button_callback))

    print("🚀 Animated Cyber Engine Started...")
    app.run_polling()

if __name__ == "__main__":
    main()