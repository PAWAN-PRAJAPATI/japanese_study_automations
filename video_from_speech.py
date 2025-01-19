import os
import pandas as pd
import textwrap
from moviepy.editor import TextClip, AudioFileClip, concatenate_videoclips, concatenate_audioclips
from pydub import AudioSegment
from sklearn.utils import shuffle

def wrap_text(text, width=40):
    """Wrap text to prevent overflow in video frames."""
    return "\n".join(textwrap.wrap(text, width=width))

def create_text_clip(text, duration, fontsize=50, font="Arial Unicode MS", size=(1280, 720), color='white', bg_color='black'):
    """Create a text clip with specified properties."""
    return TextClip(text, fontsize=fontsize, font=font, color=color, size=size, bg_color=bg_color).set_duration(duration)

def process_row(row, input_audio_dir, tick_audio_path, beep_audio_path, silence_audio_path, m_repeat, mn_repeat):
    """Process a single row from the input DataFrame."""
    hash_id = row['Id']
    japanese_text = wrap_text(row['Japanese'])
    roman_text = wrap_text(row.get('Roman', ""))
    english_text = wrap_text(row['English'])

    japanese_audio_path = os.path.join(input_audio_dir, f"{hash_id}_jp.mp3")
    english_audio_path = os.path.join(input_audio_dir, f"{hash_id}_eng.mp3")

    if not os.path.exists(japanese_audio_path) or not os.path.exists(english_audio_path):
        print(f"Skipping {hash_id} due to missing audio files.")
        return None, None

    try:
        jp_audio = AudioFileClip(japanese_audio_path)
        eng_audio = AudioFileClip(english_audio_path)
        tick_audio = AudioFileClip(tick_audio_path)
        silence_audio = AudioFileClip(silence_audio_path)

        jp_text_clip = create_text_clip(f"{japanese_text}\n{roman_text}", jp_audio.duration)
        silence_text_clip = create_text_clip(f"{japanese_text}\n{roman_text}", silence_audio.duration)
        eng_text_clip = create_text_clip(english_text, eng_audio.duration, fontsize=40)
        tick_clip = create_text_clip("...", tick_audio.duration, fontsize=40)

        repeated_text_clip = concatenate_videoclips([jp_text_clip, silence_text_clip] * mn_repeat)
        repeated_text_clip = concatenate_videoclips([repeated_text_clip, tick_clip, eng_text_clip] * m_repeat)
        repeated_audio = concatenate_audioclips([jp_audio, silence_audio] * mn_repeat)
        repeated_audio = concatenate_audioclips([repeated_audio, tick_audio, eng_audio] * m_repeat)

        beep_audio_clip = AudioFileClip(beep_audio_path)
        next_clip = create_text_clip("next...", beep_audio_clip.duration, fontsize=40)

        combined_video = concatenate_videoclips([repeated_text_clip, next_clip])
        combined_audio = concatenate_audioclips([repeated_audio, beep_audio_clip])

        return combined_video.set_audio(combined_audio), combined_audio
    except Exception as e:
        print(f"Error processing row {hash_id}: {e}")
        return None, None

def process_batch(df_batch, input_audio_dir, tick_audio_path, beep_audio_path, silence_audio_path, output_dir, batch_index, m_repeat, mn_repeat, fps):
    """Process a batch of rows to create video and audio files."""
    clips = []
    audios = []
    chapter = "0"
    for _, row in df_batch.iterrows():
        video_clip, audio_clip = process_row(row, input_audio_dir, tick_audio_path, beep_audio_path, silence_audio_path, m_repeat, mn_repeat)
        if video_clip and audio_clip:
            clips.append(video_clip)
            audios.append(audio_clip)
        chapter = row['Chapter']
    if clips:
        final_clip = concatenate_videoclips(clips)
        final_audio = concatenate_audioclips(audios)
        video_output_path = os.path.join(output_dir, f"output_video_{batch_index + 1}.mp4")
        audio_output_path = os.path.join(output_dir, f"output_audio_{batch_index + 1}.mp3")
        merged_video_path = os.path.join(output_dir, f"chapter_{chapter}_{batch_index + 1}.mp4")

        final_clip.write_videofile(video_output_path, 
                                   codec='libx264', 
                                   audio_codec='aac', 
                                   fps=fps,
                                   remove_temp=True)
        final_audio.write_audiofile(audio_output_path)
        merge_video_audio(video_output_path, audio_output_path, merged_video_path, fps)

        os.remove(video_output_path)
        os.remove(audio_output_path)
    else:
        print(f"No valid clips to concatenate for batch {batch_index + 1}.")

def merge_video_audio(vidname, audname, outname, fps):
    """Merge video and audio into a final output video."""
    from moviepy.editor import VideoFileClip, AudioFileClip
    video_clip = VideoFileClip(vidname)
    audio_background = AudioFileClip(audname)
    final_clip = video_clip.set_audio(audio_background)
    final_clip.write_videofile(outname, fps=fps)

def create_videos(input_file, output_dir, input_audio_dir, n_text=5, m_repeat=1, mn_repeat=2, fps=3):
    """Create videos from text and audio files."""
    df = pd.read_csv(input_file, sep="\t")
    df = shuffle(df)
    beep_audio_path = "./resource/next.mp3"
    tick_audio_path = "./resource/tick.mp3"
    silence_audio_path = "./resource/silence.mp3"

    for batch_index, start_row in enumerate(range(0, len(df), n_text)):
        df_batch = df.iloc[start_row:start_row + n_text]
        process_batch(df_batch, input_audio_dir, tick_audio_path, beep_audio_path, silence_audio_path, output_dir, batch_index, m_repeat, mn_repeat, fps)

if __name__ == "__main__":
    input_file = "input.tsv"  # Path to your .tsv file
    input_audio_dir = "output_audio"  # Directory containing audio files
    output_dir = "output_video"
    os.makedirs(output_dir, exist_ok=True)

    create_videos(input_file, output_dir, input_audio_dir, n_text=5, m_repeat=3, mn_repeat=2, fps=3)
