import re
from collections import Counter
from urllib.parse import urlparse

import pandas as pd


class ChatAnalyzer:

    def __init__(self, messages):
        self.messages = messages
        self.dataframe = None

    def create_dataframe(self):

        self.dataframe = pd.DataFrame(self.messages)

        self.dataframe["date"] = pd.to_datetime(
            self.dataframe["date"],
            format="%d/%m/%y",
            errors="coerce"
        )

        self.dataframe["datetime"] = pd.to_datetime(
            self.dataframe["date"].dt.strftime("%d/%m/%Y")
            + " "
            + self.dataframe["time"],
            format="%d/%m/%Y %I:%M %p",
            errors="coerce"
        )

        self.dataframe["message_type"] = self.dataframe.apply(
            self.classify_message,
            axis=1
        )

        return self.dataframe

    def classify_message(self, row):

        sender = str(row["sender"]).strip()
        message = str(row["message"]).strip()

        if sender.lower() == "meta ai":
            return "Meta AI"

        if "<media omitted>" in message.lower():
            return "Media"

        if re.search(
            r"https?://\S+|www\.\S+",
            message,
            re.IGNORECASE
        ):
            return "Link"

        system_phrases = [
            "changed the group",
            "changed this group's",
            "changed the group icon",
            "joined using",
            "security code changed",
            "was added",
            "was removed",
            "left the group",
            "joined the group"
        ]

        message_lower = message.lower()

        for phrase in system_phrases:
            if phrase in message_lower:
                return "System"

        return "Text"

    def get_message_count(self):

        if self.dataframe is None:
            self.create_dataframe()

        return len(self.dataframe)

    def get_human_message_count(self):

        if self.dataframe is None:
            self.create_dataframe()

        human_messages = self.dataframe[
            self.dataframe["sender"].str.lower() != "meta ai"
        ]

        return len(human_messages)

    def get_participant_count(self):

        if self.dataframe is None:
            self.create_dataframe()

        human_messages = self.dataframe[
            self.dataframe["sender"].str.lower() != "meta ai"
        ]

        return human_messages["sender"].nunique()

    def get_ai_message_count(self):

        if self.dataframe is None:
            self.create_dataframe()

        ai_messages = self.dataframe[
            self.dataframe["sender"].str.lower() == "meta ai"
        ]

        return len(ai_messages)

    def get_total_words(self):

        if self.dataframe is None:
            self.create_dataframe()

        text_messages = self.dataframe[
            self.dataframe["message_type"] == "Text"
        ]

        return int(
            text_messages["message"].str.split().str.len().sum()
        )

    def get_participant_statistics(self):

        if self.dataframe is None:
            self.create_dataframe()

        human_messages = self.dataframe[
            (self.dataframe["sender"].str.lower() != "meta ai")
            & (
                self.dataframe["message_type"].isin(
                    ["Text", "Media", "Link"]
                )
            )
        ].copy()

        statistics = human_messages.groupby("sender").agg(
            messages=("message", "count")
        )

        text_messages = human_messages[
            human_messages["message_type"] == "Text"
        ].copy()

        text_messages["word_count"] = (
            text_messages["message"].str.split().str.len()
        )

        words = text_messages.groupby("sender")["word_count"].sum()

        statistics["words"] = words

        statistics["message_percentage"] = (
            statistics["messages"]
            / statistics["messages"].sum()
            * 100
        )

        return statistics.sort_values(
            by="messages",
            ascending=False
        )

    def get_day_activity(self):

        if self.dataframe is None:
            self.create_dataframe()

        human_messages = self.dataframe[
            self.dataframe["message_type"].isin(
                ["Text", "Media", "Link"]
            )
            & (
                self.dataframe["sender"].str.lower() != "meta ai"
            )
        ].copy()

        human_messages["day"] = (
            human_messages["datetime"].dt.day_name()
        )

        day_order = [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday"
        ]

        activity = human_messages["day"].value_counts()

        return activity.reindex(
            day_order,
            fill_value=0
        )

    def get_hour_activity(self):

        if self.dataframe is None:
            self.create_dataframe()

        human_messages = self.dataframe[
            self.dataframe["message_type"].isin(
                ["Text", "Media", "Link"]
            )
            & (
                self.dataframe["sender"].str.lower() != "meta ai"
            )
        ].copy()

        human_messages["hour"] = (
            human_messages["datetime"].dt.hour
        )

        activity = human_messages["hour"].value_counts()

        return activity.reindex(
            range(24),
            fill_value=0
        )

    def get_busiest_day(self):

        activity = self.get_day_activity()

        return activity.idxmax(), activity.max()

    def get_busiest_hour(self):

        activity = self.get_hour_activity()

        return activity.idxmax(), activity.max()

    def get_busiest_date(self):

        if self.dataframe is None:
            self.create_dataframe()

        human_messages = self.dataframe[
            self.dataframe["message_type"].isin(
                ["Text", "Media", "Link"]
            )
            & (
                self.dataframe["sender"].str.lower() != "meta ai"
            )
        ].copy()

        activity = human_messages["date"].value_counts()

        return activity.idxmax(), activity.max()

    def get_busiest_date_hour(self):

        if self.dataframe is None:
            self.create_dataframe()

        human_messages = self.dataframe[
            self.dataframe["message_type"].isin(
                ["Text", "Media", "Link"]
            )
            & (
                self.dataframe["sender"].str.lower() != "meta ai"
            )
        ].copy()

        human_messages["hour"] = (
            human_messages["datetime"].dt.hour
        )

        activity = human_messages.groupby(
            ["date", "hour"]
        ).size()

        return activity.idxmax(), activity.max()

    def get_overview_statistics(self):

        if self.dataframe is None:
            self.create_dataframe()

        human_messages = self.dataframe[
            self.dataframe["sender"].str.lower() != "meta ai"
        ]

        text_messages = human_messages[
            human_messages["message_type"] == "Text"
        ].copy()

        text_messages["message_length"] = (
            text_messages["message"].str.len()
        )

        return {
            "human_messages": len(human_messages),
            "participants": self.get_participant_count(),
            "total_words": self.get_total_words(),
            "start_date": self.dataframe["date"].min(),
            "end_date": self.dataframe["date"].max(),
            "average_message_length": (
                text_messages["message_length"].mean()
            ),
            "longest_message": (
                text_messages["message_length"].max()
            ),
            "shortest_message": (
                text_messages["message_length"].min()
            ),
            "media_count": len(
                self.dataframe[
                    self.dataframe["message_type"] == "Media"
                ]
            ),
            "link_count": len(
                self.dataframe[
                    self.dataframe["message_type"] == "Link"
                ]
            ),
            "system_count": len(
                self.dataframe[
                    self.dataframe["message_type"] == "System"
                ]
            ),
            "ai_messages": self.get_ai_message_count()
        }

    def get_text_statistics(self):

        if self.dataframe is None:
            self.create_dataframe()

        text_messages = self.dataframe[
            self.dataframe["message_type"] == "Text"
        ].copy()

        if text_messages.empty:
            return {
                "total_words": 0,
                "average_words_per_message": 0,
                "longest_message": "No text messages found.",
                "longest_message_sender": "",
                "longest_message_date": None,
                "longest_message_length": 0
            }

        text_messages["word_count"] = (
            text_messages["message"]
            .str.split()
            .str.len()
        )

        longest_message = text_messages.loc[
            text_messages["message"].str.len().idxmax()
        ]

        return {
            "total_words": int(
                text_messages["word_count"].sum()
            ),
            "average_words_per_message": (
                text_messages["word_count"].mean()
            ),
            "longest_message": longest_message["message"],
            "longest_message_sender": longest_message["sender"],
            "longest_message_date": longest_message["date"],
            "longest_message_length": len(
                longest_message["message"]
            )
        }

    def get_top_words(self, limit=20):

        if self.dataframe is None:
            self.create_dataframe()

        text_messages = self.dataframe[
            self.dataframe["message_type"] == "Text"
        ]

        all_text = " ".join(
            text_messages["message"].astype(str)
        )

        words = re.findall(
            r"\b[a-zA-Z][a-zA-Z']*\b",
            all_text.lower()
        )

        stop_words = {
            "the", "a", "an", "and", "or", "is", "it",
            "to", "of", "in", "on", "for", "with", "this",
            "that", "was", "are", "be", "i", "you", "we",
            "he", "she", "they", "me", "my", "your", "our",
            "so", "but", "if", "at", "as", "from", "have",
            "has", "had", "do", "does", "did", "not",
            "will", "would", "could", "should", "can",
            "just", "very", "than", "then", "there",
            "here", "what", "when", "where", "who",
            "how", "why", "which",

            "hai", "hain", "tha", "thi", "the",
            "ho", "hu", "hun", "h",
            "raha", "rahe", "rahi", "rha", "rhe", "rhi",
            "kya", "kyu", "kyun", "kyunki",
            "mai", "main", "mein", "me",
            "mujhe", "mujh", "mera", "meri", "mere",
            "tum", "tumhe", "tumhara", "tumhari", "tumhare",
            "aap", "ap", "aapko",
            "hum", "ham", "hamara", "hamari", "hamare",
            "ye", "yeh", "woh", "wo",
            "iska", "iske", "iski",
            "uska", "uske", "uski",
            "ka", "ke", "ki", "ko",
            "se", "ne", "par", "pe",
            "nahi", "nahin", "na",
            "haan", "han", "ha",
            "bhi", "hi",
            "toh", "to", "aur", "ya",
            "ek", "koi", "kuch", "sab",
            "ab", "abhi", "tab", "phir", "fir",
            "jab", "jo", "jis", "jise",
            "jaisa", "waisa", "waise",
            "wala", "wali", "wale",
            "maine", "mene", "tune", "tu",
            "tera", "teri", "tere",
            "bas", "ok", "okay",
            "hoga", "hogi", "hoge", "hona", "hone",
            "acha", "accha", "achha",
            "are", "arre", "oye",
            "bhai", "yaar", "yar", "bro",
            "aisa", "aise", "aisi",
            "mat", "matlab", "shayad",
            "already", "actually", "literally",

            "kar", "karo", "karna", "karne",
            "karte", "karta", "karti",
            "kiya", "kia",
            "diya", "dena", "de", "dete",
            "le", "lena", "lete",
            "aa", "aana", "aaya", "aayi", "aaye",
            "ja", "jaa", "jana", "jane",
            "gaya", "gayi", "gaye", "gya",
            "bol", "bola", "boli", "bolo",
            "bata", "batao", "bta",
            "pata", "lag", "laga", "lage"
        }

        filtered_words = [
            word
            for word in words
            if word not in stop_words
        ]

        return Counter(filtered_words).most_common(limit)

    def _extract_emojis(self, text):

        emoji_pattern = re.compile(
            r"[\U0001F300-\U0001FAFF\u2600-\u27BF]"
            r"(?:\uFE0F|\U0001F3FB-\U0001F3FF)?"
            r"(?:\u200D"
            r"[\U0001F300-\U0001FAFF\u2600-\u27BF]"
            r"(?:\uFE0F|\U0001F3FB-\U0001F3FF)?"
            r")*"
        )

        return emoji_pattern.findall(str(text))

    def get_top_emojis(self, limit=20):

        if self.dataframe is None:
            self.create_dataframe()

        text_messages = self.dataframe[
            self.dataframe["message_type"] == "Text"
        ]

        emoji_counts = Counter()

        for message in text_messages["message"].astype(str):

            emojis = self._extract_emojis(message)

            emoji_counts.update(emojis)

        return emoji_counts.most_common(limit)

    def get_total_emoji_count(self):

        return sum(
            count
            for emoji, count in self.get_top_emojis(limit=None)
        )

    def get_emoji_by_participant(self, limit=10):

        if self.dataframe is None:
            self.create_dataframe()

        text_messages = self.dataframe[
            (self.dataframe["message_type"] == "Text")
            & (
                self.dataframe["sender"].str.lower() != "meta ai"
            )
        ]

        participant_emojis = {}

        for participant in text_messages["sender"].unique():

            participant_messages = text_messages[
                text_messages["sender"] == participant
            ]

            emoji_counts = Counter()

            for message in participant_messages["message"].astype(str):

                emoji_counts.update(
                    self._extract_emojis(message)
                )

            participant_emojis[participant] = (
                emoji_counts.most_common(limit)
            )

        return participant_emojis

    def get_link_statistics(self):

        if self.dataframe is None:
            self.create_dataframe()

        link_messages = self.dataframe[
            self.dataframe["message_type"] == "Link"
        ].copy()

        human_links = link_messages[
            link_messages["sender"].str.lower() != "meta ai"
        ]

        links_by_participant = (
            human_links["sender"]
            .value_counts()
        )

        return {
            "total_links": len(human_links),
            "links_by_participant": links_by_participant
        }

    def get_link_domains(self, limit=20):

        if self.dataframe is None:
            self.create_dataframe()

        link_messages = self.dataframe[
            self.dataframe["message_type"] == "Link"
        ]

        domain_counts = Counter()

        url_pattern = re.compile(
            r"(?:https?://|www\.)([^/\s]+)",
            re.IGNORECASE
        )

        for message in link_messages["message"].astype(str):

            matches = url_pattern.findall(message)

            for domain in matches:

                domain = domain.lower().rstrip(".,!?;:")

                if domain.startswith("www."):
                    domain = domain[4:]

                domain_counts[domain] += 1

        return domain_counts.most_common(limit)

    def get_all_links(self):

        if self.dataframe is None:
            self.create_dataframe()

        link_messages = self.dataframe[
            self.dataframe["message_type"] == "Link"
        ].copy()

        results = []

        url_pattern = re.compile(
            r"https?://\S+|www\.\S+",
            re.IGNORECASE
        )

        for _, row in link_messages.iterrows():

            matches = url_pattern.findall(
                str(row["message"])
            )

            for url in matches:

                clean_url = url.rstrip(
                    ".,!?;:)]}"
                )

                parsed = urlparse(
                    clean_url
                    if clean_url.startswith(("http://", "https://"))
                    else "https://" + clean_url
                )

                domain = parsed.netloc.lower()

                if domain.startswith("www."):
                    domain = domain[4:]

                results.append({
                    "date": row["date"],
                    "time": row["time"],
                    "sender": row["sender"],
                    "url": clean_url,
                    "domain": domain
                })

        return results

    def get_media_statistics(self):

        if self.dataframe is None:
            self.create_dataframe()

        media_messages = self.dataframe[
            self.dataframe["message_type"] == "Media"
        ]

        human_media = media_messages[
            media_messages["sender"].str.lower() != "meta ai"
        ]

        media_by_participant = (
            human_media["sender"]
            .value_counts()
        )

        human_messages = self.dataframe[
            self.dataframe["sender"].str.lower() != "meta ai"
        ]

        media_percentage = (
            len(human_media)
            / len(human_messages)
            * 100
        ) if len(human_messages) else 0

        return {
            "total_media": len(human_media),
            "media_percentage": media_percentage,
            "media_by_participant": media_by_participant
        }

    def get_all_media(self):

        if self.dataframe is None:
            self.create_dataframe()

        media_messages = self.dataframe[
            self.dataframe["message_type"] == "Media"
        ]

        results = []

        for _, row in media_messages.iterrows():

            results.append({
                "date": row["date"],
                "time": row["time"],
                "sender": row["sender"],
                "message": row["message"]
            })

        return results

    def search_messages(
        self,
        query="",
        participant="",
        message_type="",
        start_date="",
        end_date=""
    ):

        if self.dataframe is None:
            self.create_dataframe()

        results = self.dataframe.copy()

        query = str(query).strip()

        if query:
            results = results[
                results["message"]
                .astype(str)
                .str.contains(
                    query,
                    case=False,
                    na=False,
                    regex=False
                )
            ]

        if participant:
            results = results[
                results["sender"] == participant
            ]

        if message_type:
            results = results[
                results["message_type"] == message_type
            ]

        if start_date:
            start = pd.to_datetime(
                start_date,
                errors="coerce"
            )

            if not pd.isna(start):
                results = results[
                    results["date"] >= start
                ]

        if end_date:
            end = pd.to_datetime(
                end_date,
                errors="coerce"
            )

            if not pd.isna(end):
                results = results[
                    results["date"] <= end
                ]

        results = results.sort_values(
            by="datetime",
            ascending=False
        )

        return results

    def get_search_participants(self):

        if self.dataframe is None:
            self.create_dataframe()

        return sorted(
            self.dataframe["sender"]
            .dropna()
            .unique()
            .tolist()
        )

    def get_message_type_counts(self):

        if self.dataframe is None:
            self.create_dataframe()

        return (
            self.dataframe["message_type"]
            .value_counts()
            .to_dict()
        )