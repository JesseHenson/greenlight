import json

from app.ai.client import anthropic_client


PROS_CONS_PROMPT = """Analyze this idea from multiple stakeholder perspectives.

Challenge context: {challenge_context}
Idea: {idea_content}

Provide a pros and cons analysis considering:
- Impact on the team and organization
- Impact on end users or customers
- Impact on key stakeholders
- Long-term sustainability

Respond with ONLY valid JSON (no markdown, no code blocks):
{{
  "pros": ["pro 1", "pro 2", "pro 3"],
  "cons": ["con 1", "con 2", "con 3"],
  "stakeholder_impact": "brief assessment of impact on key stakeholders"
}}"""

FEASIBILITY_PROMPT = """Assess the feasibility of this idea.

Challenge context: {challenge_context}
Idea: {idea_content}

Evaluate on these dimensions and respond with ONLY valid JSON (no markdown, no code blocks):
{{
  "score": 7,
  "logistics": "assessment of practical logistics",
  "cost": "assessment of financial impact",
  "time": "assessment of time requirements",
  "complexity": "assessment of implementation complexity",
  "summary": "one-line feasibility summary"
}}

Score from 1 (very difficult) to 10 (very easy to implement)."""

IMPACT_PROMPT = """Assess the potential impact of this idea on all stakeholders.

Challenge context: {challenge_context}
Idea: {idea_content}

Evaluate how this idea impacts different stakeholders and respond with ONLY valid JSON (no markdown, no code blocks):
{{
  "score": 7,
  "team_impact": "how this affects the team implementing it",
  "user_impact": "how this affects end users or customers",
  "balance_assessment": "overall impact assessment across stakeholders",
  "risks": "any risks or unintended consequences to watch for"
}}

Score from 1 (very low impact) to 10 (transformative impact)."""


async def analyze_idea(idea_content: str, challenge_context: str, analysis_type: str) -> str:
    prompts = {
        "pros_cons": PROS_CONS_PROMPT,
        "feasibility": FEASIBILITY_PROMPT,
        "impact": IMPACT_PROMPT,
    }
    prompt = prompts[analysis_type].format(
        challenge_context=challenge_context, idea_content=idea_content
    )

    response = await anthropic_client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text
