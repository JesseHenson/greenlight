import json

from app.ai.client import anthropic_client

CREATIVITY_CHECK_PROMPT = """You are a creativity guardian for a brainstorming platform called Greenlight.
Your job is to protect divergent thinking by detecting contributions that shut down creativity too early.

The current session stage is: {stage}

{stage_instructions}

Message to analyze:
"{content}"

Respond with ONLY valid JSON (no markdown, no code blocks):
{{
  "is_convergent": true/false,
  "reason": "brief explanation of what type of premature analysis or criticism was detected, or empty string if fine",
  "suggested_alternative": "a reframed version that builds on ideas instead of shutting them down, or empty string if fine"
}}"""

IDEATE_INSTRUCTIONS = """During the IDEATE stage, be STRICT. Block ALL evaluation, criticism, and convergent thinking.

Detect and flag:
- Premature analysis: "that won't work because...", "let's be realistic", "the problem with that is..."
- Convergent thinking: "let's narrow down", "the best one is...", "we should focus on..."
- Dismissiveness: "we already tried that", "that's obvious", "everyone knows..."
- Criticism as questions: "but how would that even work?", "isn't that too expensive?"
- Judgment: "that's a bad idea", "not practical", "too risky"

Encourage: wild ideas, unexpected connections, "what if" thinking, building on others' ideas."""

BUILD_INSTRUCTIONS = """During the BUILD stage, be MODERATE. Block pure criticism but allow "Yes, And" building.

Flag contributions that:
- Tear down without building up: "that idea is flawed because..."
- Dismiss without offering alternatives: "no, that won't work"
- Skip straight to evaluation: "let's rank these" or "this one is clearly the best"

Allow contributions that:
- Build on existing ideas: "yes, and we could also..."
- Combine ideas: "what if we merged idea A with idea B?"
- Refine constructively: "I love this part, what if we also added..."
- Ask building questions: "how might we make this even bigger?"

Do NOT flag constructive building contributions."""

CONVERGE_INSTRUCTIONS = """During the CONVERGE stage, allow everything. Analysis and criticism are now welcome.
Always return is_convergent: false."""


async def check_creativity(content: str, stage: str = "ideate") -> dict:
    stage_map = {
        "ideate": IDEATE_INSTRUCTIONS,
        "build": BUILD_INSTRUCTIONS,
        "converge": CONVERGE_INSTRUCTIONS,
        "approved_for_analysis": CONVERGE_INSTRUCTIONS,
        "analysis_in_progress": CONVERGE_INSTRUCTIONS,
        "analysis_complete": CONVERGE_INSTRUCTIONS,
    }
    stage_instructions = stage_map.get(stage, IDEATE_INSTRUCTIONS)

    response = await anthropic_client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=500,
        messages=[
            {"role": "user", "content": CREATIVITY_CHECK_PROMPT.format(
                content=content,
                stage=stage,
                stage_instructions=stage_instructions,
            )}
        ],
    )
    text = response.content[0].text
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {
            "is_convergent": False,
            "reason": "",
            "suggested_alternative": "",
        }
