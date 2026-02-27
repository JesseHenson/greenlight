from app.ai.client import anthropic_client


SUMMARY_PROMPT = """You are summarizing a co-parenting brainstorming session.

Problem: {problem_title}
Description: {problem_description}

Ideas and their analyses:
{ideas_with_analyses}

Provide a comprehensive session summary that includes:
1. Common themes across ideas
2. Top 2-3 recommended solutions with brief justification
3. Key trade-offs to discuss
4. Suggested next steps for the co-parents

Respond with ONLY valid JSON (no markdown, no code blocks):
{{
  "themes": ["theme 1", "theme 2"],
  "top_recommendations": [
    {{"idea": "idea summary", "why": "justification"}},
    {{"idea": "idea summary", "why": "justification"}}
  ],
  "trade_offs": ["trade-off 1", "trade-off 2"],
  "next_steps": ["step 1", "step 2", "step 3"]
}}"""


async def summarize_session(
    problem_title: str,
    problem_description: str,
    ideas_with_analyses: str,
) -> str:
    response = await anthropic_client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=1500,
        messages=[
            {
                "role": "user",
                "content": SUMMARY_PROMPT.format(
                    problem_title=problem_title,
                    problem_description=problem_description,
                    ideas_with_analyses=ideas_with_analyses,
                ),
            }
        ],
    )
    return response.content[0].text
