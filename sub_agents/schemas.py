"""
sub_agents/schemas.py
Strict Pydantic output schemas for all Hunter sub-agents.

Every sub-agent returns a validated Pydantic model to the Lead Agent (Hunter),
ensuring zero ambiguity in inter-agent communication. These models are serialized
to dicts and written to HunterState for downstream consumption.
"""

from pydantic import BaseModel, Field
from typing import Optional, List


# ═══════════════════════════════════════════════════════════════════════════════
# 1. SCOUT AGENT — Job Discovery
# ═══════════════════════════════════════════════════════════════════════════════

class JobListing(BaseModel):
    """A single job/internship discovered by the Scout Agent."""
    job_id: str = Field(description="Unique identifier for tracking (e.g., 'scout_001')")
    title: str = Field(description="Job title (e.g., 'AI Engineer Intern')")
    company: str = Field(description="Company name")
    location: str = Field(description="Job location or 'Remote'")
    url: str = Field(description="Direct application URL")
    description_summary: str = Field(description="2-3 sentence summary of the role")
    required_skills: List[str] = Field(default_factory=list, description="Key skills mentioned in the listing")
    source: str = Field(default="web_search", description="Where this listing was found")


class ScoutResult(BaseModel):
    """Structured output from the Scout Agent after a job search run."""
    query_used: str = Field(description="The search query that was executed")
    total_found: int = Field(description="Number of jobs discovered")
    jobs: List[JobListing] = Field(default_factory=list)
    report_path: Optional[str] = Field(default=None, description="Path to saved scout_report.md")


# ═══════════════════════════════════════════════════════════════════════════════
# 2. MATCH AGENT — Resume/Job Compatibility Scoring
# ═══════════════════════════════════════════════════════════════════════════════

class MatchDetail(BaseModel):
    """Compatibility analysis for a single job against the user's resume."""
    job_id: str
    company: str
    role: str
    fit_score: int = Field(ge=0, le=100, description="Compatibility score 0-100")
    matching_skills: List[str] = Field(default_factory=list, description="Skills the user already has")
    missing_skills: List[str] = Field(default_factory=list, description="Skills the user is missing")
    verdict: str = Field(description="HIGHLY_RECOMMENDED | GOOD_FIT | MODERATE | WEAK_FIT | SKIP")


class MatchResult(BaseModel):
    """Structured output from the Match Agent after scoring all scouted jobs."""
    total_scored: int
    ranked_jobs: List[MatchDetail] = Field(default_factory=list, description="Jobs sorted by fit_score descending")
    report_path: Optional[str] = Field(default=None, description="Path to saved job_rankings.md")


# ═══════════════════════════════════════════════════════════════════════════════
# 3. APPLICATION AGENT — Form Submission & Resume Upload
# ═══════════════════════════════════════════════════════════════════════════════

class ApplicationResult(BaseModel):
    """Structured output from the Application Agent after attempting to apply."""
    job_id: str
    company: str
    role: str
    status: str = Field(description="SUBMITTED | AWAITING_APPROVAL | FAILED")
    confirmation_screenshot: Optional[str] = Field(default=None, description="Path to screenshot if captured")
    notes: str = Field(default="", description="Any issues or details about the submission")


# ═══════════════════════════════════════════════════════════════════════════════
# 4. TRACKER AGENT — Application Status Logging
# ═══════════════════════════════════════════════════════════════════════════════

class TrackerRecord(BaseModel):
    """A single tracked application entry."""
    job_id: str
    company: str
    role: str
    applied_date: str = Field(description="ISO date string (e.g., '2026-09-02')")
    status: str = Field(description="APPLIED | INTERVIEWING | REJECTED | OFFER | WITHDRAWN")
    platform: str = Field(default="", description="Where the application was submitted")
    notes: Optional[str] = Field(default=None)


class TrackerResult(BaseModel):
    """Structured output from the Tracker Agent."""
    total_tracked: int
    records: List[TrackerRecord] = Field(default_factory=list)
    report_path: Optional[str] = Field(default=None, description="Path to saved tracker_report.md")


# ═══════════════════════════════════════════════════════════════════════════════
# 5. MARKET ANALYZER AGENT — Career Strategy & Skill Gap Analysis
# ═══════════════════════════════════════════════════════════════════════════════

class MarketAnalysisResult(BaseModel):
    """Structured output from the Market Analyzer Agent."""
    target_role: str = Field(description="The role being analyzed (e.g., 'AI Engineer')")
    top_in_demand_skills: List[str] = Field(default_factory=list, description="Most sought-after skills in the market")
    user_strong_skills: List[str] = Field(default_factory=list, description="Skills the user already excels at")
    resume_gap_analysis: List[str] = Field(default_factory=list, description="Skills/experiences the user is missing")
    recommended_actions: List[str] = Field(default_factory=list, description="Concrete improvement suggestions")
    market_trend_summary: str = Field(default="", description="Brief overview of industry hiring trends")


# ═══════════════════════════════════════════════════════════════════════════════
# 6. OUTREACH AGENT — Recruiter Cold Email Drafting & Dispatch
# ═══════════════════════════════════════════════════════════════════════════════

class OutreachResult(BaseModel):
    """Structured output from the Outreach Agent after drafting/sending an email."""
    company: str
    recipient_name: Optional[str] = Field(default=None, description="Recruiter or hiring manager name")
    recipient_email: str
    subject: str
    email_body: str
    status: str = Field(description="DRAFTED | SENT | FAILED")
    notes: Optional[str] = Field(default=None)
