import ctypes
import json
import os
import time
from config import TDLIB_PATH

from telegram_client.authorization import AuthorizationMixin
from telegram_client.chats import ChatsMixin
from telegram_client.messages import MessagesMixin
from telegram_client.downloads import DownloadsMixin


class TelegramClient(
    AuthorizationMixin,
    ChatsMixin,
    MessagesMixin,
    DownloadsMixin
):
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
    

            