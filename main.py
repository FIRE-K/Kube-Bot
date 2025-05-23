import telebot
import os

BOT_TOKEN = os.environ.get('BOT_TOKEN')
USERS_FILE = 'users.txt'
KUBE_CODE_FILE = 'Kube_code.py'

bot = telebot.TeleBot(BOT_TOKEN)
user_sessions = {}  # {telegram_id: username}

def load_users():
    users = {}
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            for line in f:
                username, password, role = line.strip().split(',')
                users[username] = {'password': password, 'role': role}
    return users

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        for username, data in users.items():
            f.write(f"{username},{data['password']},{data['role']}\n")

def get_user_role(username):
    users = load_users()
    return users.get(username, {}).get('role')

def is_admin(username):
    return get_user_role(username) == 'admin'

@bot.message_handler(commands=['start', 'register'])
def register(message):
    bot.send_message(message.chat.id, "Send username,password to register:")
    bot.register_next_step_handler(message, process_register)

def process_register(message):
    try:
        username, password = message.text.split(',')
        users = load_users()
        if username in users:
            bot.send_message(message.chat.id, "Username exists. Try /login.")
            return
        role = 'admin' if not users else 'user'
        users[username] = {'password': password, 'role': role}
        save_users(users)
        bot.send_message(message.chat.id, f"Registered! Your role: {role}. Now /login.")
    except Exception:
        bot.send_message(message.chat.id, "Invalid format. Use username,password.")

@bot.message_handler(commands=['login'])
def login(message):
    bot.send_message(message.chat.id, "Send username,password to login:")
    bot.register_next_step_handler(message, process_login)

def process_login(message):
    try:
        username, password = message.text.split(',')
        users = load_users()

        ####### Store passwords' cookies ########

        if username in users and users[username]['password'] == password:
            user_sessions[message.from_user.id] = username
            bot.send_message(message.chat.id, f"Logged in as {username}.")
        else:
            bot.send_message(message.chat.id, "Invalid credentials.")
    except Exception:
        bot.send_message(message.chat.id, "Invalid format. Use username,password.")

@bot.message_handler(commands=['profile'])
def profile(message):
    username = user_sessions.get(message.from_user.id)
    if not username:
        bot.send_message(message.chat.id, "Please /login first.")
        return
    role = get_user_role(username)
    bot.send_message(message.chat.id, f"Username: {username}\nRole: {role}")

@bot.message_handler(commands=['users'])
def list_users(message):
    username = user_sessions.get(message.from_user.id)
    if not username or not is_admin(username):
        bot.send_message(message.chat.id, "Admins only.")
        return
    users = load_users()
    text = "\n".join([f"{u}: {d['role']}" for u, d in users.items()])
    bot.send_message(message.chat.id, text or "No users.")

@bot.message_handler(commands=['edit_user'])
def edit_user(message):
    username = user_sessions.get(message.from_user.id)
    if not username or not is_admin(username):
        bot.send_message(message.chat.id, "Admins only.")
        return
    bot.send_message(message.chat.id, "Send: username,newrole (or username,delete)")
    bot.register_next_step_handler(message, process_edit_user)

def process_edit_user(message):
    try:
        users = load_users()
        parts = message.text.split(',')
        if len(parts) != 2:
            raise Exception()
        uname, action = parts
        if uname not in users:
            bot.send_message(message.chat.id, "User not found.")
            return
        if action == 'delete':
            del users[uname]
            save_users(users)
            bot.send_message(message.chat.id, "User deleted.")
        else:
            users[uname]['role'] = action
            save_users(users)
            bot.send_message(message.chat.id, "Role updated.")
    except Exception:
        bot.send_message(message.chat.id, "Invalid format.")

@bot.message_handler(commands=['edit_code'])
def edit_code(message):
    username = user_sessions.get(message.from_user.id)
    if not username or not is_admin(username):
        bot.send_message(message.chat.id, "Admins only.")
        return
    bot.send_message(message.chat.id, "Send new code for Kube_code.py:")
    bot.register_next_step_handler(message, process_edit_code)

def process_edit_code(message):
    with open(KUBE_CODE_FILE, 'w') as f:
        f.write(message.text)
    bot.send_message(message.chat.id, "Kube_code.py updated.")

@bot.message_handler(commands=['code'])
def run_code(message):
    username = user_sessions.get(message.from_user.id)
    if not username:
        bot.send_message(message.chat.id, "Please /login first.")
        return
    bot.send_message(message.chat.id, "Send code as text to run:")
    bot.register_next_step_handler(message, process_run_code)

def process_run_code(message):
    try:
        code = message.text
        # Security: Only allow safe code execution in real use!
        exec_globals = {}
        exec(code, exec_globals)
        bot.send_message(message.chat.id, "Code executed.")
    except Exception as e:
        bot.send_message(message.chat.id, f"Error: {e}")

bot.polling()
