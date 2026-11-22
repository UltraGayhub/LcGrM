import shutil
from config import VOICE_DIR

class DownloadsMixin:

    def download_voices(self, chat_id, total_limit=500):


        print("\nИщу голосовые сообщения...")

        voice_dir = VOICE_DIR

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
        downloaded_files = []

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

                downloaded_files.append({
                    "message_id": voice["message_id"],
                    "name": destination.name,
                    "path": str(destination.resolve())
                })


            except Exception as error:
                print(f"Ошибка скачивания: {error}")

        print(
            f"\nГотово! Скачано голосовых: "
            f"{len(downloaded_files)}/{len(voice_messages)}"
        )

        return downloaded_files
