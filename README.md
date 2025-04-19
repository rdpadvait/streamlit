### ALL STREAMLIT FUNCTIONS

### Pre Requisites
1. OpenAI
    - Environment variable `OPENAI_API_KEY`
2. ElevenLabs
    - Environment variable `ELEVENLABS_API_KEY` with text-to-audio permissions
    - Dubbing voice ids in `.env` file
3. Google
    - Google credesntials in repo file `.streamlit/secrets.toml` file
4. `conda`

### Installation

To install the required dependencies, run:

```bash
pip install -r requirements.txt
```
or
```bash
> conda env create -f conda.yml
> conda activate srssssss
```

### Running the UI

To start the application, execute:

```bash
streamlit run ask_ap.py
```

### Asking a Question

To just get answer for a question, execute:

```bash
python -m src.answer "What is suffering?"

### Code

1. Entry point is `ask_ap.py` file
```