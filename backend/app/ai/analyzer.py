import json

from app.ai.client import anthropic_client


PROS_CONS_PROMPT = """Analyze this co-parenting idea from multiple perspectives.

Problem context: {problem_context}
Idea: {idea_content}

Provide a pros and cons analysis considering:
- Impact on the children
- Impact on Parent A
- Impact on Parent B
- Long-term sustainability

Respond with ONLY valid JSON (no markdown, no code blocks):
{{
  "pros": ["pro 1", "pro 2", "pro 3"],
  "cons": ["con 1", "con 2", "con 3"],
  "children_impact": "brief assessment of impact on children"
}}"""

FEASIBILITY_PROMPT = """Assess the feasibility of this co-parenting idea.

Problem context: {problem_context}
Idea: {idea_content}

Evaluate on these dimensions and respond with ONLY valid JSON (no markdown, no code blocks):
{{
  "score": 7,
  "logistics": "assessment of practical logistics",
  "cost": "assessment of financial impact",
  "time": "assessment of time requirements",
  "complexity": "assessment of coordination complexity",
  "summary": "one-line feasibility summary"
}}

Score from 1 (very difficult) to 10 (very easy to implement)."""

FAIRNESS_PROMPT = """Assess the fairness of this co-parenting idea for both parents.

Problem context: {problem_context}
Idea: {idea_content}

Evaluate how this idea impacts each parent and respond with ONLY valid JSON (no markdown, no code blocks):
{{
  "score": 7,
  "parent_a_impact": "how this affects the parent who proposed the problem",
  "parent_b_impact": "how this affects the co-parent",
  "balance_assessment": "overall fairness assessment",
  "potential_resentment": "any areas that might cause resentment if not addressed"
}}

Score from 1 (very unfair) to 10 (perfectly balanced)."""


async def analyze_idea(idea_content: str, problem_context: str, analysis_type: str) -> str:
    prompts = {
        "pros_cons": PROS_CONS_PROMPT,
        "feasibility": FEASIBILITY_PROMPT,
        "fairness": FAIRNESS_PROMPT,
    }
    prompt = prompts[analysis_type].format(
        problem_context=problem_context, idea_content=idea_content
    )

    response = await anthropic_client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text
