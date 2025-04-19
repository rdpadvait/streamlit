import os

from openai import OpenAI
from tqdm import tqdm

from src.process import parse_text, process_citations

bcolors = {
    "HEADER": "\033[95m",
    "OKBLUE": "\033[94m",
    "OKCYAN": "\033[96m",
    "OKGREEN": "\033[92m",
    "WARNING": "\033[93m",
    "FAIL": "\033[91m",
    "ENDC": "\033[0m",
    "BOLD": "\033[1m",
    "UNDERLINE": "\033[4m",
}


def upload_file(client: OpenAI, file_path: str, vector_store_id: str):
    with open(file_path, "rb") as file:
        uploaded = client.files.create(file=file, purpose="assistants")
        print(f"{uploaded.filename}: {uploaded.status}")
        res = client.beta.vector_stores.files.create_and_poll(
            vector_store_id=vector_store_id,
            file_id=uploaded.id,
        )
        print(f"{uploaded.filename}: {res.status}")


def upload_file_batch(client: OpenAI, file_paths: list, vector_store_id: str):
    files = [open(path, "rb") for path in file_paths]
    file_batch = client.beta.vector_stores.file_batches.upload_and_poll(
        vector_store_id=vector_store_id, files=files
    )
    # client.beta.vector_stores.async_file_batches.create(vector_store_id=vector_store_id, files=files)
    print(f"Batch status: {file_batch.status}")
    print(f"File counts in batch: {file_batch.file_counts}")


def create_vector_store(client: OpenAI, articles_dir, vector_store_id=None):
    vector_store_id = vector_store_id or client.beta.vector_stores.create().id
    print(f"Vector store ID: {vector_store_id}")
    file_names = sorted(os.listdir(articles_dir))
    file_paths = [os.path.join(articles_dir, file) for file in file_names][:3229]
    print(f"Reading {len(file_paths)} files. Example file: {file_paths[-1]}")

    file_streams = [open(path, "rb") for path in file_paths]
    batches = [file_streams[i : i + 500] for i in range(0, len(file_streams), 500)]

    for batch in tqdm(batches, desc="Uploading file batches"):
        breakpoint()
        file_batch = client.beta.vector_stores.file_batches.upload_and_poll(
            vector_store_id=vector_store_id, files=batch
        )
        print(f"Batch status: {file_batch.status}")
        print(f"File counts in batch: {file_batch.file_counts}")

    return vector_store_id


def upload_vector_store():
    client = OpenAI()
    # write("final_files2.txt", "\n".join([f["filename"] for f in client.files.list().to_dict()["data"]]))
    vector_store_id = "vs_p0N3kJVZjg9UKsNoAVMqQhhq"  # "vs_AhcDunMrsJciEMtcFgpFGuux"
    # vector_store_id = client.beta.vector_stores.create(name="New Articles").id
    print(f"Vector store ID: {vector_store_id}")
    vector_store = client.beta.vector_stores.retrieve(vector_store_id)
    print(f"{bcolors.OKGREEN}{vector_store}{bcolors.ENDC}")
    articles_dir = "data/new_articles"
    file_paths = [
        os.path.join(articles_dir, file) for file in sorted(os.listdir(articles_dir))
    ][8517:]
    for file_path in tqdm(file_paths, desc="Uploading files"):
        upload_file(client, file_path, vector_store_id)
    # create_vector_store(client, articles_dir, vector_store_id)


def main():
    client = OpenAI()
    ASSISTANT_ID = "asst_3Mp4nLnLS13ciCRWUjkFO6hz"
    question = "J krishnamurti says choice is very denial of freedom, but as after listening you and reading about Bhagat Singh I came to know that greats like Bhagat Singh chose to live a life of a revolutionary. So , there is a term ( Chunav ) which is choice. \nSo, these 2 defination of choice are contradicting with each other.\nWhat really choice means ??"
    assistant = client.beta.assistants.retrieve(ASSISTANT_ID)
    print(f"Assistant: {bcolors.OKGREEN}{assistant.name}{bcolors.ENDC}")

    thread_id = client.beta.threads.create().id
    message_id = client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=question,
    )
    run = client.beta.threads.runs.create_and_poll(
        assistant_id=ASSISTANT_ID,
        thread_id=thread_id,
    )  # answer generated in this step!

    messages = client.beta.threads.messages.list(thread_id=thread_id)

    message_content = messages.data[0].content[0].text
    process_citations(client, message_content)
    print(f"{bcolors.OKBLUE}{message_content.value}{bcolors.ENDC}")


if __name__ == "__main__":
    main()
