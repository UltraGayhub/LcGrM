from config import (
    API_ID,
    API_HASH,
    DATABASE_DIR,
    FILES_DIR,
)


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
    