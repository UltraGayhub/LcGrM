from dataclasses import dataclass
from typing import Optional


@dataclass
class Message:
    id: int
    chat_id: int
    sender_id: Optional[int]
    sender_type: str
    date: int
    text: str
    type: str
    is_outgoing: bool

    @classmethod
    def from_tdlib(cls, data: dict):
        from telegram_client.message_parser import parse_message

        parsed = parse_message(data)

        return cls(
            id=parsed["id"],
            chat_id=parsed["chat_id"],
            sender_id=parsed["sender"]["id"],
            sender_type=parsed["sender"]["type"],
            date=parsed["date"],
            text=parsed["text"],
            type=parsed["type"],
            is_outgoing=parsed["is_outgoing"]
        )