"""Seed the database with example data for demo/testing."""
import json
from datetime import datetime, timedelta

from sqlmodel import Session

from app.database import engine, create_db_and_tables
from app.models.user import User
from app.models.problem import Challenge, ChallengeCollaborator, CollaboratorRole, ChallengeStatus
from app.models.idea import Idea
from app.models.session import GreenlightSession, SessionStatus
from app.models.analysis import Analysis, AnalysisType
from app.models.comment import Comment
from app.models.approval import SessionApproval, GateType
from app.models.draft import IdeaDraft
from app.models.group import Team, TeamMember, GroupRole

create_db_and_tables()

with Session(engine) as s:
    # ── Users ──
    user_a = User(name="Alex Chen", email="alex@test.com", clerk_id="seed_user_a")
    user_b = User(name="Jordan Lee", email="jordan@test.com", clerk_id="seed_user_b")
    s.add(user_a)
    s.add(user_b)
    s.commit()
    s.refresh(user_a)
    s.refresh(user_b)

    # ── Team ──
    team = Team(name="Product Team")
    s.add(team)
    s.commit()
    s.refresh(team)

    s.add(TeamMember(group_id=team.id, user_id=user_a.id, role=GroupRole.owner))
    s.add(TeamMember(group_id=team.id, user_id=user_b.id, role=GroupRole.member))
    s.commit()

    # ═══════════════════════════════════════════════════════
    # Challenge 1 — Ideate phase (active, with ideas)
    # ═══════════════════════════════════════════════════════
    c1 = Challenge(
        title="How might we reduce meeting fatigue?",
        description="Our team spends over 20 hours per week in meetings and it's crushing productivity. We need creative approaches to reduce meeting overhead while keeping everyone aligned.",
        created_by=user_a.id,
        group_id=team.id,
    )
    s.add(c1)
    s.commit()
    s.refresh(c1)

    s.add(ChallengeCollaborator(challenge_id=c1.id, user_id=user_a.id, role=CollaboratorRole.owner))
    s.add(ChallengeCollaborator(challenge_id=c1.id, user_id=user_b.id, role=CollaboratorRole.collaborator))
    session1 = GreenlightSession(challenge_id=c1.id, status=SessionStatus.ideate)
    s.add(session1)
    s.commit()
    s.refresh(session1)

    idea_c1_1 = Idea(challenge_id=c1.id, content="Replace all recurring meetings with async video updates — record a 2-min Loom instead", created_by=user_a.id)
    idea_c1_2 = Idea(challenge_id=c1.id, content="Meeting-free Wednesdays — no meetings allowed at all on Wednesdays, company-wide", created_by=user_b.id)
    idea_c1_3 = Idea(challenge_id=c1.id, content="AI meeting bot that attends for you and sends a summary — you only join if action items involve you", created_by=user_a.id)
    s.add(idea_c1_1)
    s.add(idea_c1_2)
    s.add(idea_c1_3)
    s.commit()
    s.refresh(idea_c1_1)
    s.refresh(idea_c1_2)
    s.refresh(idea_c1_3)

    # Example draft notes
    s.add(IdeaDraft(
        idea_id=idea_c1_1.id, user_id=user_a.id,
        notes="Love the async angle — could combine with written summaries",
        want_pros_cons=True, want_feasibility=True, want_impact=False,
    ))
    s.add(IdeaDraft(
        idea_id=idea_c1_2.id, user_id=user_b.id,
        notes="Simple and bold — would need exec buy-in",
        want_pros_cons=True, want_feasibility=False, want_impact=True,
    ))

    # ═══════════════════════════════════════════════════════
    # Challenge 2 — Analysis complete (full demo)
    # ═══════════════════════════════════════════════════════
    c2 = Challenge(
        title="Redesign the onboarding experience",
        description="New hires take 3 months to feel productive. We need ideas to compress onboarding and make the first week feel exciting, not overwhelming.",
        created_by=user_b.id,
        group_id=team.id,
    )
    s.add(c2)
    s.commit()
    s.refresh(c2)

    s.add(ChallengeCollaborator(challenge_id=c2.id, user_id=user_a.id, role=CollaboratorRole.collaborator))
    s.add(ChallengeCollaborator(challenge_id=c2.id, user_id=user_b.id, role=CollaboratorRole.owner))
    session2 = GreenlightSession(challenge_id=c2.id, status=SessionStatus.analysis_complete)
    s.add(session2)
    s.commit()
    s.refresh(session2)

    # Both teammates approved both gates for this completed session
    s.add(SessionApproval(session_id=session2.id, user_id=user_a.id, gate=GateType.ideate_to_build))
    s.add(SessionApproval(session_id=session2.id, user_id=user_b.id, gate=GateType.ideate_to_build))
    s.add(SessionApproval(session_id=session2.id, user_id=user_a.id, gate=GateType.build_to_converge))
    s.add(SessionApproval(session_id=session2.id, user_id=user_b.id, gate=GateType.build_to_converge))

    idea1 = Idea(challenge_id=c2.id, content="Pair every new hire with a 'day one buddy' who walks them through their first real task together", created_by=user_a.id)
    idea2 = Idea(challenge_id=c2.id, content="Gamified onboarding quest — complete challenges to unlock access to tools, repos, and Slack channels", created_by=user_b.id)
    idea3 = Idea(challenge_id=c2.id, content="Ship something on day one — have a tiny PR ready for them to modify, test, and deploy", created_by=user_a.id)
    s.add(idea1)
    s.add(idea2)
    s.add(idea3)
    s.commit()
    s.refresh(idea1)
    s.refresh(idea2)
    s.refresh(idea3)

    # ── Analyses for idea 1: Day One Buddy ──
    s.add(Analysis(idea_id=idea1.id, analysis_type=AnalysisType.pros_cons, content=json.dumps({
        "pros": [
            "Immediate human connection reduces first-day anxiety",
            "Knowledge transfer happens naturally through pairing",
            "Builds team relationships from day one",
        ],
        "cons": [
            "Buddy's productivity dips during onboarding week",
            "Quality depends on buddy's teaching skills",
            "May not scale well during large hiring waves",
        ],
        "stakeholder_impact": "Highly positive for new hires — they feel welcomed and productive faster. Moderate cost to buddies' existing workload."
    })))
    s.add(Analysis(idea_id=idea1.id, analysis_type=AnalysisType.feasibility, content=json.dumps({
        "score": 8, "logistics": "Easy to set up — just assign buddies from same team",
        "cost": "Low — only cost is buddy's time (~10 hrs/week for first week)",
        "time": "Can start immediately with next hire",
        "complexity": "Low — needs a buddy matching guide and a short training doc",
        "summary": "Highly feasible with minimal overhead"
    })))
    s.add(Analysis(idea_id=idea1.id, analysis_type=AnalysisType.impact, content=json.dumps({
        "score": 8, "team_impact": "Buddies develop mentoring skills; team bonds strengthen",
        "user_impact": "New hires feel supported and productive faster",
        "balance_assessment": "Strong positive impact across the board",
        "risks": "Risk of buddy burnout if they're assigned too frequently"
    })))

    # ── Analyses for idea 2: Gamified Quest ──
    s.add(Analysis(idea_id=idea2.id, analysis_type=AnalysisType.pros_cons, content=json.dumps({
        "pros": [
            "Makes onboarding feel fun and engaging",
            "Self-paced — new hires aren't blocked by others' schedules",
            "Progress is visible and measurable",
        ],
        "cons": [
            "Significant upfront development effort",
            "Needs ongoing maintenance as tools change",
            "Some people may find gamification patronizing",
        ],
        "stakeholder_impact": "Very engaging for new hires who enjoy game mechanics. Engineering team needs to build and maintain the platform."
    })))
    s.add(Analysis(idea_id=idea2.id, analysis_type=AnalysisType.feasibility, content=json.dumps({
        "score": 5, "logistics": "Need to build quest platform and integrate with existing tools",
        "cost": "Medium — 2-3 sprints of engineering effort upfront",
        "time": "2-3 months to build v1",
        "complexity": "Medium-high — integrations with Slack, GitHub, HR systems",
        "summary": "Requires meaningful investment but scales well"
    })))
    s.add(Analysis(idea_id=idea2.id, analysis_type=AnalysisType.impact, content=json.dumps({
        "score": 7, "team_impact": "Reduces ad-hoc onboarding questions; standardizes the experience",
        "user_impact": "New hires get a structured, self-guided experience",
        "balance_assessment": "Good long-term investment but high initial cost",
        "risks": "May become stale if not regularly updated with new content"
    })))

    # ── Analyses for idea 3: Ship on Day One ──
    s.add(Analysis(idea_id=idea3.id, analysis_type=AnalysisType.pros_cons, content=json.dumps({
        "pros": [
            "Incredible confidence boost — 'I shipped on my first day!'",
            "Forces dev environment setup to actually work",
            "Creates immediate sense of contribution",
        ],
        "cons": [
            "Requires maintaining a ready-to-go starter PR",
            "Might feel artificial if the change is too trivial",
            "Some roles don't have code to ship",
        ],
        "stakeholder_impact": "Hugely motivating for new engineers. Minimal impact on codebase. Forces the team to keep their setup docs current."
    })))
    s.add(Analysis(idea_id=idea3.id, analysis_type=AnalysisType.feasibility, content=json.dumps({
        "score": 7, "logistics": "Need a library of starter PRs maintained per team",
        "cost": "Low — small ongoing effort to maintain starter tasks",
        "time": "Can start within a week",
        "complexity": "Low-medium — needs CI/CD to support safe 'first deploy'",
        "summary": "Very doable with some prep work"
    })))
    s.add(Analysis(idea_id=idea3.id, analysis_type=AnalysisType.impact, content=json.dumps({
        "score": 9, "team_impact": "Team gets a real (small) contribution on day one",
        "user_impact": "New hire feels accomplished and part of the team immediately",
        "balance_assessment": "Highest impact-to-effort ratio of all ideas",
        "risks": "Risk of deployment issues causing a stressful first day if not well-prepared"
    })))

    # ── Summary ──
    s.add(Analysis(challenge_id=c2.id, analysis_type=AnalysisType.summary, content=json.dumps({
        "themes": ["Immediate contribution", "Human connection", "Self-paced learning", "Reducing anxiety"],
        "top_recommendations": [
            {"idea": "Ship something on day one", "why": "Highest impact with lowest effort — creates immediate sense of belonging and contribution"},
            {"idea": "Day one buddy system", "why": "Complements shipping by providing human support; easy to implement immediately"},
        ],
        "trade_offs": [
            "Ship-on-day-one requires maintained starter tasks but creates incredible first impressions",
            "Gamified quest has the best long-term scalability but highest upfront cost",
            "Buddy system is free but depends on individual buddy quality",
        ],
        "next_steps": [
            "Create 3 starter PRs (one per team) for the ship-on-day-one program",
            "Write a buddy matching guide and pilot with next 2 hires",
            "Evaluate gamified quest ROI after buddy + ship programs are running",
        ]
    })))

    # ── Example comments on idea 3 ──
    now = datetime.utcnow()
    s.add(Comment(idea_id=idea3.id, content="This is brilliant — I wish I had this when I started. The dev setup alone took me 2 days.", created_by=user_b.id, created_at=now - timedelta(hours=2)))
    s.add(Comment(idea_id=idea3.id, content="We could pre-configure their laptop image so the environment is ready to go on day one.", created_by=user_a.id, created_at=now - timedelta(hours=1, minutes=45)))
    s.add(Comment(idea_id=idea3.id, content="Yes! And we should have a celebration Slack message when they merge their first PR.", created_by=user_b.id, created_at=now - timedelta(hours=1, minutes=30)))

    # ═══════════════════════════════════════════════════════
    # Challenge 3 — Empty, just started
    # ═══════════════════════════════════════════════════════
    c3 = Challenge(
        title="Boost team engagement for remote workers",
        description="Half our team is remote and they consistently score lower on engagement surveys. We need creative ideas to make remote teammates feel just as connected and valued as in-office folks.",
        created_by=user_a.id,
        group_id=team.id,
    )
    s.add(c3)
    s.commit()
    s.refresh(c3)

    s.add(ChallengeCollaborator(challenge_id=c3.id, user_id=user_a.id, role=CollaboratorRole.owner))
    s.add(ChallengeCollaborator(challenge_id=c3.id, user_id=user_b.id, role=CollaboratorRole.collaborator))
    s.add(GreenlightSession(challenge_id=c3.id, status=SessionStatus.ideate))

    s.commit()
    print("Seeded: 2 users, 1 team, 3 challenges, 6 ideas, 10 analyses, 3 comments, 4 approvals, 2 drafts")
