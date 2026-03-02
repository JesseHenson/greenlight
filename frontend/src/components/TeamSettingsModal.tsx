import { useCallback, useEffect, useState } from 'react';
import { isAxiosError } from 'axios';
import api from '../api/client';
import type { Team } from '../types';

interface PendingInvite {
  id: number;
  email: string;
  created_at: string;
}

interface Props {
  team: Team;
  onClose: () => void;
  onTeamUpdated: (team: Team) => void;
}

export default function TeamSettingsModal({ team, onClose, onTeamUpdated }: Props) {
  const [teamName, setTeamName] = useState(team.name);
  const [inviteEmail, setInviteEmail] = useState('');
  const [pendingInvites, setPendingInvites] = useState<PendingInvite[]>([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [editingName, setEditingName] = useState(false);

  const fetchPendingInvites = useCallback(async () => {
    try {
      const res = await api.get(`/teams/${team.id}/pending-invites`);
      setPendingInvites(res.data);
    } catch {
      // ignore
    }
  }, [team.id]);

  useEffect(() => {
    fetchPendingInvites();
  }, [fetchPendingInvites]);

  const handleUpdateName = async () => {
    setLoading(true);
    setError('');
    try {
      await api.patch(`/teams/${team.id}`, { name: teamName });
      onTeamUpdated({ ...team, name: teamName });
      setEditingName(false);
    } catch (err: unknown) {
      setError(isAxiosError(err) && err.response?.data?.detail || 'Failed to update');
    } finally {
      setLoading(false);
    }
  };

  const handleInvite = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setMessage('');
    try {
      const res = await api.post(`/teams/${team.id}/invite`, { email: inviteEmail });
      setMessage(res.data.message);
      setInviteEmail('');
      if (res.data.status === 'added') {
        const teamRes = await api.get(`/teams/${team.id}`);
        onTeamUpdated(teamRes.data);
      } else {
        fetchPendingInvites();
      }
    } catch (err: unknown) {
      setError(isAxiosError(err) && err.response?.data?.detail || 'Failed to invite');
    } finally {
      setLoading(false);
    }
  };

  const handleCancelInvite = async (inviteId: number) => {
    try {
      await api.delete(`/teams/${team.id}/pending-invites/${inviteId}`);
      fetchPendingInvites();
    } catch {
      // ignore
    }
  };

  return (
    <div className="fixed inset-0 bg-slate-900/60 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-xl border border-slate-200/60 max-w-md w-full p-6 max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-5">
          <h2 className="text-lg font-semibold text-slate-900">Team Settings</h2>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600 text-xl leading-none transition-colors">&times;</button>
        </div>

        {error && <div className="bg-red-50 text-red-700 p-3 rounded-md text-sm mb-4">{error}</div>}
        {message && <div className="bg-emerald-50 text-emerald-700 p-3 rounded-md text-sm mb-4">{message}</div>}

        {/* Team Name */}
        <div className="mb-6">
          <label className="block text-xs font-medium text-slate-500 uppercase tracking-wider mb-2">Team Name</label>
          {editingName ? (
            <div className="flex gap-2">
              <input
                type="text"
                value={teamName}
                onChange={(e) => setTeamName(e.target.value)}
                className="flex-1 px-3 py-1.5 border border-slate-300 rounded-md text-sm shadow-sm focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
              />
              <button
                onClick={handleUpdateName}
                disabled={loading}
                className="px-3 py-1.5 bg-emerald-600 text-white rounded-md text-sm hover:bg-emerald-700 disabled:opacity-50 shadow-sm transition-colors"
              >
                Save
              </button>
              <button
                onClick={() => { setEditingName(false); setTeamName(team.name); }}
                className="px-3 py-1.5 text-slate-600 bg-slate-100 rounded-md text-sm hover:bg-slate-200 transition-colors"
              >
                Cancel
              </button>
            </div>
          ) : (
            <div className="flex items-center gap-2">
              <span className="text-sm text-slate-900">{team.name || 'Unnamed team'}</span>
              <button
                onClick={() => setEditingName(true)}
                className="text-xs text-emerald-600 hover:text-emerald-700 transition-colors"
              >
                Edit
              </button>
            </div>
          )}
        </div>

        {/* Members */}
        <div className="mb-6">
          <label className="block text-xs font-medium text-slate-500 uppercase tracking-wider mb-2">Members</label>
          <div className="space-y-2">
            {team.members.map((m) => (
              <div key={m.user_id} className="flex items-center gap-3 p-2 bg-slate-50 rounded-md">
                <div className="w-8 h-8 rounded-full bg-emerald-100 flex items-center justify-center text-sm font-medium text-emerald-700">
                  {m.user_name.charAt(0).toUpperCase()}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium text-slate-900 truncate">{m.user_name}</div>
                  <div className="text-xs text-slate-500 truncate">{m.email}</div>
                </div>
                <span className="text-xs text-slate-400 capitalize">{m.role}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Pending Invites */}
        {pendingInvites.length > 0 && (
          <div className="mb-6">
            <label className="block text-xs font-medium text-slate-500 uppercase tracking-wider mb-2">Pending Invites</label>
            <div className="space-y-2">
              {pendingInvites.map((inv) => (
                <div key={inv.id} className="flex items-center gap-3 p-2 bg-amber-50 rounded-md">
                  <div className="w-8 h-8 rounded-full bg-amber-100 flex items-center justify-center text-sm text-amber-700">
                    ?
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-sm text-slate-900 truncate">{inv.email}</div>
                    <div className="text-xs text-slate-500">Invite sent</div>
                  </div>
                  <button
                    onClick={() => handleCancelInvite(inv.id)}
                    className="text-xs text-red-500 hover:text-red-700 transition-colors"
                  >
                    Cancel
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Invite Form */}
        <div>
          <label className="block text-xs font-medium text-slate-500 uppercase tracking-wider mb-2">Invite Teammate</label>
          <form onSubmit={handleInvite} className="flex gap-2">
            <input
              type="email"
              value={inviteEmail}
              onChange={(e) => setInviteEmail(e.target.value)}
              required
              placeholder="email@example.com"
              className="flex-1 px-3 py-1.5 border border-slate-300 rounded-md text-sm shadow-sm focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
            />
            <button
              type="submit"
              disabled={loading}
              className="px-3 py-1.5 bg-emerald-600 text-white rounded-md text-sm hover:bg-emerald-700 disabled:opacity-50 shadow-sm transition-colors"
            >
              {loading ? 'Sending...' : 'Invite'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
