import { useState } from 'react';
import api from '../api/client';
import type { ParentGroup } from '../types';

interface Props {
  onGroupCreated: (group: ParentGroup) => void;
}

export default function GroupSetup({ onGroupCreated }: Props) {
  const [step, setStep] = useState<'prompt' | 'create' | 'invite' | 'sent'>('prompt');
  const [groupName, setGroupName] = useState('');
  const [inviteEmail, setInviteEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [createdGroup, setCreatedGroup] = useState<ParentGroup | null>(null);
  const [, setInviteStatus] = useState<'added' | 'invited' | null>(null);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const res = await api.post('/groups', { name: groupName || 'Our Family' });
      setCreatedGroup(res.data);
      setStep('invite');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create group');
    } finally {
      setLoading(false);
    }
  };

  const handleInvite = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!createdGroup) return;
    setLoading(true);
    setError('');
    try {
      const res = await api.post(`/groups/${createdGroup.id}/invite`, { email: inviteEmail });
      setInviteStatus(res.data.status);
      if (res.data.status === 'added') {
        // User was already registered — refresh and go to dashboard
        const groupRes = await api.get(`/groups/${createdGroup.id}`);
        onGroupCreated(groupRes.data);
      } else {
        // Invitation sent — show confirmation
        setStep('sent');
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to invite');
    } finally {
      setLoading(false);
    }
  };

  const handleSkip = () => {
    if (createdGroup) {
      onGroupCreated(createdGroup);
    }
  };

  if (step === 'prompt') {
    return (
      <div className="bg-indigo-50 border border-indigo-200 rounded-xl p-6 mb-6">
        <div className="flex items-start gap-4">
          <div className="text-3xl">👨‍👩‍👧‍👦</div>
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-indigo-900">Connect with your co-parent</h3>
            <p className="text-indigo-700 mt-1 text-sm">
              Create a parent group to automatically share all conversations with your co-parent.
              No more inviting per-conversation.
            </p>
            <button
              onClick={() => setStep('create')}
              className="mt-3 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 font-medium text-sm"
            >
              Set Up Group
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (step === 'create') {
    return (
      <div className="bg-white border border-gray-200 rounded-xl p-6 mb-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Create your parent group</h3>
        <form onSubmit={handleCreate} className="space-y-4">
          {error && <div className="bg-red-50 text-red-700 p-3 rounded-lg text-sm">{error}</div>}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Group name (optional)
            </label>
            <input
              type="text"
              value={groupName}
              onChange={(e) => setGroupName(e.target.value)}
              placeholder="e.g., Our Family"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            />
          </div>
          <div className="flex gap-3">
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 font-medium text-sm"
            >
              {loading ? 'Creating...' : 'Create Group'}
            </button>
            <button
              type="button"
              onClick={() => setStep('prompt')}
              className="px-4 py-2 text-gray-600 bg-gray-100 rounded-lg hover:bg-gray-200 text-sm"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    );
  }

  if (step === 'sent') {
    return (
      <div className="bg-green-50 border border-green-200 rounded-xl p-6 mb-6">
        <h3 className="text-lg font-semibold text-green-900 mb-1">Invitation sent!</h3>
        <p className="text-green-700 text-sm mb-3">
          We sent an email to <strong>{inviteEmail}</strong> with a link to sign up.
          They'll automatically join your group when they create their account.
        </p>
        <button
          onClick={() => { if (createdGroup) onGroupCreated(createdGroup); }}
          className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 font-medium text-sm"
        >
          Continue to Dashboard
        </button>
      </div>
    );
  }

  // step === 'invite'
  return (
    <div className="bg-white border border-gray-200 rounded-xl p-6 mb-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-1">Invite your co-parent</h3>
      <p className="text-sm text-gray-500 mb-4">
        Enter their email address. We'll send them an invite to join.
      </p>
      <form onSubmit={handleInvite} className="space-y-4">
        {error && <div className="bg-red-50 text-red-700 p-3 rounded-lg text-sm">{error}</div>}
        <div>
          <input
            type="email"
            value={inviteEmail}
            onChange={(e) => setInviteEmail(e.target.value)}
            required
            placeholder="co-parent@email.com"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
          />
        </div>
        <div className="flex gap-3">
          <button
            type="submit"
            disabled={loading}
            className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 font-medium text-sm"
          >
            {loading ? 'Sending...' : 'Send Invite'}
          </button>
          <button
            type="button"
            onClick={handleSkip}
            className="px-4 py-2 text-gray-600 bg-gray-100 rounded-lg hover:bg-gray-200 text-sm"
          >
            Skip for now
          </button>
        </div>
      </form>
    </div>
  );
}
