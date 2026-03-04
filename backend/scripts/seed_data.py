#!/usr/bin/env python3
"""
Seed data for CRM Agent:
- 500 synthetic support tickets
- 200 NPS responses
- Amazon reviews from HuggingFace (Cell Phones) or synthetic
- Crisis scenario: 50 tickets + 30 reviews about "checkout failed on iOS v2.3.1" in last 6h
- Embed all into ChromaDB
"""
import json
import os
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Add backend root to path and load .env from project root
_backend_dir = Path(__file__).resolve().parent.parent
_project_root = _backend_dir.parent
sys.path.insert(0, str(_backend_dir))
os.chdir(_backend_dir)
# Load .env from project root so OPENAI_API_KEY is available
env_file = _project_root / ".env"
if env_file.exists():
    from dotenv import load_dotenv
    load_dotenv(env_file)

from app.config import get_settings, ensure_dirs
from app.db.data_store import save_tickets, save_nps, save_reviews, save_metrics
from app.db.chroma import get_chroma_client, COLLECTION_NAME

# Categories and themes for synthetic data
TICKET_CATEGORIES = ["Billing", "Checkout", "Shipping", "Account", "iOS App", "Android App", "Website", "Other"]
REGIONS = ["West Coast", "East Coast", "Midwest", "South", "International"]
PRIORITIES = ["P0", "P1", "P2"]

def random_ts(days_back: int, hours_back: int = 0):
    delta = timedelta(days=random.randint(0, days_back), hours=random.randint(0, 24), minutes=random.randint(0, 59))
    if hours_back:
        delta = timedelta(hours=random.randint(0, hours_back), minutes=random.randint(0, 59))
    return (datetime.now(timezone.utc) - delta).strftime("%Y-%m-%dT%H:%M:%SZ")


def gen_tickets(count: int, crisis: bool = False, start_id: int = 1000) -> list[dict]:
    tickets = []
    for i in range(count):
        if crisis:
            category = "Checkout"
            subject = "Checkout failed on iOS v2.3.1"
            body = "Checkout fails when I try to pay on the iOS app version 2.3.1. Error says payment could not be processed."
            region = random.choice(["West Coast", "West Coast", "East Coast"])  # bias West
            priority = "P0" if i % 2 == 0 else "P1"
            created = random_ts(days_back=0, hours_back=6)
        else:
            category = random.choice(TICKET_CATEGORIES)
            subjects = [
                "Password reset not working", "Order delayed", "Refund request",
                "App crashes on launch", "Wrong item shipped", "Duplicate charge",
                "Login issue", "Subscription cancel", "Feature request",
            ]
            subject = random.choice(subjects)
            body = f"Customer reported: {subject}. Ticket #{1000 + i}."
            region = random.choice(REGIONS)
            priority = random.choice(PRIORITIES)
            created = random_ts(days_back=30)
        tickets.append({
            "id": f"TKT-{start_id + len(tickets)}",
            "subject": subject,
            "body": body,
            "category": category,
            "status": random.choice(["open", "open", "pending", "new", "closed"]) if not crisis else "open",
            "priority": priority,
            "region": region,
            "created_at": created,
            "escalated": priority == "P0" or (crisis and i < 10),
            "metadata": {"version": "iOS v2.3.1"} if crisis else {},
        })
    return tickets


def gen_nps(count: int) -> list[dict]:
    nps_list = []
    for i in range(count):
        score = random.choices([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10], weights=[1, 1, 2, 2, 3, 5, 5, 8, 10, 12, 15])[0]
        feedback = "" if random.random() > 0.4 else random.choice([
            "Great app!", "Slow checkout.", "Love the support.", "Had an issue with payment.",
            "Checkout failed on my phone.", "Everything works well.",
        ])
        nps_list.append({
            "id": f"NPS-{2000 + i}",
            "score": score,
            "feedback": feedback,
            "date": random_ts(days_back=30),
            "region": random.choice(REGIONS),
        })
    return nps_list


def gen_synthetic_reviews(count: int, crisis: bool = False, start_id: int = 3000) -> list[dict]:
    reviews = []
    for i in range(count):
        if crisis:
            text = "Checkout failed on iOS v2.3.1. Very frustrating. Could not complete purchase."
            sentiment = 0.2
            product_name = "iOS App"
            date = random_ts(days_back=0, hours_back=6)
        else:
            text = random.choice([
                "Good product, fast shipping.", "App is slow sometimes.", "Great customer service.",
                "Had a billing issue but resolved.", "Works as expected.", "UI could be better.",
            ])
            sentiment = random.uniform(0.3, 0.95)
            product_name = random.choice(["iOS App", "Android App", "Website", "Subscription"])
            date = random_ts(days_back=90)
        reviews.append({
            "id": f"REV-{start_id + i}",
            "text": text,
            "sentiment": round(sentiment, 2),
            "product_name": product_name,
            "product_id": f"prod-{random.randint(1, 20)}",
            "date": date,
            "region": random.choice(REGIONS),
        })
    return reviews


def load_amazon_reviews(max_reviews: int = 500) -> list[dict]:
    try:
        from datasets import load_dataset
        for config in ["raw_review_Cell_Phones_and_Accessories", "raw_review_Cell_Phones", "raw_review_Electronics", "raw_review_All_Beauty"]:
            try:
                ds = load_dataset("McAuley-Lab/Amazon-Reviews-2023", config, split="train")
                n = min(max_reviews, len(ds))
                out = []
                for i in range(n):
                    row = ds[i]
                    if isinstance(row, dict):
                        text = row.get("review_body") or row.get("content") or str(row)[:500]
                        rating = int(row.get("star_rating", row.get("rating", 5)))
                        if isinstance(rating, str):
                            rating = int(rating) if rating.isdigit() else 5
                    else:
                        text = str(row)[:500]
                        rating = 5
                    out.append({
                        "id": f"AMZ-{4000 + len(out)}",
                        "text": str(text)[:500],
                        "sentiment": min(1.0, max(0.0, rating / 5.0)),
                        "product_name": "Cell Phones",
                        "product_id": "amazon-cell",
                        "date": random_ts(days_back=365),
                        "region": random.choice(REGIONS),
                    })
                if out:
                    return out
            except Exception:
                continue
        return []
    except Exception as e:
        print(f"Amazon dataset load failed: {e}, using synthetic reviews only.")
        return []


def embed_and_store(documents: list[dict]):
    """Add documents to Chroma with embeddings. Each doc has text + metadata."""
    from app.db.chroma import get_chroma_client, get_embeddings, COLLECTION_NAME
    from langchain_chroma import Chroma
    settings = get_settings()
    if not settings.openai_api_key:
        print("OPENAI_API_KEY not set; skipping ChromaDB embedding.")
        return
    client = get_chroma_client()
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    embeddings = get_embeddings()
    texts = []
    metadatas = []
    ids = []
    for i, d in enumerate(documents):
        text = d.get("text") or (d.get("subject", "") + " " + (d.get("body") or ""))
        if not (text and str(text).strip()):
            continue
        meta = {k: str(v) for k, v in d.items() if k not in ("text", "body") and v is not None}
        texts.append(str(text)[:2000])
        metadatas.append(meta)
        ids.append(str(d.get("id", "")) or f"doc-{i}")
    vectorstore = Chroma(
        client=client,
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
    )
    vectorstore.add_texts(texts=texts, metadatas=metadatas, ids=ids)
    print(f"Embedded {len(texts)} documents into ChromaDB.")


def main():
    ensure_dirs(get_settings())
    # 1) Synthetic tickets (450 normal + 50 crisis)
    tickets = gen_tickets(450, crisis=False, start_id=1000) + gen_tickets(50, crisis=True, start_id=1450)
    save_tickets(tickets)
    print(f"Saved {len(tickets)} tickets.")

    # 2) NPS
    nps = gen_nps(200)
    save_nps(nps)
    print(f"Saved {len(nps)} NPS responses.")

    # 3) Reviews: try Amazon, then synthetic; add 30 crisis reviews
    reviews = load_amazon_reviews(470)
    if len(reviews) < 400:
        reviews = gen_synthetic_reviews(470, crisis=False)
    reviews += gen_synthetic_reviews(30, crisis=True, start_id=3470)
    save_reviews(reviews)
    print(f"Saved {len(reviews)} reviews.")

    # 4) Metrics
    save_metrics({
        "cx_health_score": 85.0,
        "churn_risk": 25.0,
        "nps_score": 42.0,
        "open_issues_count": sum(1 for t in tickets if t.get("status") in ("open", "pending", "new")),
    })
    print("Saved default metrics.")

    # 5) ChromaDB: embed tickets + reviews (with metadata)
    all_docs = []
    for t in tickets:
        all_docs.append({
            "id": t.get("id"),
            "text": (t.get("subject") or "") + " " + (t.get("body") or ""),
            "date": t.get("created_at"),
            "category": t.get("category"),
            "priority": t.get("priority"),
            "region": t.get("region"),
            "sentiment": 0.5,
        })
    for r in reviews:
        all_docs.append({
            "id": r.get("id"),
            "text": r.get("text", ""),
            "date": r.get("date"),
            "product_name": r.get("product_name"),
            "region": r.get("region"),
            "sentiment": r.get("sentiment", 0.5),
        })
    try:
        embed_and_store(all_docs)
    except Exception as e:
        print(f"ChromaDB embed failed: {e}. Run with OPENAI_API_KEY set to embed.")
    print("Seed complete. Crisis scenario: 50 tickets + 30 reviews about 'checkout failed on iOS v2.3.1' in last 6h.")


if __name__ == "__main__":
    main()
