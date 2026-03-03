"""Tests for AI modules with mocked Anthropic client."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def _mock_response(text: str):
    """Build a mock Anthropic API response."""
    block = MagicMock()
    block.text = text
    resp = MagicMock()
    resp.content = [block]
    return resp


@pytest.mark.asyncio
async def test_check_creativity_convergent():
    result_json = json.dumps({
        "is_convergent": True,
        "reason": "Premature criticism",
        "suggested_alternative": "Build on the idea",
    })
    mock_client = MagicMock()
    mock_client.messages.create = AsyncMock(return_value=_mock_response(result_json))

    with patch("app.ai.mediator.anthropic_client", mock_client):
        from app.ai.mediator import check_creativity
        result = await check_creativity("That won't work", "ideate")

    assert result["is_convergent"] is True
    assert result["reason"] == "Premature criticism"


@pytest.mark.asyncio
async def test_check_creativity_safe():
    result_json = json.dumps({
        "is_convergent": False,
        "reason": "",
        "suggested_alternative": "",
    })
    mock_client = MagicMock()
    mock_client.messages.create = AsyncMock(return_value=_mock_response(result_json))

    with patch("app.ai.mediator.anthropic_client", mock_client):
        from app.ai.mediator import check_creativity
        result = await check_creativity("What if we tried X?", "build")

    assert result["is_convergent"] is False


@pytest.mark.asyncio
async def test_check_creativity_invalid_json():
    mock_client = MagicMock()
    mock_client.messages.create = AsyncMock(return_value=_mock_response("not json"))

    with patch("app.ai.mediator.anthropic_client", mock_client):
        from app.ai.mediator import check_creativity
        result = await check_creativity("test", "converge")

    assert result["is_convergent"] is False
    assert result["reason"] == ""


@pytest.mark.asyncio
async def test_check_creativity_stage_mapping():
    """Test that all stage variants resolve without error."""
    result_json = json.dumps({
        "is_convergent": False, "reason": "", "suggested_alternative": ""
    })
    mock_client = MagicMock()
    mock_client.messages.create = AsyncMock(return_value=_mock_response(result_json))

    with patch("app.ai.mediator.anthropic_client", mock_client):
        from app.ai.mediator import check_creativity
        for stage in ["ideate", "build", "converge", "approved_for_analysis",
                      "analysis_in_progress", "analysis_complete", "unknown_stage"]:
            result = await check_creativity("content", stage)
            assert "is_convergent" in result


@pytest.mark.asyncio
async def test_suggest_ideas_success():
    suggestions = [
        {"idea": "Idea A", "rationale": "Good"},
        {"idea": "Idea B", "rationale": "Better"},
    ]
    mock_client = MagicMock()
    mock_client.messages.create = AsyncMock(
        return_value=_mock_response(json.dumps(suggestions))
    )

    challenge = MagicMock()
    challenge.title = "Test Challenge"
    challenge.description = "Some description"

    with patch("app.ai.suggester.anthropic_client", mock_client):
        from app.ai.suggester import suggest_ideas
        result = await suggest_ideas(challenge, ["existing idea 1"])

    assert len(result) == 2
    assert result[0]["idea"] == "Idea A"


@pytest.mark.asyncio
async def test_suggest_ideas_no_existing():
    suggestions = [{"idea": "Fresh", "rationale": "New"}]
    mock_client = MagicMock()
    mock_client.messages.create = AsyncMock(
        return_value=_mock_response(json.dumps(suggestions))
    )

    challenge = MagicMock()
    challenge.title = "T"
    challenge.description = "D"

    with patch("app.ai.suggester.anthropic_client", mock_client):
        from app.ai.suggester import suggest_ideas
        result = await suggest_ideas(challenge, [])

    assert len(result) == 1


@pytest.mark.asyncio
async def test_suggest_ideas_invalid_json():
    mock_client = MagicMock()
    mock_client.messages.create = AsyncMock(return_value=_mock_response("oops"))

    challenge = MagicMock()
    challenge.title = "T"
    challenge.description = "D"

    with patch("app.ai.suggester.anthropic_client", mock_client):
        from app.ai.suggester import suggest_ideas
        result = await suggest_ideas(challenge, [])

    assert result == []


@pytest.mark.asyncio
async def test_analyze_idea():
    mock_client = MagicMock()
    mock_client.messages.create = AsyncMock(
        return_value=_mock_response('{"pros": ["good"], "cons": ["bad"]}')
    )

    with patch("app.ai.analyzer.anthropic_client", mock_client):
        from app.ai.analyzer import analyze_idea
        result = await analyze_idea("My idea", "Challenge context", "pros_cons")

    assert "pros" in result


@pytest.mark.asyncio
async def test_analyze_idea_feasibility():
    mock_client = MagicMock()
    mock_client.messages.create = AsyncMock(
        return_value=_mock_response('{"score": 8, "summary": "Feasible"}')
    )

    with patch("app.ai.analyzer.anthropic_client", mock_client):
        from app.ai.analyzer import analyze_idea
        result = await analyze_idea("My idea", "Context", "feasibility")

    assert "score" in result


@pytest.mark.asyncio
async def test_summarize_session():
    mock_client = MagicMock()
    mock_client.messages.create = AsyncMock(
        return_value=_mock_response('{"themes": ["speed"], "top_recommendations": []}')
    )

    with patch("app.ai.summarizer.anthropic_client", mock_client):
        from app.ai.summarizer import summarize_session
        result = await summarize_session("Title", "Desc", "Ideas text")

    assert "themes" in result
