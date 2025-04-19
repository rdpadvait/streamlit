import json
import os

import dotenv
from elevenlabs import ElevenLabs

dotenv.load_dotenv()

CLIENT = ElevenLabs(api_key=os.environ["ELEVENLABS_API_KEY"])


def get_voice_id(speaker):
    if speaker == "MALE":
        return os.environ["RAJU_ID"]
    elif speaker == "FEMALE":
        return os.environ["MONIKA_ID"]
    else:
        raise ValueError(f"Invalid speaker: {speaker}")
    
def sts(input_file: str, output_file: str, **kwargs):
    speaker = kwargs.get("speaker", "AP")
    voice_id = os.environ["IVC_ID"] if speaker == "AP" else get_voice_id(speaker)
    with open(input_file, "rb") as f:
        audio = f.read()
    audio = CLIENT.speech_to_speech.convert(
        audio=audio,
        voice_id=voice_id,
        output_format="mp3_44100_128",
        model_id="eleven_multilingual_sts_v2",
        enable_logging=True,
        voice_settings=json.dumps(
            {
                "stability": 0.5,
                "similarity_boost": 1.0,
                "style": 0.0,
                "use_speaker_boost": True,
            }
        ),
    )
    with open(output_file, "wb") as f:
        for chunk in audio:
            f.write(chunk)
    print(f"✅ Audio saved successfully as '{output_file}'")


def tts(text, output_file="output.mp3", **kwargs):
    speed = kwargs.get("speed", 1.0)
    speaker = kwargs.get("speaker", "AP")
    voice_id = os.environ["PVC_ID"] if speaker == "AP" else get_voice_id(speaker)
    print(f"Using ElevenLabs API for text-to-speech conversion")
    audio = CLIENT.text_to_speech.convert(
        text=text,
        voice_id=voice_id,
        output_format="mp3_44100_128",
        model_id="eleven_multilingual_v2",
        enable_logging=True,
        voice_settings={
            "stability": 0.5,
            "similarity_boost": 1.0,
            "style": 0.0,
            "speed": speed,
            "use_speaker_boost": True,
        },
    )
    with open(output_file, "wb") as f:
        for chunk in audio:
            f.write(chunk)
    print(f"✅ Audio saved successfully as '{output_file}'")

if __name__ == "__main__":
    tts("HOW ARE YOU DOING", output_file="output.mp3")