# 🛒 E-Commerce FAQ Chatbot

A conversational FAQ assistant for e-commerce customer support, built with
Python, NLTK, scikit-learn, and Streamlit. Users can ask natural-language
questions and the chatbot surfaces the most relevant answer from a curated
FAQ dataset using TF-IDF vectorisation and cosine similarity matching.

---

## 📋 Prerequisites

| Requirement | Version |
|---|---|
| Python | 3.10 or newer |
| pip | latest recommended |

> **Windows users:** Make sure Python is on your `PATH`.

---

## 🚀 Installation

### 1. Clone / download the project

```
faq_chatbot/
├── faqs.json
├── chatbot.py
├── app.py
├── requirements.txt
└── README.md
```

### 2. (Optional) Create a virtual environment

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

> NLTK corpora (`punkt`, `stopwords`, `wordnet`) are downloaded automatically
> the first time you import `chatbot.py`.

---

## ▶️ Running the chatbot

```bash
streamlit run app.py
```

The browser will open at `http://localhost:8501` automatically.

---

## 🧪 Testing the NLP module independently

`chatbot.py` is fully self-contained and can be run without Streamlit:

```bash
python chatbot.py
```

This executes five test queries and prints the matched answers with confidence
scores to the terminal.

---

## 📁 Folder structure

```
faq_chatbot/
│
├── faqs.json          ← FAQ knowledge base (user-supplied)
├── chatbot.py         ← NLP engine (load, preprocess, match, topic hints)
├── app.py             ← Streamlit chat UI
├── requirements.txt   ← Pinned Python dependencies
└── README.md          ← This file
```

---

## ✏️ How to add new FAQs

Open `faqs.json` and append new objects to the `"questions"` array:

```json
{
  "questions": [
    { "question": "How can I create an account?", "answer": "To create an account…" },
    { "question": "Your new question here?",      "answer": "Your new answer here." }
  ]
}
```

**Rules:**
- Each entry must have both a `"question"` and an `"answer"` key.
- Restart the Streamlit app (or clear the cache with the top-right menu)
  after saving changes so the new FAQs are picked up.

---

## 🔍 How the matching works

1. **Preprocessing** — Both the user's input and every FAQ question are
   lowercased, tokenised, stripped of stopwords and punctuation, and
   lemmatised (reduced to base form, e.g. "shipping" → "ship").

2. **TF-IDF vectorisation** — The preprocessed user query and all FAQ
   questions are combined into a single corpus and converted into a TF-IDF
   matrix. TF-IDF rewards terms that appear frequently in a document but
   rarely across the whole corpus, giving them higher discriminative weight.

3. **Cosine similarity** — The angle between the user-query vector and each
   FAQ-question vector is computed. A score of `1.0` means a perfect match;
   `0.0` means no shared vocabulary.

4. **Threshold filtering** — Only matches with a cosine similarity ≥ `0.15`
   are returned. Below this threshold the chatbot replies with a polite
   fallback message.

---

## 📦 Dependencies

| Package | Version | Purpose |
|---|---|---|
| `streamlit` | 1.35.0 | Chat UI framework |
| `nltk` | 3.8.1 | Tokenisation, stopwords, lemmatisation |
| `scikit-learn` | 1.4.2 | TF-IDF vectoriser, cosine similarity |
| `numpy` | 1.26.4 | Numerical operations (required by scikit-learn) |

---

## 🛠️ Troubleshooting

| Problem | Solution |
|---|---|
| `FileNotFoundError: faqs.json` | Ensure `faqs.json` is in the **same folder** as `app.py` |
| NLTK `LookupError` | Run `python chatbot.py` once to trigger auto-download |
| Port already in use | Run `streamlit run app.py --server.port 8502` |
| Blank page on first load | Hard-refresh the browser (`Ctrl + Shift + R`) |

---

## 📄 License

This project is provided for educational and demonstration purposes.
