import os
from typing import Any

from openai import OpenAI


class BaseAssistant:
    def __init__(self, assistant_id: str):
        self.assistant_id = assistant_id
        self.client = OpenAI()

    def create_thread(self) -> str:
        return self.client.beta.threads.create().id

    def create_message(self, thread_id: str, role: str, content: str) -> str:
        return self.client.beta.threads.messages.create(
            thread_id=thread_id, role=role, content=content
        ).id

    def run_and_poll(self, thread_id: str) -> None:
        self.client.beta.threads.runs.create_and_poll(
            assistant_id=self.assistant_id, thread_id=thread_id
        )

    def get_messages(self, thread_id: str) -> Any:
        return self.client.beta.threads.messages.list(thread_id=thread_id).data

    def get_response(self, input_text: str) -> str:
        thread_id = self.create_thread()
        self.create_message(thread_id, role="user", content=input_text)
        self.run_and_poll(thread_id)
        return self.get_messages(thread_id)[0].content[0].text
