import re
from typing import Any, Dict

from openai import OpenAI

from src.utils import read


def convert_to_embed_url_with_time(youtube_url: str) -> str:
    youtube_regex = (
        r"(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:watch\?v=|embed\/)|youtu\.be\/)"
        r"([a-zA-Z0-9_-]{11})"
    )

    match = re.search(youtube_regex, youtube_url)
    if not match:
        raise ValueError("Invalid YouTube URL")

    video_id = match.group(1)

    start_time_match = re.search(r"[?&](?:t|start)=(\d+)", youtube_url)
    start_time = f"?start={start_time_match.group(1)}" if start_time_match else ""

    return f"https://www.youtube.com/embed/{video_id}{start_time}"


def process_citations(client: OpenAI, output):
    for annotation in output.annotations:
        if citation := getattr(annotation, "file_citation", None):
            fname = client.files.retrieve(citation.file_id).filename
            if annotation.text not in output.value:
                print(f"Citation not found in output: {annotation.text}")
            output.value = output.value.replace(
                annotation.text, f"<file>{fname}</file>"
            )
        else:
            print(f"Unprocessed citation: {annotation}")


def parse_header(text: str) -> tuple[str, str]:
    if ":" in text:
        header, text_without_header = text.split(":", 1)
        header += ":"
        return header.strip(), text_without_header.strip()
    else:
        return (text, "")


def parse_text(text: str, articles_md: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    text = text.replace("“", '"').replace("”", '"')
    header, text_without_header = parse_header(text)
    pattern = r"\"([^\"]*?)\"([^\"]*?)<file>(.*?)</file>"
    matches = re.findall(pattern, text_without_header, flags=re.DOTALL)
    insights = []
    for quote, _, filename in matches:
        insight_data = {"quote": f'"{quote.strip()}"'}
        article_data = articles_md[filename]
        if video_url := article_data.get("youtubeURL"):
            insight_data["video_url"] = video_url
        if article_url := article_data.get("url"):
            insight_data["article_url"] = article_url
            insight_data["article_title"] = article_data.get("title", "Article")
        insights.append(insight_data)
    footer = ""
    if "</file>" in text_without_header:
        footer_section = text_without_header.split("</file>")[-1].strip()
        if "\n" in footer_section:
            footer = footer_section.split("\n")[-1].strip()
    return {"header": header, "insights": insights, "footer": footer}


def is_valid_output(parsed_output):
    valid_strings = [
        "मुझे इस बारे में जानकारी नहीं हैं।",
        "I don't know about this.",
        "मैं इसका उत्तर देने में असमर्थ हूँ।",
        "I am unable to answer this question.",
    ]
    if any([string in str(parsed_output) for string in valid_strings]):
        return True
    if all([(not el.get("article_url")) for el in parsed_output["insights"]]):
        return False
    return True


if __name__ == "__main__":
    example_texts = [
        r"""Acharya Ji has shared the following insights on your question: 

1. "व्यवसायात्मिका बुद्धिरेकेह कुरुनन्दन। बहुशाखा ह्यनन्ताश्च बुद्धयोऽव्यवसायिनाम्।" 
   - Translation: "In this, there is a single, one-pointed conviction. The thought of irresolute ones have many branches indeed and are innumerable." 
   - Source: <file>000000.json</file>

2. "ये हमारी व्यावहारिक बल्कि एक प्रकार की व्यावसायिक बुद्धि है। बुद्धि चल इसमें भी रही है, निर्णय यहाँ भी हो रहे हैं — ऊँचे-नीचे, सही-ग़लत, अच्छे-बुरे; इनका निर्णय बिलकुल हो रहा है।" 
   - Translation: "This is our practical but a kind of business intelligence. Intelligence is also working here, decisions are being made here — high-low, right-wrong, good-bad; decisions are definitely being made." 
   - Source: <file>000000.json</file> 

These quotes reflect the concept of "व्यवसायात्मिक बुद्धि" as discussed by Acharya Prashant.""",
        r"""Acharya Ji has shared the following insights on your question: 
“If you’re talking to me, one of the options is to go to my website and put in your name. We have initiated a program to send the Upanishads to whosoever enrolls with us. Within a month or two, you’ll receive a copy of the Sarvasar Upanishad. It might answer some of your questions. It’s a free copy, you may just go there and enter your details, and you’ll receive it. And if you don’t want to wait for a few months, then you may enroll in some of the Gītā courses that we have, that might help. Or you may decide to begin with your own copy of Gītā. Whatever you decide, just begin.”alpha<file>000000.json</file>. 


For more information, "you" can visit the Gita Community page on Acharya Prashant's website.<file>000001.json</file>.""",
    ]
    print(
        parse_text(
            example_texts[0],
            read("data/articles_relevant_keys.json"),
        )
    )
