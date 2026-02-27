import json

from app.ai.client import anthropic_client

TONE_CHECK_PROMPT = """You are a tone mediator for a co-parenting communication platform.
Analyze the following message for hostile, blaming, or unproductive language patterns.

Look for:
- Blame language ("you always", "you never", "it's your fault")
- Passive aggression or sarcasm
- Name-calling or insults
- Ultimatums or threats
- Dismissive language

Message to analyze:
"{content}"

Respond with ONLY valid JSON (no markdown, no code blocks):
{{
  "is_hostile": true/false,
  "reason": "brief explanation of what was detected, or empty string if not hostile",
  "suggested_alternative": "a rephrased version that's constructive and focuses on the child's needs, or empty string if not hostile"
}}"""


async def check_tone(content: str) -> dict:
    response = await anthropic_client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=500,
        messages=[
            {"role": "user", "content": TONE_CHECK_PROMPT.format(content=content)}
        ],
    )
    text = response.content[0].text
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {
            "is_hostile": False,
            "reason": "",
            "suggested_alternative": "",
        }
