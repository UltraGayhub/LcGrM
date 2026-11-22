from dotenv import load_dotenv

load_dotenv()

from telegram_client import TelegramClient


def main():
    print("================================")
    print("      TELEGRAM APPLICATION")
    print("================================")

    client = TelegramClient()
    client.run()


if __name__ == "__main__":
    main()
