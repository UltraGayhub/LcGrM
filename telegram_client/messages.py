from telegram_client.message import Message

class MessagesMixin:    
    def get_history(self, chat_id, limit=50, from_message_id=0):
        batch = []
        seen_ids = set()
        cursor = from_message_id

        while len(batch) < limit:
            remaining = limit - len(batch)

            result = self.request({
                "@type": "getChatHistory",
                "chat_id": chat_id,
                "from_message_id": cursor,
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

            cursor = batch[-1]["id"]

        parsed_messages = [
            Message.from_tdlib(message)
            for message in reversed(batch)
        ]

        for message in parsed_messages:
            self.debug_message(message)

        return {
            "messages": parsed_messages,
            "next_from_message_id": cursor,
            "has_more": len(batch) == limit
        }


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

    def debug_message(self, message):
        print("\n========== ПОЛУЧЕНО СООБЩЕНИЕ ==========")
        print(f"ID:          {message.id}")
        print(f"Chat ID:     {message.chat_id}")
        print(f"Отправитель: {message.sender_id}")
        print(f"Дата:        {message.date}")
        print(f"Тип:         {message.type}")
        print(f"Текст:       {message.text}")
        print(f"Исходящее:   {message.is_outgoing}")
        print("=" * 42)
