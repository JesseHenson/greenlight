from app.models.notification import Notification, NotificationType


def test_list_notifications_empty(client_a, session, user_a):
    res = client_a.get("/api/notifications")
    assert res.status_code == 200
    assert res.json() == []


def test_list_notifications(client_a, session, user_a):
    session.add(Notification(
        user_id=user_a.id,
        type=NotificationType.idea_added,
        title="New idea",
        body="Someone added an idea",
        challenge_id=1,
    ))
    session.commit()

    res = client_a.get("/api/notifications")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 1
    assert data[0]["title"] == "New idea"
    assert data[0]["read"] is False


def test_unread_count(client_a, session, user_a):
    session.add(Notification(
        user_id=user_a.id, type=NotificationType.idea_added,
        title="T", body="B",
    ))
    session.add(Notification(
        user_id=user_a.id, type=NotificationType.comment_added,
        title="T2", body="B2", read=True,
    ))
    session.commit()

    res = client_a.get("/api/notifications/unread-count")
    assert res.status_code == 200
    assert res.json()["count"] == 1


def test_mark_read(client_a, session, user_a):
    notif = Notification(
        user_id=user_a.id, type=NotificationType.idea_added,
        title="T", body="B",
    )
    session.add(notif)
    session.commit()
    session.refresh(notif)

    res = client_a.post(f"/api/notifications/{notif.id}/read")
    assert res.status_code == 200

    res = client_a.get("/api/notifications/unread-count")
    assert res.json()["count"] == 0


def test_mark_read_not_found(client_a, session, user_a):
    res = client_a.post("/api/notifications/99999/read")
    assert res.status_code == 404


def test_mark_read_other_user(client_a, session, user_a, user_b):
    notif = Notification(
        user_id=user_b.id, type=NotificationType.idea_added,
        title="T", body="B",
    )
    session.add(notif)
    session.commit()
    session.refresh(notif)

    res = client_a.post(f"/api/notifications/{notif.id}/read")
    assert res.status_code == 404


def test_mark_all_read(client_a, session, user_a):
    for i in range(3):
        session.add(Notification(
            user_id=user_a.id, type=NotificationType.idea_added,
            title=f"T{i}", body=f"B{i}",
        ))
    session.commit()

    res = client_a.post("/api/notifications/read-all")
    assert res.status_code == 200
    assert "3" in res.json()["message"]

    res = client_a.get("/api/notifications/unread-count")
    assert res.json()["count"] == 0


def test_idea_creates_notification(client_a, client_b, session, user_a, user_b):
    """Creating an idea should notify other collaborators."""
    from app.models.problem import Challenge, ChallengeCollaborator, CollaboratorRole
    from app.models.session import GreenlightSession

    c = Challenge(title="Notif Test", description="D", created_by=user_a.id)
    session.add(c)
    session.commit()
    session.refresh(c)
    session.add(ChallengeCollaborator(challenge_id=c.id, user_id=user_a.id, role=CollaboratorRole.owner))
    session.add(ChallengeCollaborator(challenge_id=c.id, user_id=user_b.id, role=CollaboratorRole.collaborator))
    session.add(GreenlightSession(challenge_id=c.id))
    session.commit()

    client_a.post(f"/api/challenges/{c.id}/ideas", json={"content": "My great idea"})

    res = client_b.get("/api/notifications/unread-count")
    assert res.json()["count"] == 1


def test_comment_creates_notification(client_a, client_b, session, user_a, user_b):
    """Creating a comment should notify other collaborators."""
    from app.models.problem import Challenge, ChallengeCollaborator, CollaboratorRole
    from app.models.idea import Idea

    c = Challenge(title="Comment Notif", description="D", created_by=user_a.id)
    session.add(c)
    session.commit()
    session.refresh(c)
    session.add(ChallengeCollaborator(challenge_id=c.id, user_id=user_a.id, role=CollaboratorRole.owner))
    session.add(ChallengeCollaborator(challenge_id=c.id, user_id=user_b.id, role=CollaboratorRole.collaborator))
    idea = Idea(challenge_id=c.id, content="Idea", created_by=user_a.id)
    session.add(idea)
    session.commit()
    session.refresh(idea)

    client_b.post(f"/api/ideas/{idea.id}/comments", json={"content": "Nice idea!"})

    res = client_a.get("/api/notifications/unread-count")
    assert res.json()["count"] == 1
