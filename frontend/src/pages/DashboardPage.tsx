import { useEffect, useState } from 'react';
import { UserButton } from '@clerk/clerk-react';
import api from '../api/client';
import type { Challenge, User, Team } from '../types';
import ChallengeCard from '../components/ChallengeCard';
import CreateChallengeModal from '../components/CreateChallengeModal';
import TeamSetup from '../components/TeamSetup';
import TeamSettingsModal from '../components/TeamSettingsModal';
import WelcomePage from './WelcomePage';
import NotificationBell from '../components/NotificationBell';

interface Props {
  user: User;
  onDevSignOut?: () => void;
}

export default function DashboardPage({ user, onDevSignOut }: Props) {
  const [challenges, setChallenges] = useState<Challenge[]>([]);
  const [showCreate, setShowCreate] = useState(false);
  const [loading, setLoading] = useState(true);
  const [team, setTeam] = useState<Team | null>(null);
  const [teamLoading, setTeamLoading] = useState(true);
  const [showTeamSettings, setShowTeamSettings] = useState(false);
  const [skippedOnboarding, setSkippedOnboarding] = useState(false);

  const fetchChallenges = async () => {
    try {
      const res = await api.get('/challenges');
      setChallenges(res.data);
    } finally {
      setLoading(false);
    }
  };

  const fetchTeams = async () => {
    try {
      const res = await api.get('/teams');
      if (res.data.length > 0) {
        setTeam(res.data[0]);
      }
    } finally {
      setTeamLoading(false);
    }
  };

  useEffect(() => {
    fetchChallenges();
    fetchTeams();
  }, []);

  const handleArchive = async (challengeId: number) => {
    try {
      await api.post(`/challenges/${challengeId}/archive`);
      fetchChallenges();
    } catch {
      // ignore
    }
  };

  // Show full-screen welcome for first-time users (no team yet)
  if (!teamLoading && !team && !skippedOnboarding) {
    return (
      <WelcomePage
        onComplete={(t) => setTeam(t)}
        onSkip={() => setSkippedOnboarding(true)}
      />
    );
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-slate-900">
        <div className="max-w-5xl mx-auto px-4 py-4 flex items-center justify-between">
          <h1 className="text-lg font-semibold text-white tracking-tight">Greenlight</h1>
          <div className="flex items-center gap-2 sm:gap-4">
            {team && (
              <button
                onClick={() => setShowTeamSettings(true)}
                className="flex items-center gap-2 px-2 py-1 rounded-md hover:bg-slate-800 transition-colors"
                title="Team settings"
              >
                <span className="hidden sm:inline text-xs text-slate-400 uppercase tracking-wide">{team.name || 'Team'}</span>
                <div className="flex -space-x-2">
                  {team.members.map((m) => (
                    <div
                      key={m.user_id}
                      title={m.user_name}
                      className="w-7 h-7 rounded-full bg-emerald-500/20 border-2 border-slate-800 flex items-center justify-center text-xs font-medium text-emerald-300"
                    >
                      {m.user_name.charAt(0).toUpperCase()}
                    </div>
                  ))}
                </div>
              </button>
            )}
            <NotificationBell />
            <span className="hidden sm:inline text-sm text-slate-300">{user.name}</span>
            {onDevSignOut ? (
              <button
                onClick={onDevSignOut}
                className="px-3 py-1 text-xs text-slate-400 hover:text-white border border-slate-700 rounded-md hover:bg-slate-800 transition-colors"
              >
                Switch User
              </button>
            ) : (
              <UserButton />
            )}
          </div>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 py-6 sm:py-8">
        {!teamLoading && !team && (
          <TeamSetup onTeamCreated={(t) => setTeam(t)} />
        )}

        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-semibold text-slate-900 tracking-tight">Challenges</h2>
          <button
            onClick={() => setShowCreate(true)}
            className="px-4 py-2 bg-emerald-600 text-white rounded-md hover:bg-emerald-700 font-medium shadow-sm transition-colors"
          >
            + New Challenge
          </button>
        </div>

        {loading ? (
          <div className="text-center py-12 text-slate-500">Loading...</div>
        ) : challenges.length === 0 ? (
          <div className="text-center py-12 bg-white rounded-lg border border-slate-200/60 shadow-sm">
            <p className="text-slate-500 mb-4">No challenges yet. Start one to begin brainstorming!</p>
            <button
              onClick={() => setShowCreate(true)}
              className="px-4 py-2 bg-emerald-600 text-white rounded-md hover:bg-emerald-700 shadow-sm transition-colors"
            >
              Create Your First Challenge
            </button>
          </div>
        ) : (
          <div className="grid gap-4 md:grid-cols-2">
            {challenges.map((c) => (
              <ChallengeCard key={c.id} challenge={c} onArchive={handleArchive} />
            ))}
          </div>
        )}
      </main>

      {showCreate && (
        <CreateChallengeModal
          groupId={team?.id ?? null}
          onCreated={() => {
            setShowCreate(false);
            fetchChallenges();
          }}
          onClose={() => setShowCreate(false)}
        />
      )}

      {showTeamSettings && team && (
        <TeamSettingsModal
          team={team}
          onClose={() => setShowTeamSettings(false)}
          onTeamUpdated={(updated) => setTeam(updated)}
        />
      )}
    </div>
  );
}
