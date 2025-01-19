import genanki
import csv
import os
import hashlib

# Define the deck and model
DECK_NAME = "Japanese Practice N5"
MODEL_ID = 1234567890  # Unique ID for the model
DECK_ID = 9876543210   # Unique ID for the deck

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
        # Card 1: English text and audio on front, Japanese and Roman with audio on the back
        {
            "name": "English to Japanese",
            "qfmt": "<div class='card front'>{{EnglishText}}<br>{{EnglishAudio}}</div>",
            "afmt": "<div class='card back'>{{FrontSide}}<hr id=answer>{{JapaneseText}}<br>{{RomanText}}<br>{{JapaneseAudio}}</div>"
        },
        # Card 2: Japanese audio on front, English, Roman, and Japanese text on the back with English audio
        {
            "name": "Japanese Audio to English",
            "qfmt": "<div class='card front'>{{JapaneseAudio}}</div>",
            "afmt": "<div class='card back'>{{FrontSide}}<hr id=answer>{{JapaneseText}}<br>{{RomanText}}<br>{{EnglishText}}<br>{{EnglishAudio}}</div>"
        }
    ]
)

# Create a new Anki deck
anki_deck = genanki.Deck(
    DECK_ID,
    DECK_NAME
)

# Define paths
TSV_FILE = "input.tsv"  # Replace with your TSV file name
AUDIO_FOLDER = "output_audio"

def generate_guid(field):
    return int(hashlib.md5(field.encode('utf-8')).hexdigest()[:8], 16)

# Read the .tsv file and add notes to the deck
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

        # Create a note for the row
        note = genanki.Note(
            model=anki_model,
            fields=[english_text, english_audio_path, japanese_text, roman_text, japanese_audio_path]
            guid=generate_guid(card_id)  # Pass fields to generate the GUID
        )
        
        # Add the note to the deck
        anki_deck.add_note(note)

# Save the deck to a .apkg file
output_file = "japanese_practice_deck_n5.apkg"
genanki.Package(anki_deck, media_files=[os.path.join(AUDIO_FOLDER, f) for f in os.listdir(AUDIO_FOLDER)]).write_to_file(output_file)
print(f"Anki deck has been created and saved to {output_file}")
