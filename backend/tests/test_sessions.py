from unittest.mock import patch


def _create_challenge_with_idea(client_a, team_with_members):
    """Helper: create a challenge and add one idea."""
    challenge = client_a.post("/api/challenges", json={
        "title": "Meeting fatigue",
        "description": "Too many meetings",
        "group_id": team_with_members.id,
    }).json()
    client_a.post(f"/api/challenges/{challenge['id']}/ideas", json={
        "content": "Replace all recurring meetings with async video updates",
    })
    return challenge


def test_single_approval_stays_ideating(client_a, client_b, team_with_members):
    """One member approving should NOT transition the session."""
    challenge = _create_challenge_with_idea(client_a, team_with_members)

    with patch("app.services.analysis_runner.run_analysis"):
        resp = client_a.post(f"/api/challenges/{challenge['id']}/session/approve")

    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ideate"
    assert len(data["approvals"]) == 1
    assert data["all_approved"] is False


def test_both_approve_transitions_to_build(client_a, client_b, team_with_members):
    """Both members approving ideate gate should transition to build."""
    challenge = _create_challenge_with_idea(client_a, team_with_members)

    with patch("app.services.analysis_runner.run_analysis"):
        client_a.post(f"/api/challenges/{challenge['id']}/session/approve")
        resp = client_b.post(f"/api/challenges/{challenge['id']}/session/approve")

    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "build"
    assert data["all_approved"] is False  # new gate, no approvals yet


def test_both_gates_leads_to_analysis(client_a, client_b, team_with_members):
    """Approving both gates should trigger analysis."""
    challenge = _create_challenge_with_idea(client_a, team_with_members)

    with patch("app.services.analysis_runner.run_analysis") as mock_analysis:
        # Gate 1: ideate -> build
        client_a.post(f"/api/challenges/{challenge['id']}/session/approve")
        client_b.post(f"/api/challenges/{challenge['id']}/session/approve")

        # Gate 2: build -> converge
        client_a.post(f"/api/challenges/{challenge['id']}/session/approve")
        resp = client_b.post(f"/api/challenges/{challenge['id']}/session/approve")

        mock_analysis.assert_called_once_with(challenge["id"])

    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "approved_for_analysis"


def test_duplicate_approval_409(client_a, client_b, team_with_members):
    """Same member approving twice should return 409."""
    challenge = _create_challenge_with_idea(client_a, team_with_members)

    with patch("app.services.analysis_runner.run_analysis"):
        client_a.post(f"/api/challenges/{challenge['id']}/session/approve")
        resp = client_a.post(f"/api/challenges/{challenge['id']}/session/approve")

    assert resp.status_code == 409
    assert "already approved" in resp.json()["detail"]


def test_get_session_status(client_a, team_with_members):
    challenge = _create_challenge_with_idea(client_a, team_with_members)
    resp = client_a.get(f"/api/challenges/{challenge['id']}/session")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ideate"
    assert data["total_collaborators"] == 2
