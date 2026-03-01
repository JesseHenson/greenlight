import { useState } from 'react';
import api from '../api/client';

interface Suggestion {
  idea: string;
  rationale: string;
}

interface Props {
  challengeId: number;
  onAccept: (content: string) => void;
}

export default function AISuggestButton({ challengeId, onAccept }: Props) {
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [loading, setLoading] = useState(false);
  const [show, setShow] = useState(false);

  const fetchSuggestions = async () => {
    setLoading(true);
    try {
      const res = await api.post(`/ai/suggest-ideas/${challengeId}`);
      setSuggestions(res.data.suggestions);
      setShow(true);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  };

  if (!show) {
    return (
      <button
        onClick={fetchSuggestions}
        disabled={loading}
        className="px-4 py-2 bg-indigo-50 text-indigo-700 rounded-md hover:bg-indigo-100 border border-indigo-200/60 shadow-sm disabled:opacity-50 font-medium text-sm transition-colors"
      >
        {loading ? 'Thinking...' : 'Get AI Suggestions'}
      </button>
    );
  }

  return (
    <div className="bg-indigo-50/50 border border-indigo-200/60 rounded-lg p-4 space-y-3">
      <div className="flex items-center justify-between">
        <h4 className="font-medium text-indigo-800">AI Suggestions</h4>
        <button
          onClick={() => setShow(false)}
          className="text-indigo-400 hover:text-indigo-600 text-sm transition-colors"
        >
          Close
        </button>
      </div>
      {suggestions.map((s, i) => (
        <div key={i} className="bg-white rounded-lg p-3 border border-indigo-200/60">
          <p className="text-slate-800 text-sm">{s.idea}</p>
          <p className="text-xs text-slate-500 mt-1">{s.rationale}</p>
          <button
            onClick={() => {
              onAccept(s.idea);
              setSuggestions((prev) => prev.filter((_, idx) => idx !== i));
              if (suggestions.length <= 1) setShow(false);
            }}
            className="mt-2 px-3 py-1 bg-indigo-600 text-white rounded-md text-xs hover:bg-indigo-700 shadow-sm transition-colors"
          >
            Add This Idea
          </button>
        </div>
      ))}
    </div>
  );
}
