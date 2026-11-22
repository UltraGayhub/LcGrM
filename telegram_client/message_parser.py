def parse_message(message):
    content = message.get("content", {})
    content_type = content.get("@type", "")

    sender_data = message.get("sender_id", {})
    sender_type = sender_data.get("@type", "")

    if sender_type == "messageSenderUser":
        sender_id = sender_data.get("user_id")
        sender_kind = "user"
    elif sender_type == "messageSenderChat":
        sender_id = sender_data.get("chat_id")
        sender_kind = "chat"
    else:
        sender_id = None
        sender_kind = "unknown"

    message_type = content_type.replace("message", "").lower()

    text = ""
    if content_type == "messageText":
        text = content.get("text", {}).get("text", "")

    elif content_type == "messageVoiceNote":
        text = content.get("caption", {}).get("text", "")

    elif content_type in ("messagePhoto", "messageVideo", "messageDocument"):
        text = content.get("caption", {}).get("text", "")

    return {
        "id": message.get("id"),
        "chat_id": message.get("chat_id"),
        "sender": {
            "id": sender_id,
            "type": sender_kind
        },
        "date": message.get("date"),
        "text": text,
        "type": message_type,
        "is_outgoing": message.get("is_outgoing", False)
    }
