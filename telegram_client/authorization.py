import getpass

from config import (
    API_ID,
    API_HASH,
    DATABASE_DIR,
    FILES_DIR,
)


# Метка для запросов авторизации: по ней ответ TDLib с ошибкой
# отличается от остальных ошибок, и шаг можно повторить.
AUTH_EXTRA = "auth"

# Состояния, в которых нужен ввод пользователя
INPUT_STATES = {
    "authorizationStateWaitPhoneNumber",
    "authorizationStateWaitCode",
    "authorizationStateWaitPassword",
    "authorizationStateWaitEmailAddress",
    "authorizationStateWaitEmailCode",
    "authorizationStateWaitRegistration",
}


class AuthorizationMixin:

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

    def send_auth(self, data):
        data["@extra"] = AUTH_EXTRA
        self.send(data)

    def handle_auth_error(self, error):
        """Ошибка на шаге авторизации: показываем причину и повторяем шаг."""
        message = error.get("message", "")
        print(f"\nОшибка авторизации: {message}")

        if message.startswith("FLOOD_WAIT") or "Too Many Requests" in message:
            print("Слишком много попыток. Подождите и попробуйте позже.")

        state = getattr(self, "auth_state", None)

        if state and state.get("@type") in INPUT_STATES:
            print("Попробуйте ещё раз.")
            self.process_authorization(state)

    def process_authorization(self, state):
        state_type = state.get("@type")
        self.auth_state = state

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
            phone = ""
            while not phone:
                phone = input(
                    "\nВведите номер телефона (+79990000000): "
                ).strip()

            print("\nОтправляем номер в Telegram...")

            self.send_auth({
                "@type": "setAuthenticationPhoneNumber",
                "phone_number": phone
            })

            print("Запрос отправлен. Ожидаем ответ TDLib...")

        elif state_type == "authorizationStateWaitCode":
            code = ""
            while not code:
                code = input(
                    "\nВведите код из Telegram: "
                ).strip()

            self.send_auth({
                "@type": "checkAuthenticationCode",
                "code": code
            })

        elif state_type == "authorizationStateWaitPassword":
            hint = state.get("password_hint")
            if hint:
                print(f"Подсказка к паролю: {hint}")

            password = getpass.getpass(
                "\nВведите пароль двухфакторной защиты: "
            )

            self.send_auth({
                "@type": "checkAuthenticationPassword",
                "password": password
            })

        elif state_type == "authorizationStateReady":
            print("\n================================")
            print("УСПЕШНАЯ АВТОРИЗАЦИЯ TELEGRAM!")
            print("================================")

            self.authorized = True

        elif state_type == "authorizationStateWaitRegistration":
            print("Этот номер ещё не зарегистрирован в Telegram.")
            first_name = ""
            while not first_name:
                first_name = input("Имя: ").strip()
            last_name = input("Фамилия (можно пусто): ").strip()

            self.send_auth({
                "@type": "registerUser",
                "first_name": first_name,
                "last_name": last_name
            })

        elif state_type == "authorizationStateWaitOtherDeviceConfirmation":
            print("Подтвердите вход на другом устройстве.")
            link = state.get("link")
            if link:
                print(f"Ссылка для подтверждения: {link}")

        elif state_type == "authorizationStateWaitEmailAddress":
            email = ""
            while not email:
                email = input("\nВведите адрес электронной почты: ").strip()

            self.send_auth({
                "@type": "setAuthenticationEmailAddress",
                "email_address": email
            })

        elif state_type == "authorizationStateWaitEmailCode":
            code = ""
            while not code:
                code = input("\nВведите код из электронной почты: ").strip()

            self.send_auth({
                "@type": "checkAuthenticationEmailCode",
                "code": {
                    "@type": "emailAddressAuthenticationCode",
                    "code": code
                }
            })

        elif state_type == "authorizationStateLoggingOut":
            print("Выполняется выход из аккаунта...")

        elif state_type == "authorizationStateClosed":
            print("TDLib закрыта.")
