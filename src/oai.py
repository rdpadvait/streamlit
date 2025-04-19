import base64
import os
from typing import Optional

from omegaconf import OmegaConf
from openai import OpenAI

from logger import logger


class OpenAIHandler:
    def __init__(self, configs_dir: Optional[str] = "configs"):
        self.client = OpenAI()
        self.configs_dir = configs_dir
        self.translation_config = OmegaConf.load(os.path.join(configs_dir, "translate.yaml"))
        self.transcription_config = OmegaConf.load(os.path.join(configs_dir, "transcribe_no_speaker.yaml"))
        logger.info(f"OpenAIHandler initialized")
    
    def translate(self, input_text: str, language: str = "English", **kwargs) -> str:
        if not input_text:
            return ""
        logger.info(f"Translating to {language}: ```{input_text}```")
        config = OmegaConf.to_container(self.translation_config, resolve=True)
        for key, value in kwargs.items():
            if key in config:
                config[key] = value
                logger.info(f"Overriding config parameter {key} with value {value}")
                
        system_prompt = config["system_prompt"].format(language=language)  
        
        try:
            response = self.client.chat.completions.create(
                model=config["model"],
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": input_text}
                ],
                response_format={"type": config["response_format"]},
                temperature=config["temperature"],
                max_tokens=config["max_tokens"],
                top_p=config["top_p"],
                frequency_penalty=config["frequency_penalty"],
                presence_penalty=config["presence_penalty"]
            )
            
            output_text = response.choices[0].message.content
            if len(parts := output_text.split("```")) >= 3:
                output_text = parts[1].strip()
            logger.info(f"{language} translation: ```{output_text}```")
            return output_text
        except Exception as e:
            logger.error(f"An error occurred during translation: {e}")
            raise e
    
    def transcribe(self, audio_path: str, **kwargs) -> str:
        logger.info(f"Transcribing audio file: {audio_path}")
        
        config = OmegaConf.to_container(self.transcription_config, resolve=True)
        for key, value in kwargs.items():
            if key in config:
                config[key] = value
                logger.info(f"Overridden config value: {key}={value}")
        
        with open(audio_path, "rb") as f:
            config["messages"][-1]["content"][-1]["input_audio"]["data"] = base64.b64encode(
                f.read()
            ).decode("utf-8")

        try:
            out = (
                self.client.chat.completions.create(
                    model=config["model"],
                    messages=config["messages"],
                    modalities=config["modalities"],
                    temperature=config["temperature"],
                    max_completion_tokens=config["max_completion_tokens"],
                    top_p=config["top_p"],
                    frequency_penalty=config["frequency_penalty"],
                    presence_penalty=config["presence_penalty"],
                )
                .choices[0]
                .message.content
            )
            if not out:
                raise RuntimeError(f"Empty transcript for {audio_path}")
            logger.info(f"Transcription completed for audio file: {audio_path}")
            return out.strip().strip("...")
        except Exception as e:
            logger.error(f"An error occurred during transcription: {e}")
            raise e

if __name__ == "__main__":
    text = """शादी के बाद देख लोगे कि लड़के लड़की दोनों का वजन पाँच-पाँच किलो न बढ़ गया हो तो दो साल के अंदर। और उसके तीन-चार साल और बीतने दो बच्चे हो जाते हैं तो इतने ही मोटे-मोटे हो जाते हैं। अब बीमार नहीं पड़ोगे क्या? और वो इतने मोटे होकर रहेंगे क्योंकि वो अब जिस मजबूर जिंदगी में फँस गए हैं, उसमें कहाँ समय है खेलने का, कूदने का, व्यायाम करने का। एक जो आम मध्यम वर्गीय गृहस्थ होता है, उसके पास समय होता है क्या कि वो जा करके एक घंटा badminton खेले, swimming करे, gyming करे, होता है? दौड़ लगाए? वो तो अब जीवन की चक्की में पिस रहा है, पिस रहा है। अब जीवन की चक्की में पिस रहा है तो बीमार भी पड़ेगा। विवेकानंद ने एक बार इसी लिए किसी संदर्भ में कह दिया था। आए होंगे कुछ कमजोर लोग उनके पास। उनसे बोलते, तुम्हारे लिए गीता से ज़्यादा महत्वपूर्ण है football खेलना। तुम तन से इतने कमजोर हो, तुमसे मैं कैसे कह दूँ कि आज़ाद जिंदगी जियो। पहले शरीर ठीक करो।"""
    handler = OpenAIHandler()
    bengali_translation = handler.translate(text, "Bengali")
    print("Translated text:", bengali_translation)
