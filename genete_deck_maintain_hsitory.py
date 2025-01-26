import genanki
import csv
import os
import sqlite3

# Define the old deck path
OLD_DECK_PATH = "old_deck.apkg"
NEW_DECK_NAME = "Japanese Practice N5 - Updated"
NEW_DECK_ID = 9876543220  # Unique ID for the new deck
MODEL_ID = 1234567890

# Anki model definition
anki_model = genanki.Model(
    MODEL_ID,
    "Japanese Learning Model",
    css="""
    .card {
      font-family: Arial, Helvetica, sans-serif;
      font-size: 20px;
      text-align: center;
      color: #eaeaea;
      background-color: #1e1e1e;
      margin: 10px;
      padding: 20px;
      border: 2px solid #333;
      border-radius: 10px;
      box-shadow: 2px 2px 10px rgba(0, 0, 0, 0.8);
    }

    .front {
      color: #4caf4f;
    }

    .back {
      color: #f28b82;
    }

    hr {
      border: none;
      border-top: 2px dashed #555;
      margin: 20px 0;
    }
    """,
    fields=[
        {"name": "EnglishText"},
        {"name": "EnglishAudio"},
        {"name": "JapaneseText"},
        {"name": "RomanText"},
        {"name": "JapaneseAudio"}
    ],
    templates=[
        {
            "name": "English to Japanese",
            "qfmt": "<div class='card front'>{{EnglishText}}<br>{{EnglishAudio}}</div>",
            "afmt": "<div class='card back'>{{FrontSide}}<hr id=answer>{{JapaneseText}}<br>{{RomanText}}<br>{{JapaneseAudio}}</div>"
        },
        {
            "name": "Japanese Audio to English",
            "qfmt": "<div class='card front'>{{JapaneseAudio}}</div>",
            "afmt": "<div class='card back'>{{FrontSide}}<hr id=answer>{{JapaneseText}}<br>{{RomanText}}<br>{{EnglishText}}<br>{{EnglishAudio}}</div>"
        }
    ]
)

# Open the old .apkg file as a SQLite database
def open_old_deck(path):
    conn = sqlite3.connect(path)
    return conn

# Extract notes and review history from the old deck
def get_old_notes_with_history(conn):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT n.flds, c.reps, c.lapses, c.ivl, c.due
        FROM notes n
        JOIN cards c ON n.id = c.nid
    """)
    old_notes = {}
    for row in cursor.fetchall():
        fields = row[0].split("\x1f")  # Fields are separated by 0x1F
        english_text = fields[0]  # Assuming the first field is English text
        old_notes[english_text] = {
            "reps": row[1],
            "lapses": row[2],
            "interval": row[3],
            "due": row[4]
        }
    return old_notes

# Create the new Anki deck
anki_deck = genanki.Deck(
    NEW_DECK_ID,
    NEW_DECK_NAME
)

# Define paths
TSV_FILE = "input.tsv"  # Replace with your TSV file name
AUDIO_FOLDER = "output_audio"

# Open the old deck and get history
old_deck_conn = open_old_deck(OLD_DECK_PATH)
old_notes = get_old_notes_with_history(old_deck_conn)

# Read the .tsv file and add notes to the new deck
with open(TSV_FILE, "r", encoding="utf-8") as tsv_file:
    reader = csv.DictReader(tsv_file, delimiter="\t")
    for row in reader:
        # Extract data from each row
        english_text = row["English"]
        japanese_text = row["Japanese"]
        roman_text = row["Roman"]
        card_id = row["Id"]

        # Generate audio file paths
        japanese_audio_path = f"[sound:{card_id}_jp.mp3]"
        english_audio_path = f"[sound:{card_id}_eng.mp3]"

        # Check if the note exists in the old deck
        review_data = old_notes.get(english_text, {
            "reps": 0,
            "lapses": 0,
            "interval": 0,
            "due": 0
        })

        # Create a note
        note = genanki.Note(
            model=anki_model,
            fields=[english_text, english_audio_path, japanese_text, roman_text, japanese_audio_path]
        )
        anki_deck.add_note(note)

# Save the deck to a .apkg file
output_file = "japanese_practice_deck_updated.apkg"
genanki.Package(anki_deck, media_files=[os.path.join(AUDIO_FOLDER, f) for f in os.listdir(AUDIO_FOLDER)]).write_to_file(output_file)
print(f"Updated Anki deck has been created and saved to {output_file}")
