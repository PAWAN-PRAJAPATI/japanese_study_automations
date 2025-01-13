import hashlib
import pandas as pd
from google.cloud import texttospeech
import os

def generate_stable_hash(text):
    """Generate a stable hash ID from a string."""
    return hashlib.sha256(text.encode('utf-8')).hexdigest()[:10]

def synthesize_speech(client, text, language_code):
    """Use Google Text-to-Speech API to synthesize speech and return audio content."""
    input_text = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(
        language_code=language_code, ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
    )
    audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)

    # Perform the text-to-speech request
    response = client.synthesize_speech(
        input=input_text, voice=voice, audio_config=audio_config
    )
    return response.audio_content

def main():
    # Load the .tsv file
    input_file = "input.tsv"  # Replace with your file path
    df = pd.read_csv(input_file, sep="\t")

    # Initialize Google Text-to-Speech client
    client = texttospeech.TextToSpeechClient()

    output_dir = "output_audio"
    os.makedirs(output_dir, exist_ok=True)

    texts_to_synthesize = []
    ids = []
    for index, row in df.iterrows():
        english_text = row['English']
        japanese_text = row['Japanese']

        # Generate a stable hash ID from the English text
        hash_id = generate_stable_hash(english_text)
        ids.append(hash_id)

        # Define output file paths
        english_audio_path = os.path.join(output_dir, f"{hash_id}_eng.mp3")
        japanese_audio_path = os.path.join(output_dir, f"{hash_id}_jp.mp3")

        texts_to_synthesize.append((english_text, "en-US", english_audio_path))
        texts_to_synthesize.append((japanese_text, "ja-JP", japanese_audio_path))

    # Add the hash IDs as a new column to the dataframe
    df['Id'] = ids

    # Save the updated dataframe back to the input file
    df.to_csv(input_file, sep="\t", index=False)

    # Synthesize and save audio for all texts
    for text, language_code, output_path in texts_to_synthesize:
        audio_content = synthesize_speech(client, text, language_code)
        with open(output_path, "wb") as out:
            out.write(audio_content)
        print(f"Audio content written to {output_path}")

if __name__ == "__main__":
    main()
