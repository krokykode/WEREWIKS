import os
import sys
import time
import glob
import zipfile
import requests
import pandas as pd
import re
from colorama import Fore, init, Style
from termcolor import colored
from tabulate import tabulate
import subprocess
import pkg_resources
from telethon.sync import TelegramClient
from telethon.errors import SessionPasswordNeededError, PhoneNumberInvalidError

# Конфигурация путей
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASES_DIR = os.path.join(SCRIPT_DIR, 'bases')
TG_SESSION_FILE = os.path.join(SCRIPT_DIR, 'tg_session.session')
TEST_DB_URL = "https://github.com/example/test-bases/archive/refs/heads/main.zip"

# Инициализация цветов
init(autoreset=True)
COLORS = {
    'title': Fore.MAGENTA + Style.BRIGHT,
    'text': Fore.WHITE,
    'option': Fore.CYAN,
    'warning': Fore.YELLOW,
    'error': Fore.RED,
    'success': Fore.GREEN,
    'header': Fore.BLUE + Style.BRIGHT,
    'disclaimer': Fore.RED + Style.BRIGHT
}

def install_dependencies():
    required = {'pandas', 'colorama', 'requests', 'tabulate', 'termcolor', 'telethon'}
    installed = {pkg.key for pkg in pkg_resources.working_set}
    missing = required - installed

    if missing:
        print(COLORS['warning'] + "\nУстановка недостающих зависимостей..." + Style.RESET_ALL)
        python = sys.executable
        subprocess.check_call([python, '-m', 'pip', 'install', *missing], stdout=subprocess.DEVNULL)
        print(COLORS['success'] + "Зависимости успешно установлены!" + Style.RESET_ALL)

def draw_box(text, color=COLORS['title'], width=60):
    border = '╔' + '═' * (width-2) + '╗'
    text_line = '║ ' + text.center(width-4) + ' ║'
    bottom = '╚' + '═' * (width-2) + '╝'
    print(color + border)
    print(color + text_line)
    print(color + bottom + Style.RESET_ALL)

def animated_header():
    frames = [
        r"""
  ___  ____  ___ _____ ___ _  _ _  _____ ___ 
 / _ \/ ___|/ _ \_   _|_ _| \| | |_   _/ __|
| (_) \___ \ (_) || |  | || .` | | | | \__ \
 \___/|____/\___/ |_| |___|_|\_|_| |_| |___/
        """,
        r"""
  ___  ____  ___ _____ ___ _  _ _  _____ ___ 
 / _ \/ ___|/ _ \_   _|_ _| \| | |_   _/ __|
| (_) \___ \ (_) || |  | || .` | | | | \__ \
 \___/|____/\___/ |_| |___|_|\_|_| |_| |___/
 ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
        """,
        r"""
  ___  ____  ___ _____ ___ _  _ _  _____ ___ 
 / _ \/ ___|/ _ \_   _|_ _| \| | |_   _/ __|
| (_) \___ \ (_) || |  | || .` | | | | \__ \
 \___/|____/\___/ |_| |___|_|\_|_| |_| |___/
 ▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒
        """,
        r"""
  ___  ____  ___ _____ ___ _  _ _  _____ ___ 
 / _ \/ ___|/ _ \_   _|_ _| \| | |_   _/ __|
| (_) \___ \ (_) || |  | || .` | | | | \__ \
 \___/|____/\___/ |_| |___|_|\_|_| |_| |___/
 ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
        """
    ]

    for frame in frames:
        os.system('cls' if os.name == 'nt' else 'clear')
        print(COLORS['title'] + frame)
        time.sleep(0.15)

    print(COLORS['header'] + " " * 16 + "v8.0 PRO EDITION\n")
    time.sleep(0.5)

def show_table(data, headers, title=None):
    if title:
        print(COLORS['header'] + f"\n{title}" + Style.RESET_ALL)

    print(tabulate(
        data, 
        headers=headers, 
        tablefmt='fancy_grid',
        maxcolwidths=[None, 30],
        stralign='center',
        numalign='center'
    ) + "\n")

def search_data(query, search_type):
    csv_files = glob.glob(os.path.join(BASES_DIR, '*.csv'))
    found = False

    for file in csv_files:
        try:
            df = pd.read_csv(
                file,
                sep=',',
                engine='python',
                dtype=str,
                on_bad_lines='skip',
                encoding='utf-8',
                quotechar='"',
                escapechar='\\'
            )

            target_columns = []
            if search_type == 'phone':
                target_columns = [col for col in df.columns if any(kw in col.lower() for kw in ['phone', 'number', 'tel'])]
            elif search_type == 'email':
                target_columns = [col for col in df.columns if any(kw in col.lower() for kw in ['email', 'mail', 'e-mail'])]
            elif search_type == 'username':
                target_columns = [col for col in df.columns if any(kw in col.lower() for kw in ['user', 'nick', 'login', 'username', 'account'])]

            for col in target_columns:
                clean_series = df[col].astype(str).str.replace(r'\x1b\[[0-9;]*m', '', regex=True)
                try:
                    pattern = re.escape(query)
                    results = df[clean_series.str.contains(pattern, case=False, na=False, regex=True)]
                except Exception as e:
                    print(COLORS['error'] + f"\nОшибка в поисковом запросе: {str(e)}" + Style.RESET_ALL)
                    continue

                if not results.empty:
                    found = True
                    data = []
                    headers = [COLORS['header'] + h + Style.RESET_ALL for h in results.columns.tolist()]

                    for _, row in results.iterrows():
                        data_row = []
                        for item in row:
                            if pd.isna(item):
                                data_row.append(COLORS['warning'] + "N/A" + Style.RESET_ALL)
                            else:
                                clean_item = str(item).replace('\x1b[37m', '').replace('\x1b[0m', '')
                                data_row.append(COLORS['text'] + clean_item[:30] + Style.RESET_ALL)
                        data.append(data_row)

                    show_table(
                        data,
                        headers,
                        title=f"Результаты из {os.path.basename(file)} (столбец: {col})"
                    )

        except Exception as e:
            print(COLORS['error'] + f"\nОшибка обработки файла {file}: {str(e)}" + Style.RESET_ALL)

    return found

def setup_telegram_auth():
    print(COLORS['header'] + "\nНастройка доступа к Telegram API:" + Style.RESET_ALL)
    api_id = input("Введите API ID: ")
    api_hash = input("Введите API Hash: ")
    phone = input("Введите номер телефона (с кодом страны): ")

    try:
        with TelegramClient(TG_SESSION_FILE, int(api_id), api_hash) as client:
            client.connect()
            if not client.is_user_authorized():
                client.send_code_request(phone)
                code = input("Введите код из Telegram: ")
                client.sign_in(phone, code)
        print(COLORS['success'] + "Авторизация успешна!" + Style.RESET_ALL)
    except Exception as e:
        print(COLORS['error'] + f"Ошибка авторизации: {str(e)}" + Style.RESET_ALL)
        return False
    return True

def search_telegram_user(username):
    try:
        found_in_db = search_data(username, 'username')

        if not found_in_db:
            if not os.path.exists(TG_SESSION_FILE):
                print(COLORS['warning'] + "\nТребуется авторизация в Telegram!" + Style.RESET_ALL)
                if not setup_telegram_auth():
                    return

            with TelegramClient(TG_SESSION_FILE, 0, '') as client:
                user = client.get_entity(username)

                user_info = [
                    ["ID", user.id],
                    ["Имя", user.first_name],
                    ["Фамилия", user.last_name or "Нет"],
                    ["Username", user.username or "Нет"],
                    ["Бот", "Да" if user.bot else "Нет"],
                    ["Премиум", "Да" if user.premium else "Нет"],
                    ["Статус", user.status or "Неизвестно"],
                    ["Дата регистрации", user.date.strftime("%Y-%m-%d %H:%M:%S")]
                ]

                print(COLORS['success'] + "\nИнформация из Telegram API:" + Style.RESET_ALL)
                print(tabulate(user_info, tablefmt="fancy_grid"))

    except Exception as e:
        print(COLORS['error'] + f"\nОшибка поиска: {str(e)}" + Style.RESET_ALL)

def show_about():
    os.system('cls' if os.name == 'nt' else 'clear')
    draw_box("О ПРОГРАММЕ", width=60)

    about_content = [
        (COLORS['header'] + "Разработчик:" + Style.RESET_ALL,
         COLORS['text'] + "@V_488" + Style.RESET_ALL),

        (COLORS['header'] + "Канал:" + Style.RESET_ALL,
         COLORS['success'] + "Bloody Snos" + Style.RESET_ALL),

        (COLORS['header'] + "Описание:" + Style.RESET_ALL,
         COLORS['text'] + "OSINT инструмент для поиска информации\nиз открытых источников" + Style.RESET_ALL),

        (COLORS['header'] + "Особенности:" + Style.RESET_ALL,
         COLORS['text'] + "• Поиск по телефону, email, юзернейму\n• Интеграция с Telegram API\n• Поддержка больших баз данных" + Style.RESET_ALL),

        (COLORS['disclaimer'] + "ВАЖНО:" + Style.RESET_ALL,
         COLORS['disclaimer'] + "Используйте на свой страх и риск!\nРазработчик не несет ответственности\nза ваши действия." + Style.RESET_ALL)
    ]

    print("\n" + "═" * 60)
    for item in about_content:
        print(f"{item[0]:<20} {item[1]}")
    print("═" * 60 + "\n")

    input(COLORS['option'] + "Нажмите Enter чтобы вернуться..." + Style.RESET_ALL)

def manage_bases_menu():
    menu_items = [
        ("1", "Список баз данных"),
        ("2", "Открыть папку с базами"),
        ("3", "Удалить базу"),
        ("4", "Обновить тестовые базы"),
        ("5", "Назад")
    ]

    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        draw_box("УПРАВЛЕНИЕ БАЗАМИ ДАННЫХ", width=60)

        print(COLORS['text'] + "\nМеню управления:\n")
        for item in menu_items:
            print(COLORS['option'] + f" [{item[0]}] " + COLORS['text'] + item[1])

        choice = input(COLORS['option'] + "\n➤ Выберите действие: " + COLORS['text'])

        if choice == '1':
            csv_files = glob.glob(os.path.join(BASES_DIR, '*.csv'))
            if not csv_files:
                print(COLORS['warning'] + "\nНет доступных баз данных!" + Style.RESET_ALL)
            else:
                data = []
                for idx, file in enumerate(csv_files, 1):
                    file_info = [
                        idx,
                        os.path.basename(file),
                        f"{os.path.getsize(file)//1024} KB",
                        time.ctime(os.path.getctime(file))
                    ]
                    data.append(file_info)

                show_table(
                    data,
                    ["#", "Имя файла", "Размер", "Дата создания"],
                    title="Доступные базы данных:"
                )
            input("\nНажмите Enter чтобы продо��жить...")

        elif choice == '2':
            print(COLORS['text'] + f"\nПуть к базам данных: {BASES_DIR}")
            if os.name == 'nt':
                os.startfile(BASES_DIR)
            else:
                subprocess.run(['xdg-open', BASES_DIR])
            input("\nНажмите Enter после добавления файлов...")

        elif choice == '3':
            csv_files = glob.glob(os.path.join(BASES_DIR, '*.csv'))
            if not csv_files:
                print(COLORS['warning'] + "\nНет доступных баз для удаления!" + Style.RESET_ALL)
            else:
                data = [[i+1, os.path.basename(f)] for i, f in enumerate(csv_files)]
                show_table(data, ["#", "Имя файла"], title="Выберите базу для удаления:")

                try:
                    del_choice = int(input(COLORS['option'] + "\n➤ Номер базы: " + COLORS['text'])) - 1
                    os.remove(csv_files[del_choice])
                    print(COLORS['success'] + "\nБаза успешно удалена!" + Style.RESET_ALL)
                except:
                    print(COLORS['error'] + "\nНеверный выбор!" + Style.RESET_ALL)
            input("\nНажмите Enter чтобы продолжить...")

        elif choice == '4':
            download_test_bases()

        elif choice == '5':
            return

        else:
            print(COLORS['error'] + "\nНеверный выбор!" + Style.RESET_ALL)
            time.sleep(1)

def download_test_bases():
    try:
        print(COLORS['text'] + "\nИнициализация загрузки...")
        response = requests.get(TEST_DB_URL, timeout=10)
        zip_path = os.path.join(SCRIPT_DIR, 'test_bases.zip')

        with open(zip_path, 'wb') as f:
            f.write(response.content)

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(BASES_DIR)

        os.remove(zip_path)
        print(COLORS['success'] + "\nТестовые базы успешно загружены!" + Style.RESET_ALL)
        time.sleep(2)

    except Exception as e:
        print(COLORS['error'] + f"\nОшибка загрузки: {str(e)}" + Style.RESET_ALL)
        time.sleep(2)

def main_menu():
    menu_items = [
        ("1", "Поиск по номеру телефона"),
        ("2", "Поиск по email"),
        ("3", "Поиск по Telegram"),
        ("4", "Поиск по юзернейму"),
        ("5", "Управление базами"),
        ("6", "О программе"),
        ("7", "Выход")
    ]

    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        draw_box("OSINT INVESTIGATION TOOL", width=60)

        print(COLORS['text'] + "\nГлавное меню:\n")
        for item in menu_items:
            print(COLORS['option'] + f" [{item[0]}] " + COLORS['text'] + item[1])

        choice = input(COLORS['option'] + "\n➤ Выберите действие: " + COLORS['text'])

        if choice == '1':
            query = input("\nВведите номер телефона: ").strip()
            if query:
                if not search_data(query, 'phone'):
                    print(COLORS['warning'] + "\nСовпадений не найдено" + Style.RESET_ALL)
                input("\nНажмите Enter чтобы продолжить...")

        elif choice == '2':
            query = input("\nВведите email: ").strip()
            if query:
                if not search_data(query, 'email'):
                    print(COLORS['warning'] + "\nСовпадений не найдено" + Style.RESET_ALL)
                input("\nНажмите Enter чтобы продолжить...")

        elif choice == '3':
            username = input("\nВведите Telegram username (@username): ").strip().lstrip('@')
            if username:
                search_telegram_user(username)
            input("\nНажмите Enter чтобы продолжить...")

        elif choice == '4':
            username = input("\nВведите юзернейм: ").strip()
            if username:
                if not search_data(username, 'username'):
                    print(COLORS['warning'] + "\nСовпадений не найдено" + Style.RESET_ALL)
                input("\nНажмите Enter чтобы продолжить...")

        elif choice == '5':
            manage_bases_menu()

        elif choice == '6':
            show_about()

        elif choice == '7':
            print(COLORS['success'] + "\nЗавершение работы..." + Style.RESET_ALL)
            sys.exit()

        else:
            print(COLORS['error'] + "\nНеверный выбор!" + Style.RESET_ALL)
            time.sleep(1)

if __name__ == '__main__':
    install_dependencies()
    os.makedirs(BASES_DIR, exist_ok=True)
    animated_header()
    main_menu()