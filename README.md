# Spotify AI Support Agent

An AI-powered customer-support agent built for the Hiver SDE Intern assignment. The application analyzes customer-support conversations, identifies the customer’s issue, generates a suitable response, and detects cases that may require escalation.

## Project Overview

Customer-support teams receive a large number of repetitive questions and complaints. This project uses an AI-assisted workflow to help support agents respond more quickly and consistently.

The system processes customer messages and supports the following workflow:

1. Receive a customer-support message.
2. Classify the customer’s issue.
3. Retrieve relevant information from the available dataset.
4. Generate an AI-assisted response.
5. Detect whether the issue may require escalation.
6. Display the response and support information through a Streamlit interface.

## Features

* Interactive Streamlit web application
* Customer-issue classification
* AI-generated support responses
* Support for common Spotify-related issues
* Escalation detection
* Support-ticket assistance
* Conversation-style interaction
* Feedback controls
* Dataset-based support analysis
* Evaluation scripts for testing response quality

## Dataset

The project uses a customer-support conversation dataset containing fields such as:

* `tweet_id`
* `author_id`
* `inbound`
* `created_at`
* `text`
* `response_tweet_id`
* `in_response_to_tweet_id`

The dataset is stored in:

```text
data/sample(1).csv
```

The `text` field contains the customer-support messages. The response and conversation ID fields help represent relationships between customer messages and support replies.

## Project Structure

```text
hiver-support-agent/
│
├── app/
├── data/
│   └── sample(1).csv
│
├── eval/
│
├── src/
│   ├── app.py
│   ├── classifier.py
│   ├── escalation.py
│   ├── ingest.py
│   ├── intents.py
│   ├── llm_client.py
│   ├── llm_judge.py
│   ├── pipeline.py
│   ├── reply_generator.py
│   ├── retrieval.py
│   └── run_eval.py
│
├── requirements.txt
├── README.md
└── .gitignore
```

## Technologies Used

* Python
* Streamlit
* Google Gemini API
* Pandas
* NumPy
* Scikit-learn
* Python-dotenv

## AI Model

The application uses the Google Gemini API to generate support responses.

The model name is configured in:

```text
src/llm_client.py
```

The API key is loaded through an environment variable or Streamlit Secrets.

## Local Setup

### 1. Clone the repository

```bash
git clone https://github.com/ishika74/hiver-support-agent.git
cd hiver-support-agent
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

### 3. Activate the virtual environment

On Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

On macOS or Linux:

```bash
source venv/bin/activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure the Gemini API key

Create a `.env` file in the project root:

```env
GOOGLE_API_KEY=your_gemini_api_key
```

Do not commit or upload the `.env` file to GitHub.

### 6. Run the application

```bash
python -m streamlit run src/app.py
```

The application will open in your browser.

## Streamlit Cloud Deployment

1. Push the project to GitHub.
2. Open Streamlit Community Cloud.
3. Select the repository:

```text
ishika74/hiver-support-agent
```

4. Select the `main` branch.
5. Set the main file path to:

```text
src/app.py
```

6. Add the Gemini API key under Streamlit Cloud Secrets:

```toml
GOOGLE_API_KEY = "your_gemini_api_key"
```

7. Deploy the application.

## Evaluation

The repository includes evaluation-related files for testing the system:

* `src/run_eval.py`
* `src/llm_judge.py`
* `eval/`

The evaluation process can be used to inspect classification quality, response quality, and escalation behavior.

## Limitations

* The quality of generated responses depends on the available dataset and AI model.
* Gemini API usage may be limited by free-tier quotas.
* The dataset may not cover every possible customer-support issue.
* AI-generated responses should be reviewed before being used in real customer interactions.
* Escalation detection is an assistance feature and does not replace human judgment.

## Future Improvements

* Add a larger and more diverse knowledge base.
* Improve intent classification using a trained machine-learning model.
* Add conversation-memory support.
* Add authentication and user management.
* Add analytics dashboards.
* Add human-agent handoff functionality.
* Add automated evaluation reports.
* Add persistent ticket storage.

## Author

Ishika Razdan

## Repository

https://github.com/ishika74/hiver-support-agent
