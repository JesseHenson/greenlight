import { useEffect, useState } from 'react';
import { UserButton } from '@clerk/clerk-react';
import api from '../api/client';
import type { Problem, User, ParentGroup } from '../types';
import ProblemCard from '../components/ProblemCard';
import CreateProblemModal from '../components/CreateProblemModal';
import GroupSetup from '../components/GroupSetup';
import GroupSettingsModal from '../components/GroupSettingsModal';

interface Props {
  user: User;
}

export default function DashboardPage({ user }: Props) {
  const [problems, setProblems] = useState<Problem[]>([]);
  const [showCreate, setShowCreate] = useState(false);
  const [loading, setLoading] = useState(true);
  const [group, setGroup] = useState<ParentGroup | null>(null);
  const [groupLoading, setGroupLoading] = useState(true);
  const [showGroupSettings, setShowGroupSettings] = useState(false);

  const fetchProblems = async () => {
    try {
      const res = await api.get('/problems');
      setProblems(res.data);
    } finally {
      setLoading(false);
    }
  };

  const fetchGroups = async () => {
    try {
      const res = await api.get('/groups');
      if (res.data.length > 0) {
        setGroup(res.data[0]);
      }
    } finally {
      setGroupLoading(false);
    }
  };

  useEffect(() => {
    fetchProblems();
    fetchGroups();
  }, []);

  const handleArchive = async (problemId: number) => {
    try {
      await api.post(`/problems/${problemId}/archive`);
      fetchProblems();
    } catch {
      // ignore
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-5xl mx-auto px-4 py-4 flex items-center justify-between">
          <h1 className="text-xl font-bold text-gray-900">CommonGround</h1>
          <div className="flex items-center gap-4">
            {group && (
              <button
                onClick={() => setShowGroupSettings(true)}
                className="flex items-center gap-2 px-2 py-1 rounded-lg hover:bg-gray-100 transition-colors"
                title="Group settings"
              >
                <span className="text-xs text-gray-400 uppercase tracking-wide">{group.name || 'Group'}</span>
                <div className="flex -space-x-2">
                  {group.members.map((m) => (
                    <div
                      key={m.user_id}
                      title={m.user_name}
                      className="w-7 h-7 rounded-full bg-indigo-100 border-2 border-white flex items-center justify-center text-xs font-medium text-indigo-700"
                    >
                      {m.user_name.charAt(0).toUpperCase()}
                    </div>
                  ))}
                </div>
              </button>
            )}
            <span className="text-sm text-gray-600">{user.name}</span>
            <UserButton />
          </div>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 py-8">
        {!groupLoading && !group && (
          <GroupSetup onGroupCreated={(g) => setGroup(g)} />
        )}

        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold text-gray-900">Conversations</h2>
          <button
            onClick={() => setShowCreate(true)}
            className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 font-medium"
          >
            + Start a Conversation
          </button>
        </div>

        {loading ? (
          <div className="text-center py-12 text-gray-500">Loading...</div>
        ) : problems.length === 0 ? (
          <div className="text-center py-12 bg-white rounded-xl border border-gray-200">
            <p className="text-gray-500 mb-4">No conversations yet. Start one to begin brainstorming!</p>
            <button
              onClick={() => setShowCreate(true)}
              className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
            >
              Start Your First Conversation
            </button>
          </div>
        ) : (
          <div className="grid gap-4 md:grid-cols-2">
            {problems.map((p) => (
              <ProblemCard key={p.id} problem={p} onArchive={handleArchive} />
            ))}
          </div>
        )}
      </main>

      {showCreate && (
        <CreateProblemModal
          groupId={group?.id ?? null}
          onCreated={() => {
            setShowCreate(false);
            fetchProblems();
          }}
          onClose={() => setShowCreate(false)}
        />
      )}

      {showGroupSettings && group && (
        <GroupSettingsModal
          group={group}
          onClose={() => setShowGroupSettings(false)}
          onGroupUpdated={(updated) => setGroup(updated)}
        />
      )}
    </div>
  );
}
