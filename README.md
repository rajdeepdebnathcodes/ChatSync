
# ChatSync: WhatsApp Conversation Analytics and Visualization System

## Live Website

[https://chatsync-p8t1.onrender.com](https://chatsync-p8t1.onrender.com)

## About the Project

ChatSync is a web-based WhatsApp conversation analytics and visualization system that analyzes exported WhatsApp chat files and provides meaningful insights through an interactive web interface.

The system processes WhatsApp `.txt` chat files and analyzes conversation patterns, participants, message activity, text, emojis, links, and media.

Users can explore the conversation through different analytical sections instead of relying on a single static dashboard.

## Features

- WhatsApp chat file upload and parsing
- Participant-wise message statistics
- Daily and hourly activity analysis
- Text analysis and word frequency
- Message search functionality
- Emoji exploration
- Link and domain analysis
- Media analysis
- Conversation timeline
- Interactive analytics interface

## Technologies Used

Python  
Flask  
Pandas  
NumPy  
Matplotlib  
HTML  
CSS  
Regular Expressions

## How to Run the Project

Install dependencies:

    pip install -r requirements.txt

Run the server:

    python app.py

Open the browser:

[http://127.0.0.1:5000](http://127.0.0.1:5000)

## Input

The system accepts exported WhatsApp conversation files in `.txt` format.

Upload a WhatsApp chat export through the web interface to begin the analysis.

## Project Structure

    ChatSync/
    ├── modules/
    ├── outputs/
    ├── static/
    ├── templates/
    ├── uploads/
    ├── app.py
    └── requirements.txt

## License

MIT License
