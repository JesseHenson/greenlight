import { useState } from 'react';
import api from '../api/client';
import type { CreativityCheckResult } from '../types';

interface Props {
  challengeId: number;
  sessionStatus: string;
  onIdeaAdded: () => void;
}

export default function AddIdeaForm({ challengeId, sessionStatus, onIdeaAdded }: Props) {
  const [content, setContent] = useState('');
  const [loading, setLoading] = useState(false);
  const [checkResult, setCheckResult] = useState<CreativityCheckResult | null>(null);

  const submitIdea = async (text: string) => {
    setLoading(true);
    try {
      // Check creativity first
      const checkRes = await api.post('/ai/check-creativity', {
        content: text,
        stage: sessionStatus,
      });
      const check: CreativityCheckResult = checkRes.data;

      if (check.is_convergent) {
        setCheckResult(check);
        // Still save the idea but flagged
        await api.post(`/challenges/${challengeId}/ideas`, { content: text });
        onIdeaAdded();
        return;
      }

      await api.post(`/challenges/${challengeId}/ideas`, { content: text });
      setContent('');
      setCheckResult(null);
      onIdeaAdded();
    } catch (err: any) {
      // If AI check fails, submit without check
      if (err.response?.status !== 400) {
        try {
          await api.post(`/challenges/${challengeId}/ideas`, { content: text });
          setContent('');
          setCheckResult(null);
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
    if (checkResult?.suggested_alternative) {
      setContent(checkResult.suggested_alternative);
      setCheckResult(null);
    }
  };

  const keepOriginal = () => {
    setContent('');
    setCheckResult(null);
  };

  const placeholder = sessionStatus === 'build'
    ? 'Build on an idea... Try "Yes, and..." (Shift+Enter for new line)'
    : 'Share a wild idea... No judgment here! (Shift+Enter for new line)';

  return (
    <div>
      {checkResult && (
        <div className="mb-4 bg-amber-50 border border-amber-200 rounded-md p-4">
          <p className="font-medium text-amber-800">
            This looks like analysis — try building on ideas instead!
          </p>
          <p className="text-sm text-amber-700 mt-1">{checkResult.reason}</p>
          {checkResult.suggested_alternative && (
            <div className="mt-3">
              <p className="text-sm text-amber-700 font-medium">Try this instead:</p>
              <p className="text-sm text-amber-900 mt-1 italic">
                "{checkResult.suggested_alternative}"
              </p>
              <div className="flex gap-2 mt-3">
                <button
                  onClick={useSuggestion}
                  className="px-3 py-1 bg-amber-600 text-white rounded-md text-sm hover:bg-amber-700 transition-colors"
                >
                  Use Suggestion
                </button>
                <button
                  onClick={keepOriginal}
                  className="px-3 py-1 bg-slate-100 text-slate-600 rounded-md text-sm hover:bg-slate-200 transition-colors"
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
          placeholder={placeholder}
          rows={2}
          className="flex-1 px-3 py-2 border border-slate-300 rounded-md shadow-sm focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 resize-none"
        />
        <button
          type="submit"
          disabled={loading || !content.trim()}
          className="px-4 py-2 bg-emerald-600 text-white rounded-md hover:bg-emerald-700 disabled:opacity-50 self-end shadow-sm transition-colors"
        >
          {loading ? '...' : 'Add'}
        </button>
      </form>
    </div>
  );
}
