import ctypes
import json
import os
import time
from collections import Counter
from config import (
    API_ID,
    API_HASH,
    DATABASE_DIR,
    FILES_DIR,
    TDLIB_PATH,
)


class TelegramClient:
    def __init__(self):
        self.dll_directory = os.add_dll_directory(
            str(TDLIB_PATH.parent)
        )

        self.tdlib = ctypes.CDLL(str(TDLIB_PATH))
        # Отключаем подробные логи TDLib
        self.tdlib.td_set_log_verbosity_level.argtypes = [
            ctypes.c_int
        ]
        self.tdlib.td_set_log_verbosity_level.restype = None

        self.tdlib.td_set_log_verbosity_level(0)


        # Настройка функций TDLib
        self.tdlib.td_json_client_create.argtypes = []
        self.tdlib.td_json_client_create.restype = ctypes.c_void_p

        self.tdlib.td_json_client_send.argtypes = [
            ctypes.c_void_p,
            ctypes.c_char_p,
        ]
        self.tdlib.td_json_client_send.restype = None

        self.tdlib.td_json_client_receive.argtypes = [
            ctypes.c_void_p,
            ctypes.c_double,
        ]
        self.tdlib.td_json_client_receive.restype = ctypes.c_char_p

        self.tdlib.td_json_client_destroy.argtypes = [
            ctypes.c_void_p
        ]
        self.tdlib.td_json_client_destroy.restype = None

        self.client = self.tdlib.td_json_client_create()

        if not self.client:
            raise RuntimeError("Не удалось создать TDLib Client")

        self.authorized = False
        self.request_id = 0

    def send(self, data):
        request = json.dumps(
            data,
            ensure_ascii=False
        ).encode("utf-8")

        self.tdlib.td_json_client_send(
            self.client,
            request
        )

    def receive(self, timeout=1.0):
        result = self.tdlib.td_json_client_receive(
            self.client,
            timeout
        )

        if not result:
            return None

        try:
            return json.loads(result.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return None

    def set_parameters(self):
        self.send({
            "@type": "setTdlibParameters",
            "database_directory": str(DATABASE_DIR),
            "files_directory": str(FILES_DIR),
            "use_test_dc": False,
            "database_encryption_key": "",
            "use_file_database": True,
            "use_chat_info_database": True,
            "use_message_database": True,
            "use_secret_chats": False,
            "api_id": API_ID,
            "api_hash": API_HASH,
            "system_language_code": "ru",
            "device_model": "Windows PC",
            "system_version": "Windows 10",
            "application_version": "1.0",
        })

    def process_authorization(self, state):
        state_type = state.get("@type")

        print(f"\nСостояние Telegram: {state_type}")

        if state_type == "authorizationStateWaitTdlibParameters":
            print("Настраиваем TDLib...")
            self.set_parameters()

        elif state_type == "authorizationStateWaitEncryptionKey":
            self.send({
                "@type": "checkDatabaseEncryptionKey",
                "encryption_key": ""
            })

        elif state_type == "authorizationStateWaitPhoneNumber":
            phone = input(
                "\nВведите номер телефона (+79990000000): "
            ).strip()

            print("\nОтправляем номер в Telegram...")

            self.send({
                "@type": "setAuthenticationPhoneNumber",
                "phone_number": phone
            })

            print("Запрос отправлен. Ожидаем ответ TDLib...")

        elif state_type == "authorizationStateWaitCode":
            code = input(
                "\nВведите код из Telegram: "
            ).strip()

            self.send({
                "@type": "checkAuthenticationCode",
                "code": code
            })

        elif state_type == "authorizationStateWaitPassword":
            import getpass

            password = getpass.getpass(
                "\nВведите пароль двухфакторной защиты: "
            )

            self.send({
                "@type": "checkAuthenticationPassword",
                "password": password
            })

        elif state_type == "authorizationStateReady":
            print("\n================================")
            print("УСПЕШНАЯ АВТОРИЗАЦИЯ TELEGRAM!")
            print("================================")

            self.authorized = True

        elif state_type == "authorizationStateWaitRegistration":
            print("Для этого аккаунта требуется регистрация.")

        elif state_type == "authorizationStateWaitOtherDeviceConfirmation":
            print("Подтвердите вход на другом устройстве.")

        elif state_type == "authorizationStateWaitEmailAddress":
            email = input("\nВведите адрес электронной почты: ")
            self.send({
                "@type": "setAuthenticationEmailAddress",
                "email_address": email
            })

        elif state_type == "authorizationStateWaitEmailCode":
            code = input("\nВведите код из электронной почты: ")
            self.send({
                "@type": "checkAuthenticationEmailCode",
                "code": {
                    "@type": "emailAddressAuthenticationCode",
                    "code": code
                }
            })

        elif state_type == "authorizationStateClosed":
            print("TDLib закрыта.")


    def run(self):
        print("Запуск Telegram Client...")

        try:
            while not self.authorized:
                update = self.receive(1.0)

                if not update:
                    continue

                if update.get("@type") == "updateAuthorizationState":
                    state = update.get("authorization_state", {})
                    self.process_authorization(state)

                elif update.get("@type") == "error":
                    print(
                        "Ошибка TDLib:",
                        update.get("code"),
                        update.get("message")
                    )

            print("\nАвторизация успешна!")
            print("\nЗагружаем список чатов...")

            self.get_chats()

            while True:
                print("\n========== МЕНЮ ==========")
                print("1. Отправить сообщение")
                print("2. Выбрать чат и посмотреть сообщения")
                print("3. Скачать голосовые сообщения")
                print("4. Выход")

                command = input("\nВыбор: ").strip()

                if command == "1":
                    chats = self.get_chats()

                    chat_number = int(input("Номер чата: ")) - 1

                    if chat_number < 0 or chat_number >= len(chats):
                        print("Неверный номер чата.")
                        continue

                    chat_id = chats[chat_number]["id"]

                    message_text = input("Введите сообщение: ")

                    self.send_text_message(chat_id, message_text)

                elif command == "2":
                    self.select_chat()

                elif command == "3":
                    self.get_chats()

                    value = input("\nНомер чата: ").strip()

                    try:
                        index = int(value) - 1

                        if 0 <= index < len(self.chats):
                            chat_id = self.chats[index]["id"]
                            self.download_voices(chat_id)
                        else:
                            print("Неверный номер чата.")

                    except ValueError:
                        print("Нужно ввести номер чата.")

                elif command == "4":
                    break
                
                else:
                    print("Неизвестная команда.")

        except KeyboardInterrupt:
            print("\nОстановка программы...")

        except Exception as error:
            print("\nОшибка:", error)

        finally:
            self.close()


    def close(self):
        if not self.client:
            return

        self.send({"@type": "close"})

        # Ждём подтверждения закрытия TDLib
        deadline = time.monotonic() + 10

        while time.monotonic() < deadline:
            update = self.receive(0.5)

            if update and update.get("@type") == "updateAuthorizationState":
                state = update.get("authorization_state", {})

                if state.get("@type") == "authorizationStateClosed":
                    break

        self.tdlib.td_json_client_destroy(self.client)
        self.client = None

        print("Telegram Client остановлен.")
    
    def request(self, data, timeout=30):
        self.request_id += 1
        extra = str(self.request_id)
        data["@extra"] = extra

        self.send(data)
        deadline = time.monotonic() + timeout

        while time.monotonic() < deadline:
            update = self.receive(1.0)

            if not update:
                continue

            if update.get("@extra") == extra:
                if update.get("@type") == "error":
                    raise RuntimeError(
                        f"TDLib {update.get('code')}: "
                        f"{update.get('message')}"
                    )
                return update

            self.process_update(update)

        raise TimeoutError(
            f"Не дождались ответа: {data.get('@type')}"
        )

    def process_update(self, update):
        update_type = update.get("@type")

        if update_type == "updateAuthorizationState":
            state = update.get("authorization_state", {})
            self.process_authorization(state)

        elif update_type == "error":
            print(
                "Ошибка TDLib:",
                update.get("code"),
                update.get("message")
            )
    
    def get_chats(self):
        chats = []
        seen_ids = set()

        # Основной список и архив
        chat_lists = [
            {"@type": "chatListMain"},
            {"@type": "chatListArchive"}
        ]

        for chat_list in chat_lists:
            try:
                result = self.request({
                    "@type": "getChats",
                    "chat_list": chat_list,
                    "limit": 1000
                })

                for chat_id in result.get("chat_ids", []):
                    if chat_id in seen_ids:
                        continue

                    seen_ids.add(chat_id)

                    chat = self.request({
                        "@type": "getChat",
                        "chat_id": chat_id
                    })

                    chats.append({
                        "id": chat_id,
                        "title": chat.get("title", "Без названия"),
                        "type": chat.get("type", {}).get("@type", "")
                    })

            except Exception as error:
                print("Ошибка получения списка:", error)

        self.chats = chats

        print(f"\nНайдено чатов: {len(chats)}")
        print("=" * 55)

        for index, chat in enumerate(chats, 1):
            print(
                f"{index}. {chat['title']} "
#                f"| {chat['type']} "
#                f"| ID: {chat['id']}"
            )

        return chats

    def get_history(self, chat_id, limit=50):
        from datetime import datetime

        from_message_id = 0

        while True:
            batch = []
            seen_ids = set()

            # Собираем одну порцию из limit сообщений.
            # Если TDLib вернула только одно, запрашиваем следующие.
            while len(batch) < limit:
                remaining = limit - len(batch)

                result = self.request({
                    "@type": "getChatHistory",
                    "chat_id": chat_id,
                    "from_message_id": from_message_id,
                    "offset": 0,
                    "limit": remaining,
                    "only_local": False
                })

                messages = result.get("messages", [])

                if not messages:
                    break

                new_messages = [
                    message for message in messages
                    if message["id"] not in seen_ids
                ]

                if not new_messages:
                    break

                for message in new_messages:
                    seen_ids.add(message["id"])
                    batch.append(message)

                from_message_id = batch[-1]["id"]

                if len(messages) < remaining:
                    # Пробуем получить следующую порцию,
                    # если TDLib вернула меньше запрошенного.
                    continue

            if not batch:
                print("\nБольше сообщений нет.")
                break

            print(f"\nПолучено сообщений: {len(batch)}")
            print("=" * 60)

            # Показываем от старых к новым.
            for message in reversed(batch):
                content = message.get("content", {})
                content_type = content.get("@type", "")

                sender = message.get("sender_id", {})
                sender_id = (
                    sender.get("user_id")
                    or sender.get("chat_id")
                    or "?"
                )

                date = datetime.fromtimestamp(
                    message.get("date", 0)
                ).strftime("%d.%m.%Y %H:%M")

                if content_type == "messageText":
                    text = content.get("text", {}).get("text", "")
                elif content_type == "messageVoiceNote":
                    text = "[ГОЛОСОВОЕ СООБЩЕНИЕ]"
                elif content_type == "messagePhoto":
                    text = "[ФОТО]"
                elif content_type == "messageVideo":
                    text = "[ВИДЕО]"
                elif content_type == "messageDocument":
                    text = "[ФАЙЛ]"
                else:
                    text = f"[{content_type}]"

                print(
                    f"[{date}] "
                    f"ID отправителя {sender_id}: {text}"
                )

            command = input(
                "\nEnter — следующие 50 | q — назад: "
            ).strip().lower()

            if command == "q":
                break


    def select_chat(self):
        if not getattr(self, "chats", None):
            print("Сначала загрузи список чатов.")
            return

        while True:
            value = input(
                "\nВведи номер чата или q для выхода: "
            ).strip().lower()

            if value == "q":
                return

            try:
                index = int(value) - 1

                if index < 0 or index >= len(self.chats):
                    print("Неверный номер.")
                    continue

                chat = self.chats[index]

                print(f"\nОткрываем: {chat['title']}")
                self.get_history(chat["id"])

            except ValueError:
                print("Введи номер чата.")

    
    def download_voices(self, chat_id, total_limit=500):
        from pathlib import Path
        import shutil

        print("\nИщу голосовые сообщения...")

        voice_dir = Path("downloads/voice")
        voice_dir.mkdir(parents=True, exist_ok=True)

        from_message_id = 0
        all_messages = []
        seen_ids = set()

        # Получаем историю сообщений
        while len(all_messages) < total_limit:
            remaining = min(100, total_limit - len(all_messages))

            result = self.request({
                "@type": "getChatHistory",
                "chat_id": chat_id,
                "from_message_id": from_message_id,
                "offset": 0,
                "limit": remaining,
                "only_local": False
            })

            messages = result.get("messages", [])

            if not messages:
                break

            new_messages = [
                message for message in messages
                if message["id"] not in seen_ids
            ]

            if not new_messages:
                break

            for message in new_messages:
                seen_ids.add(message["id"])
                all_messages.append(message)

            from_message_id = all_messages[-1]["id"]

            if len(messages) < remaining:
                continue

        print(f"Проверено сообщений: {len(all_messages)}")

        # Ищем именно голосовые сообщения
        voice_messages = []

        for message in all_messages:
            content = message.get("content", {})

            if content.get("@type") == "messageVoiceNote":
                voice_note = content.get("voice_note", {})
                file_info = voice_note.get("voice", {})

                if file_info.get("id"):
                    voice_messages.append({
                        "message_id": message["id"],
                        "file_id": file_info["id"]
                    })

        print(f"Найдено голосовых сообщений: {len(voice_messages)}")

        if not voice_messages:
            print("Голосовые сообщения не найдены.")
            return

        # Скачиваем голосовые
        downloaded = 0

        for voice in voice_messages:
            print(f"\nСкачиваю сообщение {voice['message_id']}...")

            try:
                result = self.request({
                    "@type": "downloadFile",
                    "file_id": voice["file_id"],
                    "priority": 16,
                    "offset": 0,
                    "limit": 0,
                    "synchronous": True
                }, timeout=300)

                local = result.get("local", {})
                source_path = local.get("path")

                if not local.get("is_downloading_completed") or not source_path:
                    print("Не удалось скачать файл.")
                    continue

                destination = (
                    voice_dir /
                    f"chat_{chat_id}_message_{voice['message_id']}.ogg"
                )

                shutil.copy2(source_path, destination)

                downloaded += 1
                print(f"Сохранено: {destination}")

            except Exception as error:
                print(f"Ошибка скачивания: {error}")

        print(f"\nГотово! Скачано голосовых: {downloaded}/{len(voice_messages)}")

    def send_text_message(self, chat_id, text):
        text = text.strip()

        if not text:
            print("Сообщение не может быть пустым.")
            return

        try:
            result = self.request({
                "@type": "sendMessage",
                "chat_id": chat_id,
                "input_message_content": {
                    "@type": "inputMessageText",
                    "text": {
                        "@type": "formattedText",
                        "text": text,
                        "entities": []
                    }
                }
            })

            if result.get("@type") == "message":
                print(f"Сообщение отправлено! ID: {result['id']}")
            else:
                print("Неожиданный ответ TDLib:")
                print(result)

        except Exception as error:
            print(f"Ошибка отправки сообщения: {error}")
            