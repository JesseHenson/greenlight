import { useState } from 'react';
import { isAxiosError } from 'axios';
import api from '../api/client';

interface Props {
  groupId: number | null;
  onCreated: () => void;
  onClose: () => void;
}

export default function CreateChallengeModal({ groupId, onCreated, onClose }: Props) {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const payload: { title: string; description: string; group_id?: number } = { title, description };
      if (groupId) {
        payload.group_id = groupId;
      }
      await api.post('/challenges', payload);
      onCreated();
    } catch (err: unknown) {
      setError(isAxiosError(err) && err.response?.data?.detail || 'Failed to create challenge');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-slate-900/60 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-xl border border-slate-200/60 max-w-lg w-full p-6">
        <h2 className="text-xl font-semibold text-slate-900 mb-4">New Challenge</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <div className="bg-red-50 text-red-700 p-3 rounded-md text-sm">{error}</div>
          )}
          {groupId && (
            <div className="bg-emerald-50/50 text-emerald-700 p-3 rounded-md text-sm border border-emerald-200/60">
              This challenge will be automatically shared with your team.
            </div>
          )}
          <div>
            <label className="block text-xs font-medium text-slate-500 uppercase tracking-wider mb-1">
              What's the challenge?
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              required
              placeholder="e.g., How might we reduce meeting fatigue?"
              className="w-full px-3 py-2 border border-slate-300 rounded-md shadow-sm focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-500 uppercase tracking-wider mb-1">
              Describe the challenge
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              required
              rows={4}
              placeholder="Provide context about the challenge so the team and AI can brainstorm better solutions..."
              className="w-full px-3 py-2 border border-slate-300 rounded-md shadow-sm focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
            />
          </div>
          <div className="flex justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 bg-white border border-slate-300 text-slate-700 rounded-md hover:bg-slate-50 shadow-sm transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-2 bg-emerald-600 text-white rounded-md hover:bg-emerald-700 disabled:opacity-50 shadow-sm transition-colors"
            >
              {loading ? 'Creating...' : 'Create Challenge'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
