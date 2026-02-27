from unittest.mock import patch


def _create_problem_with_idea(client_a, group_with_parents):
    """Helper: create a problem and add one idea."""
    problem = client_a.post("/api/problems", json={
        "title": "Bedtime",
        "description": "Consistent bedtime",
        "group_id": group_with_parents.id,
    }).json()
    client_a.post(f"/api/problems/{problem['id']}/ideas", json={
        "content": "8pm school nights, 9pm weekends",
    })
    return problem


def test_single_approval_stays_brainstorming(client_a, client_b, group_with_parents):
    """One parent approving should NOT transition the session."""
    problem = _create_problem_with_idea(client_a, group_with_parents)

    with patch("app.services.analysis_runner.run_analysis"):
        resp = client_a.post(f"/api/problems/{problem['id']}/session/approve")

    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "brainstorming"
    assert len(data["approvals"]) == 1
    assert data["all_approved"] is False


def test_both_approve_transitions_to_approved(client_a, client_b, group_with_parents):
    """Both parents approving should transition to approved_for_analysis."""
    problem = _create_problem_with_idea(client_a, group_with_parents)

    with patch("app.services.analysis_runner.run_analysis") as mock_analysis:
        client_a.post(f"/api/problems/{problem['id']}/session/approve")
        resp = client_b.post(f"/api/problems/{problem['id']}/session/approve")

        mock_analysis.assert_called_once_with(problem["id"])

    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "approved_for_analysis"
    assert len(data["approvals"]) == 2
    assert data["all_approved"] is True


def test_duplicate_approval_409(client_a, client_b, group_with_parents):
    """Same parent approving twice should return 409."""
    problem = _create_problem_with_idea(client_a, group_with_parents)

    with patch("app.services.analysis_runner.run_analysis"):
        client_a.post(f"/api/problems/{problem['id']}/session/approve")
        resp = client_a.post(f"/api/problems/{problem['id']}/session/approve")

    assert resp.status_code == 409
    assert "already approved" in resp.json()["detail"]


def test_get_session_status(client_a, group_with_parents):
    problem = _create_problem_with_idea(client_a, group_with_parents)
    resp = client_a.get(f"/api/problems/{problem['id']}/session")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "brainstorming"
    assert data["total_collaborators"] == 2
