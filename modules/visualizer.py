import os

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties


class ChatVisualizer:

    def __init__(self, analyzer, output_folder="outputs"):
        self.analyzer = analyzer
        self.output_folder = output_folder

        os.makedirs(self.output_folder, exist_ok=True)

    def create_participant_chart(self):

        statistics = self.analyzer.get_participant_statistics()

        plt.figure(figsize=(10, 5))

        statistics["messages"].plot(
            kind="bar"
        )

        plt.title("Messages by Participant")
        plt.xlabel("Participant")
        plt.ylabel("Number of Messages")

        plt.xticks(rotation=30, ha="right")
        plt.tight_layout()

        file_path = os.path.join(
            self.output_folder,
            "participant_messages.png"
        )

        plt.savefig(file_path)
        plt.close()

        return file_path

    def create_day_chart(self):

        activity = self.analyzer.get_day_activity()

        plt.figure(figsize=(10, 5))

        activity.plot(
            kind="bar"
        )

        plt.title("Messages by Day of Week")
        plt.xlabel("Day")
        plt.ylabel("Number of Messages")

        plt.xticks(rotation=30)
        plt.tight_layout()

        file_path = os.path.join(
            self.output_folder,
            "messages_by_day.png"
        )

        plt.savefig(file_path)
        plt.close()

        return file_path

    def create_hour_chart(self):

        activity = self.analyzer.get_hour_activity()

        plt.figure(figsize=(10, 5))

        activity.plot(
            kind="line",
            marker="o"
        )

        plt.title("Messages by Hour")
        plt.xlabel("Hour of Day")
        plt.ylabel("Number of Messages")

        plt.xticks(range(24))
        plt.grid(True, alpha=0.3)

        plt.tight_layout()

        file_path = os.path.join(
            self.output_folder,
            "messages_by_hour.png"
        )

        plt.savefig(file_path)
        plt.close()

        return file_path

    def create_top_words_chart(self, limit=10):

        top_words = self.analyzer.get_top_words(limit)

        words = [
            item[0]
            for item in top_words
        ]

        counts = [
            item[1]
            for item in top_words
        ]

        plt.figure(figsize=(10, 5))

        plt.bar(
            words,
            counts
        )

        plt.title("Most Frequently Used Words")
        plt.xlabel("Word")
        plt.ylabel("Frequency")

        plt.xticks(
            rotation=45,
            ha="right"
        )

        plt.tight_layout()

        file_path = os.path.join(
            self.output_folder,
            "top_words.png"
        )

        plt.savefig(file_path)
        plt.close()

        return file_path

    def get_emoji_font(self):

        font_paths = [
            r"C:\Windows\Fonts\seguiemj.ttf",
            r"C:\Windows\Fonts\seguisym.ttf"
        ]

        for font_path in font_paths:

            if os.path.exists(font_path):
                return FontProperties(
                    fname=font_path
                )

        return None

    def create_emoji_chart(self, limit=10):

        top_emojis = self.analyzer.get_top_emojis(limit)

        emojis = [
            item[0]
            for item in top_emojis
        ]

        counts = [
            item[1]
            for item in top_emojis
        ]

        plt.figure(figsize=(10, 5))

        plt.bar(
            range(len(emojis)),
            counts
        )

        plt.title("Most Used Emojis")
        plt.xlabel("Emoji")
        plt.ylabel("Frequency")

        emoji_font = self.get_emoji_font()

        if emoji_font is not None:

            plt.xticks(
                range(len(emojis)),
                emojis,
                fontproperties=emoji_font,
                fontsize=18
            )

        else:

            plt.xticks(
                range(len(emojis)),
                emojis,
                fontsize=16
            )

        plt.tight_layout()

        file_path = os.path.join(
            self.output_folder,
            "top_emojis.png"
        )

        plt.savefig(
            file_path,
            dpi=150
        )

        plt.close()

        return file_path