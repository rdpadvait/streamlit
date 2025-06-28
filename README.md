### ALL STREAMLIT FUNCTIONS

### Pre Requisites
1. OpenAI
    - Environment variable `OPENAI_API_KEY`
2. ElevenLabs
    - Environment variable `ELEVENLABS_API_KEY` with text-to-audio permissions
    - Dubbing voice ids in `.env` file
3. Google
    - Google credentials in repo file `.streamlit/secrets.toml` file
4. Python 3.12+ (conda or virtual environment)

### Installation

To install the required dependencies, run:

**Option 1: Using conda (recommended)**
```bash
conda env create -f conda.yml
conda activate sr
```

**Option 2: Using Poetry (modern Python dependency management)**
```bash
# Install Poetry if you haven't already
curl -sSL https://install.python-poetry.org | python3 -

# Initialize Poetry project and install dependencies
poetry init --no-interaction
poetry add $(cat requirements.txt | grep -v "^#" | tr '\n' ' ')
poetry install

# Activate Poetry environment
poetry shell
```

**Option 3: Using virtual environment**
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
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
```

### Code

1. Entry point is `ask_ap.py` file

### Setup TTS Google Creds

#### 🔹 Step 1: Create a New Google Cloud Project

1. Go to: [https://console.cloud.google.com/](https://console.cloud.google.com/)
2. In the top navigation bar, click the **project dropdown**.
3. Click **“New Project”**
4. Fill in:
   - **Project Name**: e.g., `gtts-assistant` or any name you prefer
   - **Billing Account**: Select an existing billing account, or create one
   - **Organization**: Optional (default is fine)
5. Click **Create**
6. Once created, **switch to this new project** using the same dropdown

---

#### 🔹 Step 2: Enable Required APIs

Enable the **Text-to-Speech API**:

- Navigate to: `APIs & Services` → `Library`
- Search: **Text-to-Speech API**
- Click on it and press **Enable**

---

#### 🔹 Step 3: Create a Service Account

1. Go to: `IAM & Admin` → `Service Accounts`
2. Click **“Create Service Account”**
3. Enter the following:
   - **Service account name**: `deployment` (or any name)
4. Click **Create and Continue**
5. Assign a role:
   - Recommended: **Project > Editor**  
     Or a more specific role like: **Text-to-Speech Admin**
6. Click **Done**

---

#### 🔹 Step 4: Generate and Download Service Account Key

1. In the service account list, click the name of your newly created account
2. Go to the **Keys** tab
3. Click **“Add Key” → “Create new key”**
4. Select **JSON** format
5. Click **Create**

💾 A `.json` key file will download to your system — keep this file **secure**.

---

#### 🔹 Step 5: Extract Required Fields for Configuration

Open the `.json` key file you downloaded. It will look something like this:

```json
{
  "type": "service_account",
  "project_id": "your-project-id",
  "private_key_id": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEv...\n-----END PRIVATE KEY-----\n",
  "client_email": "deployment@your-project.iam.gserviceaccount.com",
  ...
}
```

---

#### 🔹 Step 6: Format the `[GOOGLE_CREDENTIALS]` Block

Create a block in your configuration file (`.toml`, `.env`, etc.) like this:

```
[GOOGLE_CREDENTIALS]
type = "service_account"
project_id = "your-project-id"
private_key_id = "your-private-key-id"
private_key = """ 
-----BEGIN PRIVATE KEY-----
...paste the full key here with newlines...
-----END PRIVATE KEY-----
"""
client_email = "deployment@your-project.iam.gserviceaccount.com"
client_id = "your-client-id"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/deployment@your-project.iam.gserviceaccount.com"
universe_domain = "googleapis.com"
```

> ⚠️ **Important**: Use triple quotes (`"""..."""`) for the private key to handle newlines properly.
