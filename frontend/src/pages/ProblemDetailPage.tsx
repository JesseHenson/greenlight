import { useEffect, useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import api from '../api/client';
import type { Problem, BrainstormIdea, BrainstormSession, User } from '../types';
import IdeaCard from '../components/IdeaCard';
import AddIdeaForm from '../components/AddIdeaForm';
import SessionStatusBar from '../components/SessionStatusBar';
import AISuggestButton from '../components/AISuggestButton';

interface Props {
  user: User;
}

export default function ProblemDetailPage({ user }: Props) {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [problem, setProblem] = useState<Problem | null>(null);
  const [ideas, setIdeas] = useState<BrainstormIdea[]>([]);
  const [session, setSession] = useState<BrainstormSession | null>(null);
  const [approving, setApproving] = useState(false);
  const [collabEmail, setCollabEmail] = useState('');
  const [collabMsg, setCollabMsg] = useState('');

  const fetchAll = async () => {
    const [pRes, iRes, sRes] = await Promise.all([
      api.get(`/problems/${id}`),
      api.get(`/problems/${id}/ideas`),
      api.get(`/problems/${id}/session`),
    ]);
    setProblem(pRes.data);
    setIdeas(iRes.data);
    setSession(sRes.data);
  };

  useEffect(() => {
    fetchAll();
  }, [id]);

  const handleApprove = async () => {
    setApproving(true);
    try {
      const res = await api.post(`/problems/${id}/session/approve`);
      const updatedSession = res.data;
      setSession(updatedSession);
      if (updatedSession.status !== 'brainstorming') {
        navigate(`/problems/${id}/analysis`);
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
    await api.post(`/problems/${id}/ideas`, { content });
    fetchAll();
  };

  const handleAddCollaborator = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await api.post(`/problems/${id}/collaborators`, { email: collabEmail });
      setCollabMsg(res.data.message);
      setCollabEmail('');
    } catch (err: any) {
      setCollabMsg(err.response?.data?.detail || 'Failed');
    }
  };

  if (!problem) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600" />
      </div>
    );
  }

  const isBrainstorming = session?.status === 'brainstorming';

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-5xl mx-auto px-4 py-4 flex items-center gap-4">
          <Link to="/" className="text-gray-500 hover:text-gray-700">&larr; Dashboard</Link>
          <h1 className="text-xl font-bold text-gray-900">{problem.title}</h1>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 py-8 space-y-6">
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <p className="text-gray-700">{problem.description}</p>
          <form onSubmit={handleAddCollaborator} className="mt-4 flex gap-2 items-end">
            <div className="flex-1">
              <label className="block text-xs font-medium text-gray-500 mb-1">
                Add co-parent by email
              </label>
              <input
                type="email"
                value={collabEmail}
                onChange={(e) => setCollabEmail(e.target.value)}
                placeholder="coparent@email.com"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              />
            </div>
            <button
              type="submit"
              className="px-3 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 text-sm"
            >
              Invite
            </button>
          </form>
          {collabMsg && (
            <p className="mt-2 text-sm text-green-600">{collabMsg}</p>
          )}
        </div>

        <SessionStatusBar
          session={session}
          ideaCount={ideas.length}
          currentUserId={user.id}
          onApprove={handleApprove}
          approving={approving}
        />

        {isBrainstorming && (
          <div className="space-y-4">
            <AddIdeaForm problemId={problem.id} onIdeaAdded={fetchAll} />
            <AISuggestButton problemId={problem.id} onAccept={handleAcceptSuggestion} />
          </div>
        )}

        <div className="space-y-3">
          <h3 className="text-lg font-semibold text-gray-900">Ideas ({ideas.length})</h3>
          {ideas.length === 0 ? (
            <p className="text-gray-500 text-sm">No ideas yet. Be the first to share one!</p>
          ) : (
            <div className="grid gap-3 md:grid-cols-2">
              {ideas.map((idea) => (
                <IdeaCard
                  key={idea.id}
                  idea={idea}
                  currentUser={user}
                  onDelete={handleDelete}
                  isBrainstorming={isBrainstorming}
                />
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
