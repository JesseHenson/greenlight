import { useCallback, useEffect, useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { isAxiosError } from 'axios';
import api from '../api/client';
import type { Challenge, Idea, GreenlightSession, User } from '../types';
import IdeaCard from '../components/IdeaCard';
import AddIdeaForm from '../components/AddIdeaForm';
import SessionStatusBar from '../components/SessionStatusBar';
import AISuggestButton from '../components/AISuggestButton';

interface Props {
  user: User;
}

export default function ChallengeDetailPage({ user }: Props) {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [challenge, setChallenge] = useState<Challenge | null>(null);
  const [ideas, setIdeas] = useState<Idea[]>([]);
  const [session, setSession] = useState<GreenlightSession | null>(null);
  const [approving, setApproving] = useState(false);
  const [collabEmail, setCollabEmail] = useState('');
  const [collabMsg, setCollabMsg] = useState('');

  const fetchAll = useCallback(async () => {
    const [cRes, iRes, sRes] = await Promise.all([
      api.get(`/challenges/${id}`),
      api.get(`/challenges/${id}/ideas`),
      api.get(`/challenges/${id}/session`),
    ]);
    setChallenge(cRes.data);
    setIdeas(iRes.data);
    setSession(sRes.data);
  }, [id]);

  useEffect(() => {
    fetchAll();
  }, [fetchAll]);

  const handleApprove = async () => {
    setApproving(true);
    try {
      const res = await api.post(`/challenges/${id}/session/approve`);
      const updatedSession = res.data;
      setSession(updatedSession);
      if (updatedSession.status === 'approved_for_analysis' || updatedSession.status === 'analysis_in_progress' || updatedSession.status === 'analysis_complete') {
        navigate(`/challenges/${id}/analysis`);
      }
    } finally {
      setApproving(false);
    }
  };

  const handleDelete = async (ideaId: number) => {
    await api.delete(`/ideas/${ideaId}`);
    fetchAll();
  };

  const handleAcceptSuggestion = async (content: string) => {
    await api.post(`/challenges/${id}/ideas`, { content });
    fetchAll();
  };

  const handleAddCollaborator = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await api.post(`/challenges/${id}/collaborators`, { email: collabEmail });
      setCollabMsg(res.data.message);
      setCollabEmail('');
    } catch (err: unknown) {
      setCollabMsg(isAxiosError(err) && err.response?.data?.detail || 'Failed');
    }
  };

  if (!challenge) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600" />
      </div>
    );
  }

  const canAddIdeas = session?.status === 'ideate' || session?.status === 'build';

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-slate-900">
        <div className="max-w-5xl mx-auto px-4 py-4 flex items-center gap-4">
          <Link to="/" className="text-slate-400 hover:text-white transition-colors">&larr; Dashboard</Link>
          <h1 className="text-lg font-semibold text-white tracking-tight">{challenge.title}</h1>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 py-8 space-y-6">
        <div className="bg-white rounded-lg border border-slate-200/60 shadow-sm p-6">
          <p className="text-slate-600">{challenge.description}</p>
          <form onSubmit={handleAddCollaborator} className="mt-4 flex gap-2 items-end">
            <div className="flex-1">
              <label className="block text-xs font-medium text-slate-500 uppercase tracking-wider mb-1">
                Invite teammate by email
              </label>
              <input
                type="email"
                value={collabEmail}
                onChange={(e) => setCollabEmail(e.target.value)}
                placeholder="teammate@email.com"
                className="w-full px-3 py-2 border border-slate-300 rounded-md text-sm shadow-sm focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
              />
            </div>
            <button
              type="submit"
              className="px-3 py-2 bg-white border border-slate-300 text-slate-700 rounded-md hover:bg-slate-50 text-sm shadow-sm transition-colors"
            >
              Invite
            </button>
          </form>
          {collabMsg && (
            <p className="mt-2 text-sm text-emerald-600">{collabMsg}</p>
          )}
        </div>

        <SessionStatusBar
          session={session}
          ideaCount={ideas.length}
          currentUserId={user.id}
          onApprove={handleApprove}
          approving={approving}
        />

        {canAddIdeas && (
          <div className="space-y-4">
            <AddIdeaForm
              challengeId={challenge.id}
              sessionStatus={session?.status || 'ideate'}
              onIdeaAdded={fetchAll}
            />
            <AISuggestButton challengeId={challenge.id} onAccept={handleAcceptSuggestion} />
          </div>
        )}

        <div className="space-y-3">
          <h3 className="text-lg font-semibold text-slate-900">Ideas ({ideas.length})</h3>
          {ideas.length === 0 ? (
            <p className="text-slate-400 text-sm">No ideas yet. Be the first to share one!</p>
          ) : (
            <div className="grid gap-3 md:grid-cols-2">
              {ideas.map((idea) => (
                <IdeaCard
                  key={idea.id}
                  idea={idea}
                  currentUser={user}
                  onDelete={handleDelete}
                  canEdit={canAddIdeas}
                />
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
