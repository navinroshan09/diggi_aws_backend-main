from urllib import response
from openai import OpenAI
import os
from enum import Enum
from pydantic import BaseModel, Field
import os
from dotenv import load_dotenv
from serpapi import GoogleSearch
import trafilatura
from typing import Optional, List
load_dotenv()
from typing import Union
from schemas import ArticleAnalysis

SERP_API_KEY = os.getenv("SERP_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

import json

def fetch_top_news(query, serp_api_key=SERP_API_KEY, num_results=6):
    """Fetches top news articles using SerpApi, ensuring unique sources."""
    print(f"Attempting to fetch news for query: '{query}'...")
    
    trusted_sites = (
        "site:bbc.com OR site:cnn.com OR site:reuters.com OR site:theguardian.com OR "
        "site:cnbc.com OR site:apnews.com OR site:aljazeera.com OR site:npr.org OR "
        "site:cbsnews.com OR site:abcnews.go.com OR site:nbcnews.com OR site:usatoday.com OR "
        "site:politico.com OR site:foxnews.com OR "
        "site:indianexpress.com OR site:thehindu.com OR site:hindustantimes.com OR "
        "site:timesofindia.indiatimes.com OR site:ndtv.com OR site:news18.com"
)
    refined_query = f"{query} ({trusted_sites})"

    params = {
        "engine": "google_news",
        "q": refined_query,
        "gl": "us",
        "hl": "en",
        "api_key": serp_api_key
    }

    def deduplicate_by_source(articles, limit):
        """Return up to `limit` articles with no repeated source names."""
        seen_sources = set()
        unique_articles = []
        for article in articles:
            source_name = article.get("source", {}).get("name", "").lower().strip()
            if source_name and source_name not in seen_sources:
                seen_sources.add(source_name)
                unique_articles.append(article)
            if len(unique_articles) >= limit:
                break
        return unique_articles
    
    try:
        search = GoogleSearch(params)
        results = search.get_dict()
        if "news_results" in results and results["news_results"]:
            unique = deduplicate_by_source(results["news_results"], num_results)
            print(f"SerpApi news fetch: successful (trusted sources, {len(unique)} unique)")
            return unique, None
        else:
            print("No results from trusted sources. Fetching from all sources...")
    except Exception as e:
        print(f"Trusted sources search failed: {e}")
    
    print("Fetching articles from all sources...")
    params["q"] = query
    
    try:
        search = GoogleSearch(params)
        results = search.get_dict()
        if "news_results" in results and results["news_results"]:
            unique = deduplicate_by_source(results["news_results"], num_results)
            print(f"SerpApi news fetch: successful (all sources, {len(unique)} unique)")
            return unique, None
        else:
            error_message = results.get("error", "No news_results found.")
            print(f"SerpApi news fetch: fail. Error: {error_message}")
            return [], error_message
    except Exception as e:
        print(f"SerpApi news fetch: fail. An exception occurred: {e}")
        return [], str(e)
    
def extract_article(url):
    """Extracts the main text content from a given URL."""
    print(f"Attempting to extract article from: {url}")
    try:
        downloaded = trafilatura.fetch_url(url)
        if not downloaded:
            print("Article download: fail. Could not retrieve content from URL.")
            return None
        
        text = trafilatura.extract(downloaded, include_comments=False)
        if text:
            print("Article text extraction: successful")
            return text
        else:
            print("Article text extraction: fail. Content was downloaded, but no main text could be extracted.")
            return None
    except Exception as e:
        print(f"Article text extraction: fail. An exception occurred: {e}")
        return None


def get_top_news_with_content(query, serp_api_key=SERP_API_KEY, num_results=6):
    """Fetches top news articles and extracts their content."""
    news_results, error = fetch_top_news(query, serp_api_key, num_results)
    
    if error:
        print(f"Error fetching news: {error}")
        return []
    articles = []
    for i, article in enumerate(news_results):
        title = article.get("title")
        link = article.get("link", "No link")
        source = article.get("source", {}).get("name", "Unknown source")
        thumbnail = article.get("thumbnail", "No thumbnail")
        date = article.get("date", "No date")

        print(f"\nProcessing article: '{title}' from {source}")
        
        content = extract_article(link)
        if content:
            articles.append({
                "id": i+1,
                "title": title,
                "link": link,
                "source": source,
                "thumbnail": thumbnail,
                "date": date,
                "content": content
            })
        else:
            print(f"Skipping article '{title}' due to extraction failure.")
    
    return articles

client = OpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1",
)

SYSTEM_PROMPT_A = """You are a news analysis assistant using the Diggi framework.

For each article, extract structured insights and present them in a clear readable format.

Output must be plain text (NOT JSON).

For each article use the following format:

ID: <article_id>
Title: <title>
Source: <source>
Link: <link>

CLAIM LEVEL FOCUS
- Claim: ...
  Actors: ...
  Evidence: ...

EVIDENCE TRACEABILITY
- Statement: ...
  Passage: ...

CREDIBILITY SIGNALS
Source Reliability: ...
Confidence Level: ...
Verified Facts:
- ...
Uncertain Claims:
- ...

HISTORICAL CONTEXT
Background: ...
Timeline:
- ...

PERSPECTIVES & DISAGREEMENTS
- Stakeholder: ...
  Viewpoint: ...
  Reasoning: ...

EXPLORATORY QUESTIONS
Questions:
- ...
Related Topics:
- ...

Separate each article with this line:

___________________________________________

Rules:
- Use only information from the article
- Do not fabricate sources
- If information is unavailable write "Not mentioned"""


def get_summary(query, serp_api_key=SERP_API_KEY, num_results=3):
    articles = get_top_news_with_content(query, serp_api_key, num_results)
    if not articles:
        print("No articles found to summarize.")
        return None
    USER_PROMPT = f"""
    Analyze the following articles using the Diggi framework.

    Articles:
    {json.dumps(articles, indent=2)}
    """

    response = client.responses.create(
    model="meta-llama/llama-4-scout-17b-16e-instruct",
    input=[
        {"role": "system", "content": SYSTEM_PROMPT_A},
        {"role": "user", "content": USER_PROMPT}
    ],
    temperature=0.2,
    )
    return response.output_text

SYSTEM_PROMPT_B = """You are a neutral news analysis assistant that converts raw news articles into structured analytical data.

Your task is to analyze news articles and produce structured output according to a predefined schema.

Follow these rules strictly:

GENERAL RULES
- Extract information only from the provided article text.
- Do not invent facts.
- If something is uncertain or speculative in the article, mark it appropriately in "uncertain_claims".
- Use neutral and factual language.

OUTPUT STRUCTURE
Your output must follow these analytical dimensions:

1. Claim-level focus
Break the article into individual factual claims.
For each claim include:
- claim
- actors involved
- supporting evidence from the article.

2. Multi-source comparison
If multiple sources are provided:
- Identify points where sources agree (consensus).
- Identify disagreements or differences in framing.
- Provide a short stance summary for each source.

3. Evidence & traceability
For important statements:
- Provide the statement
- Provide the exact supporting passage
- Include the source name and link if available.

4. Credibility signals
Assess the information quality without declaring truth or falsehood.
Include:
- source_reliability
- confidence_level
- verified_facts
- uncertain_claims

5. Historical & situational framing
Provide background context and a timeline of relevant events mentioned or implied in the article.

6. Perspectives & disagreements
Identify stakeholders and summarize their viewpoints and reasoning.

7. Exploratory questions
Generate open-ended analytical questions that help users explore the topic further.
Also include related topics for further investigation.

STRICT OUTPUT RULES
- Output must be valid JSON.
- Follow the schema structure exactly.
- Do not include explanations outside the JSON.
- Do not include markdown formatting.
- Do not add extra fields not defined in the schema.
- If information is missing, return empty lists instead of null.

Be precise, structured, and neutral."""

import time

def get_supper_summary(query, serp_api_key=SERP_API_KEY, num_results=3, max_retries=3, retry_delay=2):
    total_summary = get_summary(query, serp_api_key, num_results=3)
    if not total_summary:
        print("No summary generated.")
        return None
    
    print("Initial summary generated. Now refining into structured output...")
    USER_PROMPT = f"""
    Analyze the following news articles and generate structured analytical output using the defined schema.

    For each article include:
    - claim-level focus
    - multi-source comparison (compare with other articles if possible)
    - evidence traceability
    - credibility signals
    - historical context
    - perspectives and disagreements
    - exploratory questions

    Articles:
    {total_summary}
    """

    last_exception = None
    for attempt in range(1, max_retries + 1):
        try:
            # Use SYSTEM_PROMPT_B which is specifically designed for JSON schema enforcement
            response = client.beta.chat.completions.parse(
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT_B},
                    {"role": "user", "content": USER_PROMPT}
                ],
                model="openai/gpt-oss-120b",
                response_format=ArticleAnalysis,
            )
            return response.choices[0].message.parsed

        except Exception as e:
            last_exception = e
            print(f"Attempt {attempt}/{max_retries} failed: {e}")
            
            # Manual fallback if parse fails
            if "schema" in str(e).lower():
                try:
                    print("Attempting manual JSON fallback...")
                    fallback_response = client.chat.completions.create(
                        messages=[
                            {"role": "system", "content": SYSTEM_PROMPT_B},
                            {"role": "user", "content": USER_PROMPT}
                        ],
                        model="openai/gpt-oss-120b",
                        temperature=0.1
                    )
                    content = fallback_response.choices[0].message.content
                    if "```json" in content:
                        content = content.split("```json")[1].split("```")[0]
                    return ArticleAnalysis.model_validate_json(content.strip())
                except Exception as fallback_e:
                    print(f"Fallback also failed: {fallback_e}")

            if attempt < max_retries:
                print(f"Retrying in {retry_delay}s...")
                time.sleep(retry_delay)

    print(f"All {max_retries} attempts failed. Last error: {last_exception}")
    return None

def get_refined_suggestions(query):
    """Generates 4 high-quality search suggestions for a vague query."""
    print(f"Generating suggestions for vague query: '{query}'...")
    
    PROMPT = f"""
    The user provided a very vague or broad search query: '{query}'.
    Please provide exactly 4 specific, trending, or highly relevant news-style search queries that would yield better analytical results and the recent news relates to the topic.

    Return the suggestions as a JSON list of strings only.
    Example:
    ["Iran-Israel conflict updates 2024", "Iran's nuclear program international response", "Economic sanctions on Iran analysis", "Iran-Russia military cooperation"]
    """
    
    try:
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a helpful news search assistant. Return only a JSON list of 4 strings."},
                {"role": "user", "content": PROMPT}
            ],
            model="meta-llama/llama-4-scout-17b-16e-instruct", # Using a common model name from earlier, or just llama-3-70b
            temperature=0.7,
        )
        content = response.choices[0].message.content
        # Extract JSON from potential markdown blocks if LLM adds them
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
            
        suggestions = json.loads(content.strip())
        if isinstance(suggestions, list) and len(suggestions) >= 4:
            return suggestions[:4]
        return []
    except Exception as e:
        print(f"Error generating suggestions: {e}")
        return []

# if __name__ == "__main__":
#     query = "Iran USA War"
#     summary = get_supper_summary(query, SERP_API_KEY, 3)
#     if summary:
#         # print(summary)
#         print(json.dumps(summary.dict(), indent=2))