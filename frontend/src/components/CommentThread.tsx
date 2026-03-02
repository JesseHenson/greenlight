import { useCallback, useEffect, useRef, useState } from 'react';
import api from '../api/client';
import type { Comment, CreativityCheckResult } from '../types';

interface Props {
  ideaId: number;
}

export default function CommentThread({ ideaId }: Props) {
  const [comments, setComments] = useState<Comment[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [checkResult, setCheckResult] = useState<CreativityCheckResult | null>(null);
  const [pendingText, setPendingText] = useState('');
  const scrollRef = useRef<HTMLDivElement>(null);

  const fetchComments = useCallback(() => {
    api.get(`/ideas/${ideaId}/comments`).then((res) => setComments(res.data)).catch(() => {});
  }, [ideaId]);

  useEffect(() => {
    fetchComments();
  }, [fetchComments]);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [comments]);

  const postComment = async (text: string, toneFlag: boolean, suggestedAlt: string | null) => {
    await api.post(`/ideas/${ideaId}/comments`, {
      content: text,
      tone_flag: toneFlag,
      suggested_alternative: suggestedAlt,
    });
    setInput('');
    setCheckResult(null);
    setPendingText('');
    fetchComments();
  };

  const handleSend = async () => {
    const text = input.trim();
    if (!text || loading) return;

    setLoading(true);
    try {
      const checkRes = await api.post('/ai/check-creativity', { content: text, stage: 'build' });
      const check: CreativityCheckResult = checkRes.data;

      if (check.is_convergent) {
        setCheckResult(check);
        setPendingText(text);
        setLoading(false);
        return;
      }

      await postComment(text, false, null);
    } catch {
      // If check fails, post without it
      try {
        await postComment(text, false, null);
      } catch {
        // ignore post failure
      }
    } finally {
      setLoading(false);
    }
  };

  const useSuggestion = async () => {
    if (!checkResult?.suggested_alternative) return;
    setLoading(true);
    try {
      await postComment(checkResult.suggested_alternative, true, pendingText);
    } finally {
      setLoading(false);
    }
  };

  const postAnyway = async () => {
    setLoading(true);
    try {
      await postComment(pendingText, true, checkResult?.suggested_alternative || null);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div>
      <h4 className="text-sm font-semibold text-slate-700 mb-2">Discussion</h4>

      <div
        ref={scrollRef}
        className="max-h-60 overflow-y-auto space-y-3 mb-3"
      >
        {comments.length === 0 && (
          <p className="text-sm text-slate-400 italic">No comments yet. Start the discussion.</p>
        )}
        {comments.map((c) => (
          <div key={c.id} className="flex gap-2">
            <div className="w-7 h-7 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center text-xs font-bold flex-shrink-0 mt-0.5">
              {(c.creator_name || '?')[0].toUpperCase()}
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-baseline gap-2">
                <span className="text-sm font-medium text-slate-800">
                  {c.creator_name || 'Unknown'}
                </span>
                <span className="text-xs text-slate-400">
                  {new Date(c.created_at).toLocaleString()}
                </span>
                {c.tone_flag && (
                  <span className="text-xs px-1.5 py-0.5 bg-amber-100 text-amber-700 rounded">
                    Creativity-checked
                  </span>
                )}
              </div>
              <p className="text-sm text-slate-600 mt-0.5">{c.content}</p>
            </div>
          </div>
        ))}
      </div>

      {checkResult && (
        <div className="mb-3 bg-amber-50 border border-amber-200 rounded-md p-3">
          <p className="font-medium text-amber-800 text-sm">
            This looks like analysis — try building on ideas instead!
          </p>
          <p className="text-xs text-amber-700 mt-1">{checkResult.reason}</p>
          {checkResult.suggested_alternative && (
            <div className="mt-2">
              <p className="text-xs text-amber-700 font-medium">Try this instead:</p>
              <p className="text-xs text-amber-900 mt-1 italic">
                &ldquo;{checkResult.suggested_alternative}&rdquo;
              </p>
              <div className="flex gap-2 mt-2">
                <button
                  onClick={useSuggestion}
                  disabled={loading}
                  className="px-3 py-1 bg-amber-600 text-white rounded-md text-xs hover:bg-amber-700 disabled:opacity-50 transition-colors"
                >
                  Use Suggestion
                </button>
                <button
                  onClick={postAnyway}
                  disabled={loading}
                  className="px-3 py-1 bg-slate-100 text-slate-600 rounded-md text-xs hover:bg-slate-200 disabled:opacity-50 transition-colors"
                >
                  Post Anyway
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {!checkResult && (
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Add a comment..."
            className="flex-1 px-3 py-1.5 text-sm border border-slate-300 rounded-md shadow-sm focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
          />
          <button
            onClick={handleSend}
            disabled={loading || !input.trim()}
            className="px-3 py-1.5 bg-emerald-600 text-white rounded-md text-sm hover:bg-emerald-700 disabled:opacity-50 shadow-sm transition-colors"
          >
            {loading ? '...' : 'Send'}
          </button>
        </div>
      )}
    </div>
  );
}
