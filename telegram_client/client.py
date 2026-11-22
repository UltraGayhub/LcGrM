import ctypes
import json
import os
import time
from config import TDLIB_PATH
import queue
import threading

from telegram_client.message import Message
from telegram_client.core import CoreMixin
from telegram_client.authorization import AuthorizationMixin
from telegram_client.chats import ChatsMixin
from telegram_client.messages import MessagesMixin
from telegram_client.downloads import DownloadsMixin
from telegram_client.actualmessages import ActualMessageMixin


class TelegramClient(
    CoreMixin,
    AuthorizationMixin,
    ChatsMixin,
    MessagesMixin,
    DownloadsMixin,
    ActualMessageMixin
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

        self.message_events = queue.Queue()

        self._pending_requests = {}
        self._pending_lock = threading.Lock()

        self._receiver_running = False
        self._receiver_thread = None

        self._closed_event = threading.Event()
            

    
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
            self.start_receiver()
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
                    value = input("\nНомер чата: ").strip()
                    
                    try:
                        index = int(value) - 1

                        if 0 <= index < len(self.chats):
                            chat_id = self.chats[index]["id"]
                            message_text = input("Введите сообщение: ")
                            self.send_text_message(chat_id, message_text)
                        else:
                            print("Неверный номер чата.")

                    except ValueError:
                        print("Нужно ввести номер чата.")     
                elif command == "2":
                    self.select_chat()
                elif command == "3":
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
    
    def process_update(self, update):
        update_type = update.get("@type")

        if update_type == "updateAuthorizationState":
            state = update.get("authorization_state", {})
            if state.get("@type") == "authorizationStateClosed":
                self._closed_event.set()
            self.process_authorization(state)

        elif update_type == "updateNewMessage":
            raw_message = update.get("message", {})
            message = Message.from_tdlib(raw_message)

            self.message_events.put({
                "event": "new_message",
                "data": message
            })

            print("\n========== НОВОЕ СООБЩЕНИЕ ==========")
            print(f"ID: {message.id}")
            print(f"Chat ID: {message.chat_id}")
            print(f"Отправитель: {message.sender_id}")
            print(f"Текст: {message.text}")
            print(f"Исходящее: {message.is_outgoing}")
            print("=====================================")     
        elif update_type == "error":
            print(
                "Ошибка TDLib:",
                update.get("code"),
                update.get("message")
            )
    

            