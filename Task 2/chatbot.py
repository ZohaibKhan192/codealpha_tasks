"""
chatbot.py
----------
Core NLP module for the FAQ chatbot.

Provides:
  - FAQ loading from JSON
  - Text preprocessing (tokenization, stopword removal, lemmatization)
  - TF-IDF + cosine similarity based question matching
  - Topic hint extraction
"""

import json
import os
import string

import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# ---------------------------------------------------------------------------
# NLTK resource bootstrap
# ---------------------------------------------------------------------------

def _download_nltk_resources() -> None:
    """Download required NLTK corpora/models if they are not yet present."""
    resources = [
        ("tokenizers/punkt",        "punkt"),
        ("tokenizers/punkt_tab",    "punkt_tab"),
        ("corpora/stopwords",       "stopwords"),
        ("corpora/wordnet",         "wordnet"),
        ("corpora/omw-1.4",         "omw-1.4"),
    ]
    for path, pkg in resources:
        try:
            nltk.data.find(path)
        except LookupError:
            nltk.download(pkg, quiet=True)


_download_nltk_resources()

# Singletons – initialise once at module load time
_lemmatizer  = WordNetLemmatizer()
_stop_words  = set(stopwords.words("english"))
_punctuation = set(string.punctuation)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def load_faqs(filepath: str = "faqs.json") -> list[dict]:
    """
    Load FAQ data from a JSON file.

    Parameters
    ----------
    filepath : str
        Path to the JSON file containing FAQ data.
        Expected structure::

            {
                "questions": [
                    {"question": "...", "answer": "..."},
                    ...
                ]
            }

    Returns
    -------
    list[dict]
        A list of dicts, each with keys ``"question"`` and ``"answer"``.

    Raises
    ------
    FileNotFoundError
        Re-raised with a user-friendly message when the file is missing.
    ValueError
        When the JSON structure is unexpected.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(
            f"[chatbot] FAQ file not found: '{filepath}'\n"
            "Please place your faqs.json file in the same directory as this script."
        )

    with open(filepath, "r", encoding="utf-8") as fh:
        data = json.load(fh)

    if "questions" not in data or not isinstance(data["questions"], list):
        raise ValueError(
            "[chatbot] Unexpected JSON structure. "
            "Expected a top-level 'questions' key containing a list of FAQ objects."
        )

    faqs = data["questions"]
    validated = []
    for idx, item in enumerate(faqs):
        if not isinstance(item, dict) or "question" not in item or "answer" not in item:
            raise ValueError(
                f"[chatbot] FAQ entry at index {idx} is malformed. "
                "Each entry must have 'question' and 'answer' keys."
            )
        validated.append({"question": str(item["question"]), "answer": str(item["answer"])})

    return validated


def preprocess(text: str) -> str:
    """
    Clean and normalise a piece of text for TF-IDF vectorisation.

    Steps
    -----
    1. Lowercase
    2. Tokenise with NLTK ``word_tokenize``
    3. Remove stopwords (English)
    4. Remove punctuation and non-alphabetic tokens
    5. Lemmatise with ``WordNetLemmatizer``

    Parameters
    ----------
    text : str
        Raw input text.

    Returns
    -------
    str
        A single whitespace-separated string of cleaned tokens.
    """
    text   = text.lower()
    tokens = word_tokenize(text)

    cleaned = []
    for token in tokens:
        # Keep only alphabetic tokens that are not stopwords or punctuation
        if (
            token.isalpha()
            and token not in _stop_words
            and token not in _punctuation
        ):
            cleaned.append(_lemmatizer.lemmatize(token))

    return " ".join(cleaned)


def get_best_match(
    user_input: str,
    faqs: list[dict],
    threshold: float = 0.15,
) -> dict:
    """
    Find the FAQ whose question best matches the user's input.

    Strategy
    --------
    * Preprocesses the user input and all FAQ questions.
    * Builds a TF-IDF matrix over the combined corpus.
    * Computes cosine similarity between the user-input vector and each
      FAQ-question vector.
    * Returns the FAQ with the highest similarity if it meets *threshold*.

    Parameters
    ----------
    user_input : str
        Raw text typed by the user.
    faqs : list[dict]
        FAQ list returned by :func:`load_faqs`.
    threshold : float, optional
        Minimum cosine-similarity score required to return a match.
        Defaults to ``0.15``.

    Returns
    -------
    dict
        ``{"answer": str, "score": float, "matched_question": str | None}``

    Notes
    -----
    ``score`` is ``0.0`` and ``matched_question`` is ``None`` when no match
    meets the threshold.
    """
    _FALLBACK = {
        "answer": (
            "I'm sorry, I couldn't find a relevant answer. "
            "Please try rephrasing your question or contact our customer support team."
        ),
        "score": 0.0,
        "matched_question": None,
    }

    processed_input = preprocess(user_input)
    if not processed_input.strip():
        return _FALLBACK

    processed_questions = [preprocess(faq["question"]) for faq in faqs]

    # Combine: first element = user query, rest = FAQ questions
    corpus = [processed_input] + processed_questions

    try:
        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform(corpus)
    except ValueError:
        # Raised if all tokens are stop-words after preprocessing
        return _FALLBACK

    # User vector vs. all FAQ vectors
    user_vector  = tfidf_matrix[0]
    faq_vectors  = tfidf_matrix[1:]
    similarities = cosine_similarity(user_vector, faq_vectors).flatten()

    best_idx   = int(similarities.argmax())
    best_score = float(similarities[best_idx])

    if best_score < threshold:
        return _FALLBACK

    return {
        "answer":           faqs[best_idx]["answer"],
        "score":            best_score,
        "matched_question": faqs[best_idx]["question"],
    }


def get_topic_hints(faqs: list[dict]) -> list[str]:
    """
    Infer unique topic categories from the FAQ question list.

    The function scans each FAQ question for keywords associated with
    predefined e-commerce support categories and returns the set of
    categories that are represented in the dataset.

    Parameters
    ----------
    faqs : list[dict]
        FAQ list returned by :func:`load_faqs`.

    Returns
    -------
    list[str]
        Sorted list of unique category names found in the FAQ dataset.
    """
    category_keywords: dict[str, list[str]] = {
        "Account & Registration":   ["account", "sign up", "register", "login", "password", "profile"],
        "Payments":                  ["payment", "pay", "credit card", "debit", "paypal", "billing", "invoice"],
        "Order Tracking":            ["track", "tracking", "order status", "shipment status"],
        "Shipping":                  ["ship", "shipping", "delivery", "expedited", "international", "address"],
        "Returns & Refunds":         ["return", "refund", "exchange", "receipt", "damaged", "wrong item"],
        "Cancellations":             ["cancel", "cancellation"],
        "Product Availability":      ["out of stock", "backordered", "pre-order", "coming soon", "sold out",
                                      "discontinued", "limited edition", "temporarily unavailable", "on hold",
                                      "restocked", "available"],
        "Promo Codes & Discounts":   ["promo", "discount", "coupon", "code", "sale", "price match",
                                      "price adjustment", "wholesale", "bulk"],
        "Gifts & Special Orders":    ["gift", "wrap", "message", "personalized", "custom"],
        "Customer Support":          ["contact", "support", "chat", "phone", "email", "help", "assistance"],
    }

    found_categories: set[str] = set()

    for faq in faqs:
        question_lower = faq["question"].lower()
        for category, keywords in category_keywords.items():
            if any(kw in question_lower for kw in keywords):
                found_categories.add(category)

    return sorted(found_categories)


# ---------------------------------------------------------------------------
# Standalone test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 65)
    print("  FAQ Chatbot – chatbot.py standalone test")
    print("=" * 65)

    try:
        faqs = load_faqs("faqs.json")
    except FileNotFoundError as exc:
        print(exc)
        raise SystemExit(1)

    print(f"\n✅  Loaded {len(faqs)} FAQs from faqs.json\n")

    test_queries = [
        "How do I create an account?",
        "What shipping options are available?",
        "I want to return something I bought",
        "My discount code is not working",
        "Can I pay with PayPal?",
    ]

    print(f"{'QUERY':<45} {'SCORE':>6}  MATCHED QUESTION")
    print("-" * 110)

    for query in test_queries:
        result = get_best_match(query, faqs)
        score  = f"{result['score']:.2%}"
        matched = result["matched_question"] or "— no match —"
        print(f"{query:<45} {score:>6}  {matched}")

    print("\n" + "=" * 65)
    print("  Topic hints detected:")
    for hint in get_topic_hints(faqs):
        print(f"  • {hint}")
    print("=" * 65)
