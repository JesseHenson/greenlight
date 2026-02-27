import { useEffect, useState } from 'react';
import api from '../api/client';
import type { ParentGroup } from '../types';

interface PendingInvite {
  id: number;
  email: string;
  created_at: string;
}

interface Props {
  group: ParentGroup;
  onClose: () => void;
  onGroupUpdated: (group: ParentGroup) => void;
}

export default function GroupSettingsModal({ group, onClose, onGroupUpdated }: Props) {
  const [groupName, setGroupName] = useState(group.name);
  const [inviteEmail, setInviteEmail] = useState('');
  const [pendingInvites, setPendingInvites] = useState<PendingInvite[]>([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [editingName, setEditingName] = useState(false);

  useEffect(() => {
    fetchPendingInvites();
  }, []);

  const fetchPendingInvites = async () => {
    try {
      const res = await api.get(`/groups/${group.id}/pending-invites`);
      setPendingInvites(res.data);
    } catch {
      // ignore
    }
  };

  const handleUpdateName = async () => {
    setLoading(true);
    setError('');
    try {
      await api.patch(`/groups/${group.id}`, { name: groupName });
      onGroupUpdated({ ...group, name: groupName });
      setEditingName(false);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to update');
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
      const res = await api.post(`/groups/${group.id}/invite`, { email: inviteEmail });
      setMessage(res.data.message);
      setInviteEmail('');
      if (res.data.status === 'added') {
        const groupRes = await api.get(`/groups/${group.id}`);
        onGroupUpdated(groupRes.data);
      } else {
        fetchPendingInvites();
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to invite');
    } finally {
      setLoading(false);
    }
  };

  const handleCancelInvite = async (inviteId: number) => {
    try {
      await api.delete(`/groups/${group.id}/pending-invites/${inviteId}`);
      fetchPendingInvites();
    } catch {
      // ignore
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-lg max-w-md w-full p-6 max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-5">
          <h2 className="text-lg font-semibold text-gray-900">Group Settings</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl leading-none">&times;</button>
        </div>

        {error && <div className="bg-red-50 text-red-700 p-3 rounded-lg text-sm mb-4">{error}</div>}
        {message && <div className="bg-green-50 text-green-700 p-3 rounded-lg text-sm mb-4">{message}</div>}

        {/* Group Name */}
        <div className="mb-6">
          <label className="block text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">Group Name</label>
          {editingName ? (
            <div className="flex gap-2">
              <input
                type="text"
                value={groupName}
                onChange={(e) => setGroupName(e.target.value)}
                className="flex-1 px-3 py-1.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              />
              <button
                onClick={handleUpdateName}
                disabled={loading}
                className="px-3 py-1.5 bg-indigo-600 text-white rounded-lg text-sm hover:bg-indigo-700 disabled:opacity-50"
              >
                Save
              </button>
              <button
                onClick={() => { setEditingName(false); setGroupName(group.name); }}
                className="px-3 py-1.5 text-gray-600 bg-gray-100 rounded-lg text-sm hover:bg-gray-200"
              >
                Cancel
              </button>
            </div>
          ) : (
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-900">{group.name || 'Unnamed group'}</span>
              <button
                onClick={() => setEditingName(true)}
                className="text-xs text-indigo-600 hover:text-indigo-700"
              >
                Edit
              </button>
            </div>
          )}
        </div>

        {/* Members */}
        <div className="mb-6">
          <label className="block text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">Members</label>
          <div className="space-y-2">
            {group.members.map((m) => (
              <div key={m.user_id} className="flex items-center gap-3 p-2 bg-gray-50 rounded-lg">
                <div className="w-8 h-8 rounded-full bg-indigo-100 flex items-center justify-center text-sm font-medium text-indigo-700">
                  {m.user_name.charAt(0).toUpperCase()}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium text-gray-900 truncate">{m.user_name}</div>
                  <div className="text-xs text-gray-500 truncate">{m.email}</div>
                </div>
                <span className="text-xs text-gray-400 capitalize">{m.role}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Pending Invites */}
        {pendingInvites.length > 0 && (
          <div className="mb-6">
            <label className="block text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">Pending Invites</label>
            <div className="space-y-2">
              {pendingInvites.map((inv) => (
                <div key={inv.id} className="flex items-center gap-3 p-2 bg-amber-50 rounded-lg">
                  <div className="w-8 h-8 rounded-full bg-amber-100 flex items-center justify-center text-sm text-amber-700">
                    ?
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-sm text-gray-900 truncate">{inv.email}</div>
                    <div className="text-xs text-gray-500">Invite sent</div>
                  </div>
                  <button
                    onClick={() => handleCancelInvite(inv.id)}
                    className="text-xs text-red-500 hover:text-red-700"
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
          <label className="block text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">Invite Co-Parent</label>
          <form onSubmit={handleInvite} className="flex gap-2">
            <input
              type="email"
              value={inviteEmail}
              onChange={(e) => setInviteEmail(e.target.value)}
              required
              placeholder="email@example.com"
              className="flex-1 px-3 py-1.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            />
            <button
              type="submit"
              disabled={loading}
              className="px-3 py-1.5 bg-indigo-600 text-white rounded-lg text-sm hover:bg-indigo-700 disabled:opacity-50"
            >
              {loading ? 'Sending...' : 'Invite'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
