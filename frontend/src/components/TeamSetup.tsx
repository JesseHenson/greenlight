import { useState } from 'react';
import api from '../api/client';
import type { Team } from '../types';

interface Props {
  onTeamCreated: (team: Team) => void;
}

export default function TeamSetup({ onTeamCreated }: Props) {
  const [step, setStep] = useState<'prompt' | 'create' | 'invite' | 'sent'>('prompt');
  const [teamName, setTeamName] = useState('');
  const [inviteEmail, setInviteEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [createdTeam, setCreatedTeam] = useState<Team | null>(null);
  const [, setInviteStatus] = useState<'added' | 'invited' | null>(null);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const res = await api.post('/teams', { name: teamName || 'My Team' });
      setCreatedTeam(res.data);
      setStep('invite');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create team');
    } finally {
      setLoading(false);
    }
  };

  const handleInvite = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!createdTeam) return;
    setLoading(true);
    setError('');
    try {
      const res = await api.post(`/teams/${createdTeam.id}/invite`, { email: inviteEmail });
      setInviteStatus(res.data.status);
      if (res.data.status === 'added') {
        const teamRes = await api.get(`/teams/${createdTeam.id}`);
        onTeamCreated(teamRes.data);
      } else {
        setStep('sent');
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to invite');
    } finally {
      setLoading(false);
    }
  };

  const handleSkip = () => {
    if (createdTeam) {
      onTeamCreated(createdTeam);
    }
  };

  if (step === 'prompt') {
    return (
      <div className="bg-emerald-50/50 border border-emerald-200/60 rounded-lg p-6 mb-6">
        <div className="flex items-start gap-4">
          <div className="text-3xl">&#9889;</div>
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-emerald-800">Create your team</h3>
            <p className="text-emerald-600 mt-1 text-sm">
              Set up a team to automatically share all challenges with your teammates.
              No more inviting per-challenge.
            </p>
            <button
              onClick={() => setStep('create')}
              className="mt-3 px-4 py-2 bg-emerald-600 text-white rounded-md hover:bg-emerald-700 font-medium text-sm shadow-sm transition-colors"
            >
              Set Up Team
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (step === 'create') {
    return (
      <div className="bg-white border border-slate-200/60 rounded-lg shadow-sm p-6 mb-6">
        <h3 className="text-lg font-semibold text-slate-900 mb-4">Create your team</h3>
        <form onSubmit={handleCreate} className="space-y-4">
          {error && <div className="bg-red-50 text-red-700 p-3 rounded-md text-sm">{error}</div>}
          <div>
            <label className="block text-xs font-medium text-slate-500 uppercase tracking-wider mb-1">
              Team name (optional)
            </label>
            <input
              type="text"
              value={teamName}
              onChange={(e) => setTeamName(e.target.value)}
              placeholder="e.g., My Team"
              className="w-full px-3 py-2 border border-slate-300 rounded-md shadow-sm focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
            />
          </div>
          <div className="flex gap-3">
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-2 bg-emerald-600 text-white rounded-md hover:bg-emerald-700 disabled:opacity-50 font-medium text-sm shadow-sm transition-colors"
            >
              {loading ? 'Creating...' : 'Create Team'}
            </button>
            <button
              type="button"
              onClick={() => setStep('prompt')}
              className="px-4 py-2 text-slate-600 bg-slate-100 rounded-md hover:bg-slate-200 text-sm transition-colors"
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
      <div className="bg-emerald-50/50 border border-emerald-200/60 rounded-lg p-6 mb-6">
        <h3 className="text-lg font-semibold text-emerald-800 mb-1">Invitation sent!</h3>
        <p className="text-emerald-600 text-sm mb-3">
          We sent an email to <strong>{inviteEmail}</strong> with a link to sign up.
          They'll automatically join your team when they create their account.
        </p>
        <button
          onClick={() => { if (createdTeam) onTeamCreated(createdTeam); }}
          className="px-4 py-2 bg-emerald-600 text-white rounded-md hover:bg-emerald-700 font-medium text-sm shadow-sm transition-colors"
        >
          Continue to Dashboard
        </button>
      </div>
    );
  }

  // step === 'invite'
  return (
    <div className="bg-white border border-slate-200/60 rounded-lg shadow-sm p-6 mb-6">
      <h3 className="text-lg font-semibold text-slate-900 mb-1">Invite a teammate</h3>
      <p className="text-sm text-slate-500 mb-4">
        Enter their email address. We'll send them an invite to join.
      </p>
      <form onSubmit={handleInvite} className="space-y-4">
        {error && <div className="bg-red-50 text-red-700 p-3 rounded-md text-sm">{error}</div>}
        <div>
          <input
            type="email"
            value={inviteEmail}
            onChange={(e) => setInviteEmail(e.target.value)}
            required
            placeholder="teammate@email.com"
            className="w-full px-3 py-2 border border-slate-300 rounded-md shadow-sm focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
          />
        </div>
        <div className="flex gap-3">
          <button
            type="submit"
            disabled={loading}
            className="px-4 py-2 bg-emerald-600 text-white rounded-md hover:bg-emerald-700 disabled:opacity-50 font-medium text-sm shadow-sm transition-colors"
          >
            {loading ? 'Sending...' : 'Send Invite'}
          </button>
          <button
            type="button"
            onClick={handleSkip}
            className="px-4 py-2 text-slate-600 bg-slate-100 rounded-md hover:bg-slate-200 text-sm transition-colors"
          >
            Skip for now
          </button>
        </div>
      </form>
    </div>
  );
}
