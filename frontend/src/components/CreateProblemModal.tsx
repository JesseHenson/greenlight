import { useState } from 'react';
import api from '../api/client';

interface Props {
  groupId: number | null;
  onCreated: () => void;
  onClose: () => void;
}

export default function CreateProblemModal({ groupId, onCreated, onClose }: Props) {
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
      await api.post('/problems', payload);
      onCreated();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create problem');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-lg max-w-lg w-full p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Start a Conversation</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <div className="bg-red-50 text-red-700 p-3 rounded-lg text-sm">{error}</div>
          )}
          {groupId && (
            <div className="bg-indigo-50 text-indigo-700 p-3 rounded-lg text-sm">
              This conversation will be automatically shared with your co-parent group.
            </div>
          )}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              What's the issue?
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              required
              placeholder="e.g., Holiday schedule for next year"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Describe the situation
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              required
              rows={4}
              placeholder="Provide context about the problem so both parents and AI can brainstorm better solutions..."
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            />
          </div>
          <div className="flex justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50"
            >
              {loading ? 'Starting...' : 'Start Conversation'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
