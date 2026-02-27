"""Seed the database with example data for demo/testing."""
import json
from datetime import datetime, timedelta

from sqlmodel import Session

from app.database import engine, create_db_and_tables
from app.models.user import User
from app.models.problem import Problem, ProblemCollaborator, CollaboratorRole, ProblemStatus
from app.models.idea import BrainstormIdea
from app.models.session import BrainstormSession, SessionStatus
from app.models.analysis import Analysis, AnalysisType
from app.models.comment import Comment
from app.models.approval import SessionApproval
from app.models.draft import IdeaDraft
from app.models.group import ParentGroup, ParentGroupMember, GroupRole

create_db_and_tables()

with Session(engine) as s:
    # ── Users ──
    # clerk_id placeholders — real Clerk IDs are assigned on first sign-in
    parent_a = User(name="Parent A", email="a@test.com", clerk_id="seed_parent_a")
    parent_b = User(name="Parent B", email="b@test.com", clerk_id="seed_parent_b")
    s.add(parent_a)
    s.add(parent_b)
    s.commit()
    s.refresh(parent_a)
    s.refresh(parent_b)

    # ── Parent Group ──
    group = ParentGroup(name="Our Family")
    s.add(group)
    s.commit()
    s.refresh(group)

    s.add(ParentGroupMember(group_id=group.id, user_id=parent_a.id, role=GroupRole.owner))
    s.add(ParentGroupMember(group_id=group.id, user_id=parent_b.id, role=GroupRole.member))
    s.commit()

    # ═══════════════════════════════════════════════════════
    # Conversation 1 — Brainstorming phase (active, with ideas)
    # ═══════════════════════════════════════════════════════
    p1 = Problem(
        title="Summer break schedule",
        description="We need to figure out how to split the 10 weeks of summer break fairly. Both of us want time for a family vacation, and the kids have camp the first two weeks of July.",
        created_by=parent_a.id,
        group_id=group.id,
    )
    s.add(p1)
    s.commit()
    s.refresh(p1)

    s.add(ProblemCollaborator(problem_id=p1.id, user_id=parent_a.id, role=CollaboratorRole.owner))
    s.add(ProblemCollaborator(problem_id=p1.id, user_id=parent_b.id, role=CollaboratorRole.collaborator))
    session1 = BrainstormSession(problem_id=p1.id, status=SessionStatus.brainstorming)
    s.add(session1)
    s.commit()
    s.refresh(session1)

    idea_p1_1 = BrainstormIdea(problem_id=p1.id, content="Alternate weeks — odd weeks with me, even weeks with you", created_by=parent_a.id)
    idea_p1_2 = BrainstormIdea(problem_id=p1.id, content="Split into two 5-week blocks so the kids have stability in each home", created_by=parent_b.id)
    idea_p1_3 = BrainstormIdea(problem_id=p1.id, content="Each parent gets a 2-week vacation block, remaining 6 weeks alternate weekly", created_by=parent_a.id)
    s.add(idea_p1_1)
    s.add(idea_p1_2)
    s.add(idea_p1_3)
    s.commit()
    s.refresh(idea_p1_1)
    s.refresh(idea_p1_2)
    s.refresh(idea_p1_3)

    # Example draft notes (private to each parent)
    s.add(IdeaDraft(
        idea_id=idea_p1_1.id, user_id=parent_a.id,
        notes="I like this but worried about the kids switching too often",
        want_pros_cons=True, want_feasibility=True, want_fairness=False,
    ))
    s.add(IdeaDraft(
        idea_id=idea_p1_2.id, user_id=parent_b.id,
        notes="5-week blocks give more routine for the kids",
        want_pros_cons=True, want_feasibility=False, want_fairness=True,
    ))

    # ═══════════════════════════════════════════════════════
    # Conversation 2 — Analysis complete (full demo)
    # ═══════════════════════════════════════════════════════
    p2 = Problem(
        title="After-school pickup logistics",
        description="School ends at 3:15 but neither of us can reliably leave work before 3. We need a plan for daily pickups that doesn't rely on one parent doing it every day.",
        created_by=parent_b.id,
        group_id=group.id,
    )
    s.add(p2)
    s.commit()
    s.refresh(p2)

    s.add(ProblemCollaborator(problem_id=p2.id, user_id=parent_a.id, role=CollaboratorRole.collaborator))
    s.add(ProblemCollaborator(problem_id=p2.id, user_id=parent_b.id, role=CollaboratorRole.owner))
    session2 = BrainstormSession(problem_id=p2.id, status=SessionStatus.analysis_complete)
    s.add(session2)
    s.commit()
    s.refresh(session2)

    # Both parents approved for this completed session
    s.add(SessionApproval(session_id=session2.id, user_id=parent_a.id))
    s.add(SessionApproval(session_id=session2.id, user_id=parent_b.id))

    idea1 = BrainstormIdea(problem_id=p2.id, content="Sign up for the school's after-care program (goes until 5:30)", created_by=parent_a.id)
    idea2 = BrainstormIdea(problem_id=p2.id, content="Set up a carpool rotation with two other families on our street", created_by=parent_b.id)
    idea3 = BrainstormIdea(problem_id=p2.id, content="Hire a part-time nanny to handle pickups Mon-Fri", created_by=parent_a.id)
    s.add(idea1)
    s.add(idea2)
    s.add(idea3)
    s.commit()
    s.refresh(idea1)
    s.refresh(idea2)
    s.refresh(idea3)

    # ── Analyses for idea 1: After-care ──
    s.add(Analysis(brainstorm_idea_id=idea1.id, analysis_type=AnalysisType.pros_cons, content=json.dumps({
        "pros": [
            "Reliable and structured — runs every school day",
            "Kids get homework help and supervised play",
            "No coordination needed between parents",
        ],
        "cons": [
            "Monthly cost (~$300-400)",
            "Kids may feel tired from a long day",
            "Less flexibility for early pickups",
        ],
        "children_impact": "Generally positive — kids socialize with peers and have access to activities, but some children may find the extended day exhausting."
    })))
    s.add(Analysis(brainstorm_idea_id=idea1.id, analysis_type=AnalysisType.feasibility, content=json.dumps({
        "score": 8, "logistics": "Easy to set up — just enroll", "cost": "$300-400/month, split between parents",
        "time": "No daily time commitment from either parent", "complexity": "Very low — school handles everything"
    })))
    s.add(Analysis(brainstorm_idea_id=idea1.id, analysis_type=AnalysisType.fairness, content=json.dumps({
        "score": 9, "parent_a_impact": "No daily burden, equal cost share",
        "parent_b_impact": "No daily burden, equal cost share",
        "balance_assessment": "Very balanced — neither parent carries more responsibility"
    })))

    # ── Analyses for idea 2: Carpool ──
    s.add(Analysis(brainstorm_idea_id=idea2.id, analysis_type=AnalysisType.pros_cons, content=json.dumps({
        "pros": [
            "Free — no financial cost",
            "Builds community with neighbor families",
            "Kids ride home with friends",
        ],
        "cons": [
            "Depends on other families' reliability",
            "Needs coordination when schedules change",
            "May not cover every day if families drop out",
        ],
        "children_impact": "Positive — kids enjoy riding with friends and it reinforces neighborhood bonds."
    })))
    s.add(Analysis(brainstorm_idea_id=idea2.id, analysis_type=AnalysisType.feasibility, content=json.dumps({
        "score": 5, "logistics": "Need to recruit and coordinate 2+ families",
        "cost": "Free", "time": "Each parent drives ~1 day/week",
        "complexity": "Medium — requires ongoing communication and backup plans"
    })))
    s.add(Analysis(brainstorm_idea_id=idea2.id, analysis_type=AnalysisType.fairness, content=json.dumps({
        "score": 7, "parent_a_impact": "Drives roughly 1 day/week on their custody days",
        "parent_b_impact": "Drives roughly 1 day/week on their custody days",
        "balance_assessment": "Mostly fair, but imbalance possible if one parent has more custody days during the week"
    })))

    # ── Analyses for idea 3: Nanny ──
    s.add(Analysis(brainstorm_idea_id=idea3.id, analysis_type=AnalysisType.pros_cons, content=json.dumps({
        "pros": [
            "Most flexible — nanny adjusts to your schedule",
            "One-on-one attention for the kids",
            "Can also help with homework and light chores",
        ],
        "cons": [
            "Most expensive option ($800-1200/month)",
            "Need to find, vet, and manage an employee",
            "Kids miss out on socializing with peers after school",
        ],
        "children_impact": "Mixed — kids get personalized attention but less peer interaction compared to after-care or carpool."
    })))
    s.add(Analysis(brainstorm_idea_id=idea3.id, analysis_type=AnalysisType.feasibility, content=json.dumps({
        "score": 6, "logistics": "Need to hire, do background check, set schedule",
        "cost": "$800-1200/month split between parents",
        "time": "Low daily time once hired, but management overhead",
        "complexity": "Medium-high — employment logistics, backup if nanny is sick"
    })))
    s.add(Analysis(brainstorm_idea_id=idea3.id, analysis_type=AnalysisType.fairness, content=json.dumps({
        "score": 8, "parent_a_impact": "Equal cost share, no pickup duty",
        "parent_b_impact": "Equal cost share, no pickup duty",
        "balance_assessment": "Fair if costs are split evenly — one parent may end up managing the nanny more"
    })))

    # ── Summary ──
    s.add(Analysis(problem_id=p2.id, analysis_type=AnalysisType.summary, content=json.dumps({
        "themes": ["Reliability", "Cost", "Fairness", "Children's wellbeing"],
        "top_recommendations": [
            {"idea": "After-care program", "why": "Most reliable with lowest coordination overhead and very fair split"},
            {"idea": "Carpool as backup", "why": "Free complement for days when after-care isn't available"},
        ],
        "trade_offs": [
            "After-care costs money but saves both parents daily stress",
            "Carpool is free but fragile — depends on neighbors' consistency",
            "Nanny is most flexible but most expensive and hardest to set up",
        ],
        "next_steps": [
            "Check if the school's after-care program has open spots",
            "Talk to the Johnsons and Garcias about carpool interest",
            "Agree on a cost-split ratio for whichever paid option you choose",
        ]
    })))

    # ── Example comments on idea 1 ──
    now = datetime.utcnow()
    s.add(Comment(idea_id=idea1.id, content="I think this is our best bet honestly. The kids already know the after-care teachers.", created_by=parent_b.id, created_at=now - timedelta(hours=2)))
    s.add(Comment(idea_id=idea1.id, content="Agreed, but can we split the cost 50/50? I don't want to be stuck paying the whole thing.", created_by=parent_a.id, created_at=now - timedelta(hours=1, minutes=45)))
    s.add(Comment(idea_id=idea1.id, content="Of course, 50/50 makes sense. Should we sign up for the semester or month-to-month?", created_by=parent_b.id, created_at=now - timedelta(hours=1, minutes=30)))

    # ═══════════════════════════════════════════════════════
    # Conversation 3 — Empty, just started
    # ═══════════════════════════════════════════════════════
    p3 = Problem(
        title="Holiday gift coordination",
        description="Last year the kids got duplicate gifts from both of us and it was awkward. We should coordinate who's getting what this year so there's no overlap and the kids get a good variety.",
        created_by=parent_a.id,
        group_id=group.id,
    )
    s.add(p3)
    s.commit()
    s.refresh(p3)

    s.add(ProblemCollaborator(problem_id=p3.id, user_id=parent_a.id, role=CollaboratorRole.owner))
    s.add(ProblemCollaborator(problem_id=p3.id, user_id=parent_b.id, role=CollaboratorRole.collaborator))
    s.add(BrainstormSession(problem_id=p3.id, status=SessionStatus.brainstorming))

    s.commit()
    print("Seeded: 2 users, 1 parent group, 3 conversations, 6 ideas, 10 analyses, 3 comments, 2 approvals, 2 drafts")
