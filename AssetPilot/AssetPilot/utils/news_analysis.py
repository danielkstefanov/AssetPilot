from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

tokenizer = AutoTokenizer.from_pretrained("ProsusAI/finbert")
model = AutoModelForSequenceClassification.from_pretrained("ProsusAI/finbert")


def analyze_sentiment(headline: str, content: str) -> dict:
    text = f"{headline} {content}"
    inputs = tokenizer(text, return_tensors="pt", truncation=True)

    with torch.no_grad():
        scores = torch.nn.functional.softmax(model(**inputs).logits, dim=-1)[0]

    sentiment_score = float((-scores[0] + scores[2]) * 100)
    return {"is_positive": sentiment_score > 0, "sentiment_score": sentiment_score}
