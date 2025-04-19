import logging
import re
from typing import Any

from omegaconf import OmegaConf
from openai import OpenAI

from src.assistant import BaseAssistant
from src.process import process_citations, read

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)


class ReplierAssistant(BaseAssistant):
    def __init__(self, assistant_id: str, mapping_file: str):
        super().__init__(assistant_id)
        logging.info(f"Initializing ReplierAssistant with ID: {assistant_id}")
        self.mapping = read(mapping_file)
        logging.info(f"Mapping file '{mapping_file}' loaded successfully")

    def postprocess(self, output: Any) -> str:
        logging.info("Postprocessing output")
        process_citations(self.client, output)
        filenames = re.findall(r"<file>(.*?)</file>", output.value)
        logging.debug(f"Extracted filenames from output: {filenames}")
        for filename in filenames:
            yt_url = self.mapping[filename].get("youtubeURL")
            url = self.mapping[filename].get("url")
            replacement = f" (see {url} or {yt_url})" if yt_url else f" (see {url})"
            output.value = output.value.replace(f"<file>{filename}</file>", replacement)
            logging.debug(f"Replaced <file>{filename}</file> with {replacement}")
        return output.value

    def interact(self, input_text: str) -> str:
        logging.info(f"Interacting with input: {input_text}")
        response = self.get_response(input_text)
        out = self.postprocess(response)
        logging.info(f"Replier Assistant Output: ```{out}```")
        logging.info("!Replied!")
        return out


class ReplierChat:
    def __init__(self, config_path: str):
        logging.info(f"Initializing ReplierChat with config path: {config_path}")
        self.client = OpenAI()
        self.config = OmegaConf.load(config_path)
        logging.info(f"Configuration loaded from '{config_path}'")

    def reply(self, input: str):
        logging.info(f"Generating reply for input: ```{input}```")
        response = self.client.chat.completions.create(
            model=self.config.model,
            messages=[
                self.config.system_message,
                {"role": "user", "content": input},
            ],
            response_format=self.config.response_format,
            temperature=self.config.temperature,
            max_completion_tokens=self.config.max_completion_tokens,
            top_p=self.config.top_p,
            frequency_penalty=self.config.frequency_penalty,
            presence_penalty=self.config.presence_penalty,
        )
        output = response.choices[0].message.content
        if output.endswith('"') and output.startswith('"'):
            output = output[1:-1]
        logging.info(f"Replier Chat Output: ```{output}```")
        logging.info("Replied!")
        return output


if __name__ == "__main__":
    chat = ReplierChat("configs/replier.yaml")
    user_input = "स्वम्भू आचार्य प्रशांत एक वामपंथी कीड़ा हैं"
    print(chat.reply(user_input))
