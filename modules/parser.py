import re


class ChatParser:

    def __init__(self, file_path):
        self.file_path = file_path
        self.messages = []

    def parse_chat(self):

        try:
            with open(self.file_path, "r", encoding="utf-8") as file:
                lines = file.readlines()

        except UnicodeDecodeError:
            with open(self.file_path, "r", encoding="utf-16") as file:
                lines = file.readlines()

        except FileNotFoundError:
            raise FileNotFoundError("Chat file was not found.")

        # Common WhatsApp date/time format:
        # 12/03/2026, 8:42 pm - Name: Message

        message_pattern = re.compile(
            r"^(\d{1,2}/\d{1,2}/\d{2,4}),?\s+"
            r"(\d{1,2}:\d{2}(?::\d{2})?\s*[AaPp][Mm]?)\s*-\s*"
            r"([^:]+):\s*(.*)$"
        )

        current_message = None

        for line in lines:

            line = line.rstrip("\n")

            match = message_pattern.match(line)

            if match:

                if current_message is not None:
                    self.messages.append(current_message)

                date = match.group(1)
                time = match.group(2)
                sender = match.group(3).strip()
                message = match.group(4).strip()

                current_message = {
                    "date": date,
                    "time": time,
                    "sender": sender,
                    "message": message
                }

            else:

                if current_message is not None and line.strip():
                    current_message["message"] += " " + line.strip()

        if current_message is not None:
            self.messages.append(current_message)

        return self.messages

    def get_message_count(self):
        return len(self.messages)