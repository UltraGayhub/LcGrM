class MessagesMixin:

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