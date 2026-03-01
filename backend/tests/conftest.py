import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app.database import get_session
from app.main import app
from app.models.user import User
from app.models.group import Team, TeamMember, GroupRole


@pytest.fixture(name="engine")
def engine_fixture():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    yield engine


@pytest.fixture(name="session")
def session_fixture(engine):
    with Session(engine) as session:
        yield session


@pytest.fixture(name="user_a")
def user_a_fixture(session):
    user = User(name="Alex", email="a@test.com", clerk_id="clerk_a")
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture(name="user_b")
def user_b_fixture(session):
    user = User(name="Jordan", email="b@test.com", clerk_id="clerk_b")
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture(name="team_with_members")
def team_with_members_fixture(session, user_a, user_b):
    team = Team(name="Test Team")
    session.add(team)
    session.commit()
    session.refresh(team)

    session.add(TeamMember(group_id=team.id, user_id=user_a.id, role=GroupRole.owner))
    session.add(TeamMember(group_id=team.id, user_id=user_b.id, role=GroupRole.member))
    session.commit()
    return team


@pytest.fixture(autouse=True)
def setup_app(session, monkeypatch):
    """Override DB session and mock Clerk auth for all tests."""

    def get_session_override():
        yield session

    app.dependency_overrides[get_session] = get_session_override

    # Mock verify_clerk_token: treat the raw token as the clerk_id
    monkeypatch.setattr(
        "app.dependencies.verify_clerk_token",
        lambda token: {"sub": token},
    )
    # Mock get_clerk_user_info so auto-provision doesn't call Clerk API
    monkeypatch.setattr(
        "app.dependencies.get_clerk_user_info",
        lambda cid: None,
    )

    yield

    app.dependency_overrides.clear()


@pytest.fixture(name="client_a")
def client_a_fixture(user_a):
    """TestClient authenticated as User A."""
    client = TestClient(app)
    client.headers["Authorization"] = f"Bearer {user_a.clerk_id}"
    return client


@pytest.fixture(name="client_b")
def client_b_fixture(user_b):
    """TestClient authenticated as User B."""
    client = TestClient(app)
    client.headers["Authorization"] = f"Bearer {user_b.clerk_id}"
    return client
