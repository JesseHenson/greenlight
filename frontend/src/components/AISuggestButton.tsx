import { useState } from 'react';
import api from '../api/client';

interface Suggestion {
  idea: string;
  rationale: string;
}

interface Props {
  problemId: number;
  onAccept: (content: string) => void;
}

export default function AISuggestButton({ problemId, onAccept }: Props) {
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [loading, setLoading] = useState(false);
  const [show, setShow] = useState(false);

  const fetchSuggestions = async () => {
    setLoading(true);
    try {
      const res = await api.post(`/ai/suggest-ideas/${problemId}`);
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
        className="px-4 py-2 bg-purple-100 text-purple-700 rounded-lg hover:bg-purple-200 disabled:opacity-50 font-medium text-sm"
      >
        {loading ? 'Thinking...' : 'Get AI Suggestions'}
      </button>
    );
  }

  return (
    <div className="bg-purple-50 border border-purple-200 rounded-lg p-4 space-y-3">
      <div className="flex items-center justify-between">
        <h4 className="font-medium text-purple-800">AI Suggestions</h4>
        <button
          onClick={() => setShow(false)}
          className="text-purple-500 hover:text-purple-700 text-sm"
        >
          Close
        </button>
      </div>
      {suggestions.map((s, i) => (
        <div key={i} className="bg-white rounded-lg p-3 border border-purple-100">
          <p className="text-gray-900 text-sm">{s.idea}</p>
          <p className="text-xs text-gray-500 mt-1">{s.rationale}</p>
          <button
            onClick={() => {
              onAccept(s.idea);
              setSuggestions((prev) => prev.filter((_, idx) => idx !== i));
              if (suggestions.length <= 1) setShow(false);
            }}
            className="mt-2 px-3 py-1 bg-purple-600 text-white rounded text-xs hover:bg-purple-700"
          >
            Add This Idea
          </button>
        </div>
      ))}
    </div>
  );
}
