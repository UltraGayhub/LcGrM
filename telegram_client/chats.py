class ChatsMixin:

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
                f"{index}. {chat['title']}"
#               f"| {chat['type']}"
#               f"| ID: {chat['id']}"
            )
        return chats


    def select_chat(self):
            if not getattr(self, "chats", None):
                print("Сначала загрузи список чатов.")
                return
            
            value = input(
                "\nВведи номер чата или q для выхода: "
            ).strip().lower()

            if value == "q":
                return

            try:
                index = int(value) - 1

                if index < 0 or index >= len(self.chats):
                    print("Неверный номер.")

                chat = self.chats[index]
                return(chat["id"])
                print(f"\nОткрываем: {chat['title']}")
                self.get_history(chat["id"])

            except ValueError:
                print("Введи номер чата.")
