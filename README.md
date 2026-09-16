# Spotify AI Support Agent

An AI-powered customer-support assistant developed for the Hiver SDE Intern assignment.

The application processes Spotify customer-support messages, identifies the customer’s issue, generates an appropriate response using Google Gemini, and detects cases that may require escalation to a human support agent.

## Live Demo

**Streamlit App:**
https://hiver-support-agent-cvquauosx3eb3mmrqewath.streamlit.app/

## GitHub Repository

https://github.com/ishika74/hiver-support-agent

## Problem Statement

Customer-support teams receive a large number of repetitive questions and complaints. Manually classifying every issue and preparing a response can be time-consuming.

This project demonstrates an AI-assisted support workflow that helps automate the initial stages of customer support:

1. Understand the customer’s message.
2. Classify the issue.
3. Retrieve relevant information from previous support conversations.
4. Generate a response.
5. Identify whether human escalation may be required.

## Features

* Interactive Streamlit user interface
* Spotify customer-support issue classification
* AI-generated support responses
* Dataset-based retrieval
* Escalation detection
* Support-ticket assistance
* Conversation-style interaction
* Customer feedback controls
* Evaluation scripts for testing the system
* Google Gemini API integration

## Dataset

The project uses a customer-support conversation dataset containing Twitter-based customer messages and conversation relationships.

The dataset includes fields such as:

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

The `text` column contains the customer-support messages. The response and conversation ID columns provide information about relationships between customer messages and replies.

## System Workflow

```text
Customer Message
       |
       v
Issue Classification
       |
       v
Relevant Data Retrieval
       |
       v
Escalation Detection
       |
       v
AI Response Generation
       |
       v
Support Response
```

## Project Structure

```text
hiver-support-agent/
│
├── app/
│
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

## Main Components

### `app.py`

Provides the Streamlit user interface and allows users to enter customer-support questions and view generated responses.

### `llm_client.py`

Handles communication with the Google Gemini API.

### `classifier.py`

Classifies customer messages into support-related issue categories.

### `retrieval.py`

Retrieves relevant information from the available support dataset.

### `reply_generator.py`

Generates customer-support replies using the retrieved information and AI model.

### `escalation.py`

Identifies issues that may require human support-agent involvement.

### `pipeline.py`

Connects the main processing stages into a single workflow.

### `ingest.py`

Handles dataset preparation and ingestion.

### `run_eval.py`

Runs evaluation procedures for the support-agent system.

### `llm_judge.py`

Supports evaluation of generated responses using an AI-based judging process.

## Local Installation

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

For Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

For macOS or Linux:

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

Never upload the `.env` file or expose the API key publicly.

### 6. Run the application

```bash
python -m streamlit run src/app.py
```

The application will open in the browser.

## Streamlit Cloud Deployment

1. Open Streamlit Community Cloud.
2. Connect your GitHub account.
3. Select the repository:

```text
ishika74/hiver-support-agent
```

4. Select the `main` branch.
5. Set the main file path to:

```text
src/app.py
```

6. Add the Gemini API key in Streamlit Cloud Secrets:

```toml
GOOGLE_API_KEY = "your_gemini_api_key"
```

7. Deploy the application.

## Evaluation

The repository includes evaluation-related scripts and folders.

These can be used to assess:

* Issue classification
* Response generation
* Escalation behavior
* Overall support-agent performance

The evaluation scripts may require additional Gemini API requests and can be affected by API quota limits.

## Limitations

* The system’s performance depends on the quality and coverage of the dataset.
* The dataset may not contain examples for every possible customer issue.
* AI-generated responses may require human review.
* Gemini API requests may be limited by free-tier quotas.
* Escalation detection is an assistance feature and does not replace human judgment.
* The application is a prototype and is not connected to Spotify’s internal customer-support systems.

## Future Improvements

* Add a larger support knowledge base.
* Improve classification using a trained machine-learning model.
* Add persistent conversation memory.
* Add authentication and user management.
* Add analytics and monitoring.
* Add human-agent handoff functionality.
* Add persistent support-ticket storage.
* Improve evaluation with larger test sets.
* Add automated feedback-based model improvement.

## Security

API keys must be stored using environment variables locally and Streamlit Secrets during deployment.

The following files should never be committed:

```text
.env
venv/
__pycache__/
```

## Author

Ishika Razdan
