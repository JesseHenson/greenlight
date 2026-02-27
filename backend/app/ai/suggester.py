import json

from app.ai.client import anthropic_client


SUGGEST_PROMPT = """You are a creative co-parenting advisor helping two parents brainstorm solutions.

Problem: {title}
Description: {description}

Existing ideas already suggested:
{existing_ideas}

Generate 3 NEW creative ideas that haven't been suggested yet. Focus on:
- Solutions that benefit the children first
- Fairness to both parents
- Practical and implementable approaches
- Creative compromises

Respond with ONLY valid JSON (no markdown, no code blocks):
[
  {{"idea": "description of idea 1", "rationale": "why this could work"}},
  {{"idea": "description of idea 2", "rationale": "why this could work"}},
  {{"idea": "description of idea 3", "rationale": "why this could work"}}
]"""


async def suggest_ideas(problem, existing_idea_contents: list[str]) -> list[dict]:
    existing = "\n".join(f"- {c}" for c in existing_idea_contents) or "None yet"

    response = await anthropic_client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=1000,
        messages=[
            {
                "role": "user",
                "content": SUGGEST_PROMPT.format(
                    title=problem.title,
                    description=problem.description,
                    existing_ideas=existing,
                ),
            }
        ],
    )
    text = response.content[0].text
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return []
