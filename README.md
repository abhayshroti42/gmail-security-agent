

\# 🛡️ AI Gmail Security Agent



An AI-powered background email security agent that monitors Gmail, analyzes incoming emails using machine learning and security signals, and delivers real-time Windows notifications with a detailed browser-based security report.



\## 🚀 Overview



The AI Gmail Security Agent works continuously in the background without requiring Gmail to remain open.



When a new email arrives, the system:



1\. Reads the email securely through the Gmail API.

2\. Classifies it using a TF-IDF + Multinomial Naive Bayes spam classifier.

3\. Performs deterministic security analysis.

4\. Uses LangChain and LangGraph to orchestrate additional analysis.

5\. Uses Gemini for AI-assisted assessment when available.

6\. Produces a final security classification.

7\. Sends a Windows desktop notification.

8\. Generates a detailed Email Security Report in the browser.



\### Classification



\- 🔴 \*\*SPAM\*\* — suspicious or spam indicators detected

\- 🟢 \*\*SAFE\*\* — classified as legitimate with low security risk

\- 🟡 \*\*SUSPICIOUS\*\* — security signals require additional attention



\---



\## 🏗️ System Architecture



```text

&#x20;                        ┌─────────────────┐

&#x20;                        │      Gmail      │

&#x20;                        └────────┬────────┘

&#x20;                                 │

&#x20;                                 ▼

&#x20;                        ┌─────────────────┐

&#x20;                        │   Gmail API     │

&#x20;                        └────────┬────────┘

&#x20;                                 │

&#x20;                                 ▼

&#x20;                        ┌─────────────────┐

&#x20;                        │ Background      │

&#x20;                        │ Gmail Monitor   │

&#x20;                        └────────┬────────┘

&#x20;                                 │

&#x20;                   ┌─────────────┴─────────────┐

&#x20;                   ▼                           ▼

&#x20;         ┌──────────────────┐       ┌────────────────────┐

&#x20;         │ ML Spam          │       │ Security Analyzer  │

&#x20;         │ Classifier       │       │                    │

&#x20;         │                  │       │ • Sender/domain    │

&#x20;         │ TF-IDF           │       │ • Keywords         │

&#x20;         │ +                │       │ • Urgency          │

&#x20;         │ Multinomial NB   │       │ • Links            │

&#x20;         └────────┬─────────┘       │ • Suspicious URLs  │

&#x20;                  │                 └─────────┬──────────┘

&#x20;                  └────────────┬─────────────┘

&#x20;                               ▼

&#x20;                      ┌─────────────────┐

&#x20;                      │   LangGraph     │

&#x20;                      │     Agent       │

&#x20;                      └────────┬────────┘

&#x20;                               │

&#x20;                    ┌──────────┴──────────┐

&#x20;                    ▼                     ▼

&#x20;             ┌─────────────┐      ┌─────────────┐

&#x20;             │ LangChain   │      │   Gemini    │

&#x20;             │   Tools     │      │ AI Analysis │

&#x20;             └─────────────┘      └─────────────┘

&#x20;                    │                     │

&#x20;                    └──────────┬──────────┘

&#x20;                               ▼

&#x20;                      ┌─────────────────┐

&#x20;                      │ Security        │

&#x20;                      │ Decision        │

&#x20;                      └────────┬────────┘

&#x20;                               │

&#x20;                 ┌─────────────┴─────────────┐

&#x20;                 ▼                           ▼

&#x20;        ┌─────────────────┐        ┌──────────────────┐

&#x20;        │ Windows         │        │ HTML Security    │

&#x20;        │ Notification    │───────►│ Report           │

&#x20;        └─────────────────┘        └──────────────────┘

````



\---



\## ✨ Features



\### 📧 Gmail Monitoring



\* Gmail API integration

\* Background email monitoring

\* Detection of unread emails

\* Multipart email body extraction

\* Base64URL decoding

\* Duplicate prevention during monitoring

\* Read-only Gmail access

\* No automatic deletion or modification of Gmail messages



\### 🤖 Machine Learning Spam Classification



The system uses a traditional NLP pipeline:



```text

Email Subject + Body

&#x20;       ↓

Text Preprocessing

&#x20;       ↓

TF-IDF Vectorization

&#x20;       ↓

Multinomial Naive Bayes

&#x20;       ↓

SPAM / NOT SPAM

&#x20;       ↓

Confidence Score

```



The trained model and TF-IDF vectorizer are stored in:



```text

models/

├── model.pkl

└── vectorizer.pkl

```



\### 🔍 Deterministic Security Analysis



The ML classifier is combined with an independent security-analysis layer.



The analyzer examines:



\* Sender and domain information

\* Suspicious keywords

\* Urgency language

\* URLs and links

\* Suspicious links

\* Security risk level



This provides additional security signals instead of relying entirely on the ML prediction.



\### 🧠 LangChain + LangGraph Agent



LangChain is used for LLM integration and tool-based analysis.



LangGraph orchestrates the agent workflow:



```text

Prepare Email

&#x20;    ↓

Initial Analysis

&#x20;    ↓

LLM Analysis

&#x20;    ↓

Tool Calls (when required)

&#x20;    ↓

Additional Analysis

&#x20;    ↓

Final Decision

```



Available analysis tools include:



\* Sender/domain analysis

\* Link extraction

\* Suspicious-link analysis

\* Complete email security analysis



\### ✨ Gemini AI Assessment



Gemini provides an additional AI-assisted assessment based on the ML and deterministic security signals.



The system is designed so that local ML and deterministic security analysis remain available even when Gemini is temporarily unavailable.



\### 🖥️ Windows Desktop Notifications



The agent runs in the background and generates a Windows notification when an email is analyzed.



```text

New Email

&#x20;  ↓

Background Detection

&#x20;  ↓

Security Analysis

&#x20;  ↓

Windows Notification

&#x20;  ↓

Click Notification

&#x20;  ↓

Detailed Security Report

```



\### 📊 Email Security Report



Clicking the notification opens a browser-based security report containing:



\* Final classification

\* Risk level

\* ML prediction

\* ML confidence

\* Sender

\* Domain

\* Subject

\* Date/time

\* Threat signals

\* Suspicious links

\* AI-assisted assessment

\* Email preview



\---



\## 🛠️ Tech Stack



| Technology              | Purpose                    |

| ----------------------- | -------------------------- |

| Python                  | Core application           |

| Gmail API               | Email access               |

| Scikit-learn            | Machine learning           |

| TF-IDF                  | Text feature extraction    |

| Multinomial Naive Bayes | Spam classification        |

| LangChain               | LLM integration and tools  |

| LangGraph               | Agent orchestration        |

| Gemini                  | AI-assisted email analysis |

| HTML/CSS                | Security reports           |

| Windows Notifications   | Desktop alerts             |

| Git/GitHub              | Version control            |



\---



\## 📁 Project Structure



```text

gmail-security-agent/

│

├── models/

│   ├── model.pkl

│   └── vectorizer.pkl

│

├── src/

│   ├── gmail\_auth.py

│   ├── gmail\_reader.py

│   ├── gmail\_monitor.py

│   │

│   ├── spam\_classifier.py

│   ├── email\_analyzer.py

│   ├── email\_tools.py

│   │

│   ├── llm\_analyzer.py

│   ├── email\_agent.py

│   │

│   ├── report\_generator.py

│   ├── windows\_notifier.py

│   │

│   └── test\_\*.py

│

├── .gitignore

├── requirements.txt

├── run\_monitor.bat

└── README.md

```



\---



\## 🔐 Security \& Privacy



This project uses Gmail OAuth authentication and Gemini API access.



Sensitive files are intentionally excluded from Git:



```text

.env

credentials.json

token.json

logs/

reports/

```



\### Gemini API configuration



Create a local `.env` file:



```env

GOOGLE\_API\_KEY=your\_gemini\_api\_key

```



\### Gmail OAuth configuration



Place your Google OAuth desktop credentials in:



```text

credentials.json

```



After authentication, the Gmail OAuth token is stored locally as:



```text

token.json

```



\*\*Never commit API keys, OAuth credentials, tokens, passwords, or other secrets to GitHub.\*\*



\---



\## ⚙️ Installation



\### 1. Clone the repository



```bash

git clone https://github.com/abhayshroti42/gmail-security-agent.git

cd gmail-security-agent

```



\### 2. Install dependencies



```bash

pip install -r requirements.txt

```



\### 3. Configure Gmail API



Create a Google Cloud project, enable the Gmail API, configure OAuth credentials for a desktop application, and place:



```text

credentials.json

```



in the project root.



\### 4. Configure Gemini



Create a local `.env` file:



```env

GOOGLE\_API\_KEY=your\_api\_key

```



\### 5. Authenticate Gmail



Run:



```bash

python src/gmail\_auth.py

```



Follow the Google authentication process.



\### 6. Run a single monitoring cycle



```bash

python src/gmail\_monitor.py --once

```



\### 7. Run continuous monitoring



```bash

python src/gmail\_monitor.py

```



The monitor periodically checks Gmail for new unread emails and processes them in the background.



\---



\## 🧪 Testing



The project contains tests for the major components:



```text

test\_email\_agent.py

test\_email\_analyzer.py

test\_email\_tools.py

test\_gmail\_monitor.py

test\_llm\_analyzer.py

test\_windows\_notifier.py

```



Individual tests can be run with:



```bash

python src/test\_email\_analyzer.py

```



or:



```bash

python src/test\_email\_agent.py

```



\---



\## 🔄 Background Operation on Windows



The monitor can be configured to run automatically using Windows Task Scheduler.



The background process monitors Gmail without requiring Gmail to remain open.



The resulting workflow is:



```text

Gmail

&#x20; ↓

Background Agent

&#x20; ↓

ML + Security Analysis

&#x20; ↓

Windows Notification

&#x20; ↓

Browser Security Report

```



\---



\## ⚠️ Limitations



\* Gmail monitoring currently uses polling rather than Gmail push notifications.

\* Gemini analysis depends on API availability and quota.

\* The ML classifier depends on the training data used to build the saved model.

\* Security analysis provides indicators and risk assessment rather than guaranteeing that an email is safe.

\* The system does not automatically delete, move, or modify Gmail messages.

\* The current system is designed primarily as a desktop background prototype.



\---



\## 🔮 Future Improvements



Potential future improvements include:



\* Gmail push notifications instead of polling

\* Advanced phishing detection

\* URL reputation services

\* Attachment malware analysis

\* OCR-based analysis of image-based phishing emails

\* Transformer-based email classification

\* Historical security analytics

\* Local LLM support

\* Improved sender reputation analysis

\* Multi-account Gmail monitoring

\* Advanced threat-intelligence integration



\---



\## 🎯 Project Goal



The goal of this project is to combine \*\*machine learning, deterministic security analysis, and AI agents\*\* into a practical desktop email-security workflow.



Instead of relying on a single classifier, the system combines multiple sources of evidence before presenting the user with a security decision and actionable security report.



\---



\## 👨‍💻 Author



\*\*Abhay Shroti\*\*



Built as a practical AI/ML and agentic workflow project.



\---



\## 📌 Disclaimer



This project is intended for educational and research purposes.



Security classifications are automated assessments and should not be treated as guaranteed proof that an email is malicious or safe.



````

