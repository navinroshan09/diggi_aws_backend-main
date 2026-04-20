# credibility.py

from typing import List

# -------------------------------
# 1. SOURCE RELIABILITY SCORES
# -------------------------------
SOURCE_SCORES = {
    "reuters.com": 0.95,
    "bbc.com": 0.93,
    "theguardian.com": 0.92,
    "apnews.com": 0.91,
    "thehindu.com": 0.90,
    "indianexpress.com": 0.88,
    "ndtv.com": 0.85,
    "cnn.com": 0.85,
    "aljazeera.com": 0.87,
    "cnbc.com": 0.84,
    "foxnews.com": 0.75,
}


def get_source_score(url: str) -> float:
    """Returns reliability score based on domain."""
    for domain, score in SOURCE_SCORES.items():
        if domain in url:
            return score
    return 0.5  # default if unknown source


# -------------------------------
# 2. EVIDENCE SCORE
# -------------------------------
def get_evidence_score(text: str) -> float:
    """Checks presence of evidence indicators in text."""
    score = 0

    # quotes
    if '"' in text:
        score += 1

    # numbers/statistics
    if any(char.isdigit() for char in text):
        score += 1

    # reporting phrases
    if "according to" in text.lower():
        score += 1

    return score / 3  # normalize to 0–1


# -------------------------------
# 3. AGREEMENT SCORE
# -------------------------------
def get_agreement_score(claims: List[str], articles: List[dict]) -> float:
    """Measures how many claims appear across multiple articles."""
    if not claims or not articles:
        return 0.0

    match_count = 0
    total_possible = len(claims) * len(articles)

    for claim in claims:
        for article in articles:
            if claim.lower() in article["content"].lower():
                match_count += 1

    return min(match_count / total_possible, 1.0)


# -------------------------------
# 4. FINAL CREDIBILITY SCORE
# -------------------------------
def compute_credibility(article: dict, all_articles: List[dict], claims: List[str]) -> float:
    """Combines all scores into final credibility score."""
    source_score = get_source_score(article["link"])
    evidence_score = get_evidence_score(article["content"])
    agreement_score = get_agreement_score(claims, all_articles)

    final_score = (
        0.4 * source_score +
        0.3 * agreement_score +
        0.3 * evidence_score
    )

    return round(final_score, 3)


# -------------------------------
# 5. LABEL GENERATION
# -------------------------------
def get_confidence_label(score: float) -> str:
    """Converts score into human-readable label."""
    if score >= 0.8:
        return "High"
    elif score >= 0.6:
        return "Medium"
    else:
        return "Low"