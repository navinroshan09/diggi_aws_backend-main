from pydantic import BaseModel
from typing import List, Optional


# ---------- 1. CLAIM LEVEL FOCUS ----------
class Claim(BaseModel):
    claim: str
    actors: List[str]
    evidence: str


class ClaimLevelFocus(BaseModel):
    claims: List[Claim]


# ---------- 2. MULTI SOURCE COMPARISON ----------
class SourceComparison(BaseModel):
    source: str
    stance: str
    key_points: List[str]


class MultiSourceComparison(BaseModel):
    consensus_points: List[str]
    disagreement_points: List[str]
    sources: List[SourceComparison]


# ---------- 3. EVIDENCE TRACEABILITY ----------
class EvidenceTrace(BaseModel):
    statement: str
    supporting_passage: str
    source: str
    link: str


class EvidenceTraceability(BaseModel):
    evidence: List[EvidenceTrace]


# ---------- 4. CREDIBILITY SIGNALS ----------
class CredibilitySignals(BaseModel):
    source_reliability: str
    confidence_level: str
    verified_facts: List[str]
    uncertain_claims: List[str]


# ---------- 5. HISTORICAL CONTEXT ----------
class TimelineEvent(BaseModel):
    date: str
    event: str


class HistoricalContext(BaseModel):
    background: str
    timeline: List[TimelineEvent]


# ---------- 6. PERSPECTIVES ----------
class Perspective(BaseModel):
    stakeholder: str
    viewpoint: str
    reasoning: str


class Perspectives(BaseModel):
    perspectives: List[Perspective]


# ---------- 7. EXPLORATORY QUESTIONS ----------
class ExploratoryQuestions(BaseModel):
    questions: List[str]
    related_topics: List[str]


# ---------- FINAL ARTICLE STRUCTURE ----------
class ArticleAnalysis(BaseModel):
    claim_level_focus: ClaimLevelFocus
    multi_source_comparison: MultiSourceComparison
    evidence_traceability: EvidenceTraceability
    credibility_signals: CredibilitySignals
    historical_context: HistoricalContext
    perspectives: Perspectives
    exploratory_questions: ExploratoryQuestions