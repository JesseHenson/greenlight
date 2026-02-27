import { useEffect, useRef, useState } from 'react';
import api from '../api/client';
import type { Comment, ToneCheckResult } from '../types';

interface Props {
  ideaId: number;
}

export default function CommentThread({ ideaId }: Props) {
  const [comments, setComments] = useState<Comment[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [toneResult, setToneResult] = useState<ToneCheckResult | null>(null);
  const [pendingText, setPendingText] = useState('');
  const scrollRef = useRef<HTMLDivElement>(null);

  const fetchComments = () => {
    api.get(`/ideas/${ideaId}/comments`).then((res) => setComments(res.data)).catch(() => {});
  };

  useEffect(() => {
    fetchComments();
  }, [ideaId]);

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
    setToneResult(null);
    setPendingText('');
    fetchComments();
  };

  const handleSend = async () => {
    const text = input.trim();
    if (!text || loading) return;

    setLoading(true);
    try {
      const toneRes = await api.post('/ai/check-tone', { content: text });
      const tone: ToneCheckResult = toneRes.data;

      if (tone.is_hostile) {
        setToneResult(tone);
        setPendingText(text);
        setLoading(false);
        return;
      }

      await postComment(text, false, null);
    } catch {
      // If tone check fails, post without it
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
    if (!toneResult?.suggested_alternative) return;
    setLoading(true);
    try {
      await postComment(toneResult.suggested_alternative, true, pendingText);
    } finally {
      setLoading(false);
    }
  };

  const postAnyway = async () => {
    setLoading(true);
    try {
      await postComment(pendingText, true, toneResult?.suggested_alternative || null);
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
      <h4 className="text-sm font-semibold text-gray-700 mb-2">Discussion</h4>

      <div
        ref={scrollRef}
        className="max-h-60 overflow-y-auto space-y-3 mb-3"
      >
        {comments.length === 0 && (
          <p className="text-sm text-gray-400 italic">No comments yet. Start the discussion.</p>
        )}
        {comments.map((c) => (
          <div key={c.id} className="flex gap-2">
            <div className="w-7 h-7 rounded-full bg-indigo-100 text-indigo-700 flex items-center justify-center text-xs font-bold flex-shrink-0 mt-0.5">
              {(c.creator_name || '?')[0].toUpperCase()}
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-baseline gap-2">
                <span className="text-sm font-medium text-gray-900">
                  {c.creator_name || 'Unknown'}
                </span>
                <span className="text-xs text-gray-400">
                  {new Date(c.created_at).toLocaleString()}
                </span>
                {c.tone_flag && (
                  <span className="text-xs px-1.5 py-0.5 bg-amber-100 text-amber-700 rounded">
                    Tone-mediated
                  </span>
                )}
              </div>
              <p className="text-sm text-gray-700 mt-0.5">{c.content}</p>
            </div>
          </div>
        ))}
      </div>

      {toneResult && (
        <div className="mb-3 bg-amber-50 border border-amber-200 rounded-lg p-3">
          <p className="font-medium text-amber-800 text-sm">
            Your message may come across as confrontational
          </p>
          <p className="text-xs text-amber-700 mt-1">{toneResult.reason}</p>
          {toneResult.suggested_alternative && (
            <div className="mt-2">
              <p className="text-xs text-amber-700 font-medium">Suggested alternative:</p>
              <p className="text-xs text-amber-900 mt-1 italic">
                &ldquo;{toneResult.suggested_alternative}&rdquo;
              </p>
              <div className="flex gap-2 mt-2">
                <button
                  onClick={useSuggestion}
                  disabled={loading}
                  className="px-3 py-1 bg-amber-600 text-white rounded text-xs hover:bg-amber-700 disabled:opacity-50"
                >
                  Use Suggestion
                </button>
                <button
                  onClick={postAnyway}
                  disabled={loading}
                  className="px-3 py-1 bg-gray-200 text-gray-700 rounded text-xs hover:bg-gray-300 disabled:opacity-50"
                >
                  Post Anyway
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {!toneResult && (
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Add a comment..."
            className="flex-1 px-3 py-1.5 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
          />
          <button
            onClick={handleSend}
            disabled={loading || !input.trim()}
            className="px-3 py-1.5 bg-indigo-600 text-white rounded-lg text-sm hover:bg-indigo-700 disabled:opacity-50"
          >
            {loading ? '...' : 'Send'}
          </button>
        </div>
      )}
    </div>
  );
}
