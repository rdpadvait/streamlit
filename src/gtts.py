import os
from typing import Dict, Optional

from google.cloud.texttospeech import (AudioConfig, AudioEncoding,
                                       SynthesisInput, TextToSpeechClient,
                                       VoiceSelectionParams)
from google.oauth2 import service_account

from logger import logger


def tts(
    text,
    lang_code,
    output_file="output.mp3",
    voice_name=None,
    credentials: Optional[Dict] = None,
    **kwargs,
):
    speed = kwargs.get("speed", 1.0)
    speaker = kwargs.get("speaker", "AP")
    if credentials:
        credentials = service_account.Credentials.from_service_account_info(credentials)
    CLIENT = TextToSpeechClient(credentials=credentials)
    input_text = SynthesisInput(text=text)

    audio_config = AudioConfig(
        audio_encoding=AudioEncoding.MP3, speaking_rate=speed
    )
    if not voice_name:
        voices = [
            voice.name
            for voice in CLIENT.list_voices(language_code=lang_code).voices
        ]
        if not voices:
            logger.error(f"No voices found for language: {lang_code}")
            raise ValueError(f"No voices found for language: {lang_code}")
        if f"{lang_code}-Chirp3-HD-Puck" in voices:
            voice_name = f"{lang_code}-Chirp3-HD-Puck" if speaker in ["AP", "MALE"] else f"{lang_code}-Chirp3-HD-Aoede"
        else:
            logger.warning(
                f"{lang_code} does not have Chirp Voice! Using other voices."
            )
            if f"{lang_code}-Wavenet-B" in voices:
                voice_name = f"{lang_code}-Wavenet-B"
            elif f"{lang_code}-Standard-B" in voices:
                voice_name = f"{lang_code}-Standard-B"
            else:
                raise ValueError(
                    f"Only available voices for {lang_code} are: {voices}"
                )
    logger.info(f"{voice_name} selected for {lang_code}")
    voice = VoiceSelectionParams(
        language_code=lang_code,
        name=voice_name,
    )
    response = CLIENT.synthesize_speech(
        request={"input": input_text, "voice": voice, "audio_config": audio_config}
    )
    with open(output_file, "wb") as out:
        out.write(response.audio_content)
        print(f'GTTS audio written to "{output_file}"')


if __name__ == "__main__":
    text = "ਹਿਰਨਕਸ਼ਯਪ ਸਿਰਫ ਰਾਜਾ ਹੀ ਨਹੀਂ ਸੀ, ਪ੍ਰਹਿਲਾਦ ਦਾ ਬਾਪ ਵੀ ਸੀ ਤੇ ਉਹ ਛੋਟੂ ਨੇ ਕਿਹਾ ਕਿ ਤੁਸੀਂ ਭਾਵੇਂ ਰਾਜਾ ਹੋ, ਭਾਵੇਂ ਬਾਪ ਹੋ ਮੇਰੇ, ਤੁਹਾਡਾ ਸਾਸ਼ਤਾਂ ਨਹੀਂ ਦਵਾਂਗਾ। ਪਹਿਲਾਂ ਤਾਂ ਉਹਨੂੰ ਬਹੁਤ ਲਾਲਚ ਦਿੱਤੇ ਤੇ ਬਹੁਤ ਡਰਾਇਆ ਧਮਕਾਇਆ ਵੀ, ਉਹ ਕਾਹਦੇ ਲਈ ਮੰਨੇ, ਬੋਲਿਆ ਮੈਂ ਨਹੀਂ ਮੰਨਦਾ। ਤਾਂ ਫਿਰ ਭੂਆ ਜੀ ਆਏ, ਭੂਆ ਜੀ ਨੂੰ ਕਿਹਾ ਗਿਆ ਹੈ ਕਿ ਇਹਨੂੰ ਨਾ ਚੁੱਪ ਚਾਪ ਗੋਦ 'ਚ ਬਿਠਾ ਕੇ ਅੱਗ ਤੋਂ ਗੁਜ਼ਰ ਜਾ, ਹੁਣ ਭੂਆ ਜੀ ਉਸਨੂੰ ਲੈ ਕੇ ਅੱਗ ਤੋਂ ਨਿਕਲੀ ਤਾਂ ਕਹਿਣ ਵਾਲੇ ਕਹਿੰਦੇ ਨੇ ਕਿ ਕੁਝ ਐਸੀ ਹਵਾ ਚੱਲੀ ਕਿ ਭੂਆ ਜੀ ਨੇ ਜੋ ਉੱਤੇ ਪਾ ਰੱਖਿਆ ਸੀ, ਉਹ ਉੱਡ ਕੇ ਪ੍ਰਹਿਲਾਦ ਤੇ ਚਲਾ ਗਿਆ ਤਾਂ ਪ੍ਰਹਿਲਾਦ ਤਾਂ ਬਚ ਗਿਆ ਤਾਂ ਭੂਆ ਜੀ ਨੂੰ ਇੰਨੇ ਜ਼ਖਮ ਆਏ ਹੋਣਗੇ, ਇੰਨਾ ਸੜ ਗਈ ਹੋਏਗੀ ਕਿ ਭੂਆ ਜੀ ਫਿਰ ਸਾਫ ਹੋ ਗਏ। ਹੁਣ ਰਾਜੇ ਨੂੰ ਆਇਆ ਗੁੱਸਾ ਤਾਂ ਇੱਕ ਲੋਹੇ ਦਾ ਖੰਭਾ ਬਿਲਕੁਲ ਗਰਮ ਕਰਵਾ ਦਿੱਤਾ, ਛੋਟੂ ਨੂੰ ਡਰ ਤਾਂ ਲੱਗਿਆ ਹੋਵੇਗਾ, ਜੋ ਵੀ ਹੋਇਆ ਹੋਵੇਗਾ ਪਰ ਪ੍ਰਹਿਲਾਦ ਬੋਲਿਆ ਠੀਕ ਹੈ ਪਰ ਤੁਹਾਨੂੰ ਤਾਂ ਨਹੀਂ ਮੰਨ ਲਵਾਂਗਾ ਭਗਵਾਨ ਤਾਂ ਉਹ ਗਿਆ ਉਹਨੇ ਖੰਭੇ ਫਿਰ ਇੱਕ ਜੀਵ ਪ੍ਰਗਟ ਹੋਇਆ ਜੋ ਅੱਧਾ ਸ਼ੇਰ ਸੀ, ਅੱਧਾ ਇਨਸਾਨ ਸੀ। ਤੇ ਸਮਾਂ ਸੂਰਜ ਡੁੱਬਣ ਵਾਲਾ ਹੋ ਰਿਹਾ ਸੀ, ਜਦੋਂ ਨਾ ਤਾਂ ਦਿਨ ਸੀ, ਨਾ ਰਾਤ ਸੀ ਤੇ ਉਹਨੇ ਫੜ ਲਿਆ ਹਿਰਨਕਸ਼ਯਪ ਨੂੰ ਤੇ ਆਪਣੀ ਗੋਦ ਵਿੱਚ ਲੰਮਾ ਪਾ ਲਿਆ ਕਿ ਯਾਨੀ ਨਾ ਤਾਂ ਤੁਸੀਂ ਹਵਾ ਵਿੱਚ ਹੋ, ਨਾ ਤੁਸੀਂ ਜ਼ਮੀਨ ਤੇ ਹੋ, ਨਾਲੇ ਨਾ ਅਸਤਰ ਨਾਲ ਮਰੋਗੇ, ਨਾ ਸ਼ਸਤਰ ਨਾਲ। ਯਾਨੀ ਹੱਥ ਵਿੱਚ ਫੜੀ ਹੋਈ ਚੀਜ਼ ਨਾਲ ਵੀ ਨਹੀਂ ਮਰੋਗੇ ਤੇ ਜੋ ਉੱਡਦੀ ਹੋਈ ਚੀਜ਼ ਆਉਂਦੀ ਹੈ ਉਹਦੇ ਨਾਲ ਵੀ ਨਹੀਂ ਮਰੋਗੇ, ਉਹਨੇ ਕਿਹਾ ਠੀਕ ਹੈ, ਕੁਝ ਹੱਥ ਵਿੱਚ ਫੜ ਨਹੀਂ ਰੱਖਿਆ, ਉਹਨੇ ਮਾਰਿਆ ਆਪਣੇ ਨਹੂਆਂ ਨਾਲ, ਇਸ ਪੂਰੀ ਕਥਾ ਦਾ, ਇਸ ਤਿਉਹਾਰ ਦਾ ਚਿਕਨ ਤੇ ਸ਼ਰਾਬ ਨਾਲ ਕੀ ਸੰਬੰਧ ਹੈ ਮੈਨੂੰ ਸਮਝਾਓ। ਤੁਸੀਂ ਇੱਕ ਛੋਟੇ ਬੱਚੇ ਦੀ ਸਰਲਤਾ ਦੀ ਸਫਲਤਾ ਦਾ ਉਤਸਵ ਮਨਾ ਰਹੇ ਹੋ, ਤੁਸੀਂ ਇੱਕ ਜ਼ਾਲਮ ਬਾਦਸ਼ਾਹ ਦੇ ਹੰਕਾਰ ਤੇ ਚਲਾਕੀ ਦੀ ਹਾਰ ਦਾ ਜਸ਼ਨ ਮਨਾ ਰਹੇ ਹੋ, ਇਹਦੇ 'ਚ ਚਿਕਨ ਤੇ ਦਾਰੂ ਕਿੱਥੋਂ ਆ ਗਏ ਤੇ ਉਹਦੇ 'ਚ ਇਹ ਹੁੱਲੜ ਕਿੱਥੋਂ ਆ ਗਿਆ। ਚਿੱਕੜ ਸੁੱਟਣਾ ਤੇ ਬਕਵਾਸ ਕਰਨਾ ਤੇ ਭਾਬੀ ਨੂੰ ਰੰਗਣਾ, ਭਾਬੀਆਂ ਨਾਲ ਬਹੁਤ ਪਿਆਰ ਹੋ ਜਾਂਦਾ ਹੈ ਹੋਲੀ ਵਾਲੇ ਦਿਨ, ਅੱਧੇ ਸ਼ਹਿਰ ਦੀਆਂ ਔਰਤਾਂ ਉਸ ਦਿਨ ਭਾਬੀ ਹੋ ਜਾਂਦੀਆਂ ਨੇ।"
    lang_code = "pa-IN"
    tts(
        text,
        lang_code,
        output_file=f"debug/{lang_code}.mp3",
    )
