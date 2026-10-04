import os

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    send_from_directory,
    session
)

from modules.parser import ChatParser
from modules.analyzer import ChatAnalyzer
from modules.visualizer import ChatVisualizer


app = Flask(__name__)

# Secret key is required for Flask sessions.
# This is only used to remember which chat is currently selected.
app.secret_key = "chatsync-local-secret-key"


UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"

ALLOWED_EXTENSIONS = {"txt"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)


# =========================================================
# CHAT LOADING
# =========================================================

def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in ALLOWED_EXTENSIONS
    )


def load_chat_file(filename):

    file_path = os.path.join(
        UPLOAD_FOLDER,
        filename
    )

    parser = ChatParser(file_path)

    messages = parser.parse_chat()

    if not messages:
        raise ValueError(
            "No WhatsApp messages could be detected."
        )

    analyzer = ChatAnalyzer(messages)

    analyzer.create_dataframe()

    return analyzer


def get_current_analyzer():

    """
    Load the currently selected chat.

    The filename is stored in Flask session so that the
    selected conversation remains available across requests.
    """

    filename = session.get("chat_filename")

    if filename:

        file_path = os.path.join(
            UPLOAD_FOLDER,
            filename
        )

        # Make sure the selected file still exists.
        if not os.path.exists(file_path):

            session.pop("chat_filename", None)

            return None

        try:

            return load_chat_file(filename)

        except Exception:

            return None

    # Fallback:
    # If no session exists, use the most recently uploaded
    # WhatsApp text file.

    uploaded_files = [
        filename
        for filename in os.listdir(UPLOAD_FOLDER)
        if filename.lower().endswith(".txt")
    ]

    if not uploaded_files:
        return None

    uploaded_files.sort(
        key=lambda filename: os.path.getmtime(
            os.path.join(
                UPLOAD_FOLDER,
                filename
            )
        ),
        reverse=True
    )

    filename = uploaded_files[0]

    try:

        analyzer = load_chat_file(filename)

        session["chat_filename"] = filename

        return analyzer

    except Exception:

        return None


def get_current_filename():

    """
    Return the filename of the currently selected chat.
    """

    filename = session.get("chat_filename")

    if filename:
        return filename

    return None


def no_chat_page():

    return render_template(
        "upload.html",
        error_message=(
            "Please upload a WhatsApp chat first."
        )
    )


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():

    return render_template(
        "index.html"
    )


# =========================================================
# UPLOAD
# =========================================================

@app.route(
    "/upload",
    methods=["GET", "POST"]
)
def upload():

    error_message = None

    if request.method == "POST":

        chat_file = request.files.get(
            "chat_file"
        )

        if (
            chat_file is None
            or chat_file.filename == ""
        ):

            error_message = (
                "Please select a WhatsApp chat file."
            )

        elif not allowed_file(
            chat_file.filename
        ):

            error_message = (
                "Only .txt WhatsApp chat files are supported."
            )

        else:

            # Keep the original filename.
            filename = os.path.basename(
                chat_file.filename
            )

            file_path = os.path.join(
                UPLOAD_FOLDER,
                filename
            )

            try:

                # Save uploaded file.
                chat_file.save(
                    file_path
                )

                # Analyze uploaded chat.
                analyzer = load_chat_file(
                    filename
                )

                # Store the selected filename in
                # Flask session.
                session["chat_filename"] = filename

                # Generate dashboard charts.
                visualizer = ChatVisualizer(
                    analyzer,
                    OUTPUT_FOLDER
                )

                visualizer.create_participant_chart()
                visualizer.create_day_chart()
                visualizer.create_hour_chart()
                visualizer.create_top_words_chart()

                overview = (
                    analyzer.get_overview_statistics()
                )

                return render_template(
                    "dashboard.html",
                    overview=overview,
                    filename=filename,
                    top_words=analyzer.get_top_words(10),
                    top_emojis=analyzer.get_top_emojis(10)
                )

            except UnicodeError:

                error_message = (
                    "The chat file encoding could not be read."
                )

            except ValueError as error:

                error_message = str(error)

            except Exception as error:

                error_message = (
                    "The chat could not be analyzed. "
                    f"Error: {error}"
                )

    return render_template(
        "upload.html",
        error_message=error_message
    )


# =========================================================
# DASHBOARD
# =========================================================

@app.route("/dashboard")
def dashboard():

    analyzer = get_current_analyzer()

    if analyzer is None:
        return no_chat_page()

    overview = analyzer.get_overview_statistics()

    return render_template(
        "dashboard.html",
        overview=overview,
        filename=get_current_filename(),
        top_words=analyzer.get_top_words(10),
        top_emojis=analyzer.get_top_emojis(10)
    )


# =========================================================
# PARTICIPANTS
# =========================================================

@app.route("/participants")
def participants():

    analyzer = get_current_analyzer()

    if analyzer is None:
        return no_chat_page()

    statistics = analyzer.get_participant_statistics()

    most_active = (
        statistics.index[0]
        if not statistics.empty
        else "N/A"
    )

    total_messages = (
        int(statistics["messages"].sum())
        if not statistics.empty
        else 0
    )

    return render_template(
        "participants.html",
        statistics=statistics.to_dict("index"),
        participant_names=list(
            statistics.index
        ),
        most_active=most_active,
        total_messages=total_messages,
        filename=get_current_filename()
    )


# =========================================================
# ACTIVITY
# =========================================================

@app.route("/activity")
def activity():

    analyzer = get_current_analyzer()

    if analyzer is None:
        return no_chat_page()

    day_activity = analyzer.get_day_activity()

    hour_activity = analyzer.get_hour_activity()

    busiest_day, busiest_day_count = (
        analyzer.get_busiest_day()
    )

    busiest_hour, busiest_hour_count = (
        analyzer.get_busiest_hour()
    )

    busiest_date, busiest_date_count = (
        analyzer.get_busiest_date()
    )

    return render_template(
        "activity.html",
        day_activity=day_activity.to_dict(),
        hour_activity=hour_activity.to_dict(),
        busiest_day=busiest_day,
        busiest_day_count=int(
            busiest_day_count
        ),
        busiest_hour=busiest_hour,
        busiest_hour_count=int(
            busiest_hour_count
        ),
        busiest_date=busiest_date,
        busiest_date_count=int(
            busiest_date_count
        ),
        filename=get_current_filename()
    )


# =========================================================
# TEXT ANALYSIS
# =========================================================

@app.route("/text-analysis")
def text_analysis():

    analyzer = get_current_analyzer()

    if analyzer is None:
        return no_chat_page()

    text_statistics = (
        analyzer.get_text_statistics()
    )

    return render_template(
        "text_analysis.html",
        text_stats=text_statistics,
        top_words=analyzer.get_top_words(20),
        filename=get_current_filename()
    )


# =========================================================
# SEARCH
# =========================================================

@app.route("/search")
def search():

    analyzer = get_current_analyzer()

    if analyzer is None:
        return no_chat_page()

    query = request.args.get(
        "q",
        ""
    )

    participant = request.args.get(
        "participant",
        ""
    )

    message_type = request.args.get(
        "type",
        ""
    )

    start_date = request.args.get(
        "start_date",
        ""
    )

    end_date = request.args.get(
        "end_date",
        ""
    )

    results = analyzer.search_messages(
        query=query,
        participant=participant,
        message_type=message_type,
        start_date=start_date,
        end_date=end_date
    )

    total_results = len(results)

    display_results = results.head(100)

    records = []

    for _, row in display_results.iterrows():

        records.append({
            "date": row["date"],
            "time": row["time"],
            "sender": row["sender"],
            "message": row["message"],
            "type": row["message_type"]
        })

    return render_template(
        "search.html",
        results=records,
        total_results=total_results,
        query=query,
        selected_participant=participant,
        selected_type=message_type,
        start_date=start_date,
        end_date=end_date,
        participants=analyzer.get_search_participants(),
        message_types=[
            "Text",
            "Media",
            "Link",
            "System",
            "Meta AI"
        ],
        filename=get_current_filename()
    )


# =========================================================
# EMOJI EXPLORER
# =========================================================

@app.route("/emoji-explorer")
def emoji_explorer():

    analyzer = get_current_analyzer()

    if analyzer is None:
        return no_chat_page()

    top_emojis = analyzer.get_top_emojis(
        30
    )

    emoji_by_participant = (
        analyzer.get_emoji_by_participant(
            10
        )
    )

    total_emojis = (
        analyzer.get_total_emoji_count()
    )

    return render_template(
        "emoji_explorer.html",
        top_emojis=top_emojis,
        emoji_by_participant=emoji_by_participant,
        total_emojis=total_emojis,
        filename=get_current_filename()
    )


# =========================================================
# LINK EXPLORER
# =========================================================

@app.route("/link-explorer")
def link_explorer():

    analyzer = get_current_analyzer()

    if analyzer is None:
        return no_chat_page()

    links = analyzer.get_all_links()

    domains = analyzer.get_link_domains(
        20
    )

    statistics = analyzer.get_link_statistics()

    return render_template(
        "link_explorer.html",
        links=links[:500],
        total_links=statistics["total_links"],
        domains=domains,
        filename=get_current_filename()
    )


# =========================================================
# MEDIA EXPLORER
# =========================================================

@app.route("/media-explorer")
def media_explorer():

    analyzer = get_current_analyzer()

    if analyzer is None:
        return no_chat_page()

    media = analyzer.get_all_media()

    statistics = analyzer.get_media_statistics()

    media_by_participant = (
        statistics["media_by_participant"].to_dict()
    )

    max_media_count = (
        max(media_by_participant.values())
        if media_by_participant
        else 0
    )

    media_stats = {
        "total_media": statistics["total_media"],
        "media_percentage": statistics["media_percentage"],
        "media_by_participant": media_by_participant,
        "max_media_count": max_media_count
    }

    return render_template(
        "media_explorer.html",
        media_stats=media_stats,
        media_messages=media[:500],
        filename=get_current_filename()
    )


# =========================================================
# ABOUT
# =========================================================

@app.route("/about")
def about():

    return render_template(
        "about.html"
    )


# =========================================================
# RESET
# =========================================================

@app.route("/reset")
def reset():

    # Forget the currently selected conversation.
    session.pop(
        "chat_filename",
        None
    )

    return redirect(
        url_for("upload")
    )


# =========================================================
# CHART FILES
# =========================================================

@app.route("/charts/<filename>")
def charts(filename):

    return send_from_directory(
        OUTPUT_FOLDER,
        filename
    )


# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )