import json
import logging
import os
import time
from typing import Any, Dict

from openai import OpenAI

from src.process import is_valid_output, parse_text, process_citations
from src.utils import read

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
LOGGER = logging.getLogger("AskAP")


class AssistantInteraction:
    MAX_RETRIES = 1

    def __init__(self, assistant_id: str, md_path: str) -> None:
        self.assistant_id = assistant_id
        self.articles_md = read(md_path)
        assert os.getenv("OPENAI_API_KEY"), "OpenAI API Key not set."
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        LOGGER.info(f"Initialized assistant: {self.assistant_id}")

    def create_thread_and_send_message(self, question: str) -> str:
        thread_id = self.client.beta.threads.create().id
        LOGGER.info(f"Created thread: {thread_id}")
        return {
            "thread_id": thread_id,
            "message_id": self.client.beta.threads.messages.create(
                thread_id=thread_id, role="user", content=question
            ).id,
        }

    def get_response(self, thread_id: str) -> Any:
        if not thread_id:
            raise ValueError("Thread ID is not set. Create a thread first.")
        self.client.beta.threads.runs.create_and_poll(
            assistant_id=self.assistant_id, thread_id=thread_id
        )
        messages = self.client.beta.threads.messages.list(thread_id=thread_id)
        return messages.data[0].content[0].text

    def postprocess(self, output: Any) -> Dict[str, Any]:
        process_citations(self.client, output)
        return parse_text(output.value, self.articles_md)

    def interact(self, question: str) -> Dict[str, Any]:
        LOGGER.info(f"Question: {question}")
        ids = self.create_thread_and_send_message(question)
        final_output = {
            "header": "Please elaborate or rephrase the question.",
            "insights": [],
        }

        for attempt in range(self.MAX_RETRIES + 1):
            try:
                output = self.get_response(ids["thread_id"])
            except Exception as e:
                LOGGER.error(f"Error retrieving response: {e}")
                output = ""
            if not output:
                LOGGER.warning(
                    f"No response received for question: {question}. Attempting retry {attempt + 1}/{self.MAX_RETRIES}"
                )
                continue

            LOGGER.info(f"<RAW_RESPONSE> {output.value} </RAW_RESPONSE>")
            processed_output = self.postprocess(output)
            LOGGER.info(
                f"Processed response: {json.dumps(processed_output, indent=2, ensure_ascii=False)}"
            )

            if is_valid_output(processed_output):
                LOGGER.info(f"!Valid response!")
                final_output = processed_output
                break
            else:
                LOGGER.warning(
                    f"Invalid response. "
                    + (
                        f"Retry {attempt + 1}/{self.MAX_RETRIES}"
                        if attempt < self.MAX_RETRIES
                        else f"Max retries reached"
                    )
                    + f""" for question: "{question}"."""
                )
        return final_output


def main():
    assistant = AssistantInteraction(
        "asst_3Mp4nLnLS13ciCRWUjkFO6hz", "data/articles_relevant_keys.json"
    )
    import sys

    if len(sys.argv) > 1:
        question = sys.argv[1]
        start = time.time()
        assistant.interact(question)
        end = time.time()
        print(f"Time taken: {end - start:.2f}s")
    else:
        questions = read("data/search_bar.txt")
        answers = read("data/cached_answers.json")
        for question in questions:
            question = question.strip().lower()
            if question not in answers:
                answers[question] = assistant.interact(question)
        with open("data/cached_answers.json", "w") as f:
            json.dump(answers, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()
