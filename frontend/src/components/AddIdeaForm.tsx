import { useState } from 'react';
import api from '../api/client';
import type { ToneCheckResult } from '../types';

interface Props {
  problemId: number;
  onIdeaAdded: () => void;
}

export default function AddIdeaForm({ problemId, onIdeaAdded }: Props) {
  const [content, setContent] = useState('');
  const [loading, setLoading] = useState(false);
  const [toneResult, setToneResult] = useState<ToneCheckResult | null>(null);

  const submitIdea = async (text: string) => {
    setLoading(true);
    try {
      // Check tone first
      const toneRes = await api.post('/ai/check-tone', { content: text });
      const tone: ToneCheckResult = toneRes.data;

      if (tone.is_hostile) {
        setToneResult(tone);
        // Still save the idea but flagged
        await api.post(`/problems/${problemId}/ideas`, { content: text });
        onIdeaAdded();
        return;
      }

      await api.post(`/problems/${problemId}/ideas`, { content: text });
      setContent('');
      setToneResult(null);
      onIdeaAdded();
    } catch (err: any) {
      // If AI check fails, submit without tone check
      if (err.response?.status !== 400) {
        try {
          await api.post(`/problems/${problemId}/ideas`, { content: text });
          setContent('');
          setToneResult(null);
          onIdeaAdded();
        } catch {
          // ignore
        }
      }
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!content.trim()) return;
    submitIdea(content);
  };

  const useSuggestion = () => {
    if (toneResult?.suggested_alternative) {
      setContent(toneResult.suggested_alternative);
      setToneResult(null);
    }
  };

  const keepOriginal = () => {
    setContent('');
    setToneResult(null);
  };

  return (
    <div>
      {toneResult && (
        <div className="mb-4 bg-amber-50 border border-amber-200 rounded-lg p-4">
          <p className="font-medium text-amber-800">
            Your message may come across as confrontational
          </p>
          <p className="text-sm text-amber-700 mt-1">{toneResult.reason}</p>
          {toneResult.suggested_alternative && (
            <div className="mt-3">
              <p className="text-sm text-amber-700 font-medium">Suggested alternative:</p>
              <p className="text-sm text-amber-900 mt-1 italic">
                "{toneResult.suggested_alternative}"
              </p>
              <div className="flex gap-2 mt-3">
                <button
                  onClick={useSuggestion}
                  className="px-3 py-1 bg-amber-600 text-white rounded text-sm hover:bg-amber-700"
                >
                  Use Suggestion
                </button>
                <button
                  onClick={keepOriginal}
                  className="px-3 py-1 bg-gray-200 text-gray-700 rounded text-sm hover:bg-gray-300"
                >
                  Dismiss
                </button>
              </div>
            </div>
          )}
        </div>
      )}
      <form onSubmit={handleSubmit} className="flex gap-2">
        <textarea
          value={content}
          onChange={(e) => setContent(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              if (content.trim() && !loading) handleSubmit(e);
            }
          }}
          placeholder="Share an idea... Focus on solutions, not blame. (Shift+Enter for new line)"
          rows={2}
          className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 resize-none"
        />
        <button
          type="submit"
          disabled={loading || !content.trim()}
          className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 self-end"
        >
          {loading ? '...' : 'Add'}
        </button>
      </form>
    </div>
  );
}
