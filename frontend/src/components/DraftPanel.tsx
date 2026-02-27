import { useEffect, useRef, useState } from 'react';
import api from '../api/client';
import type { IdeaDraft, IdeaDraftUpdate } from '../types';

interface Props {
  ideaId: number;
}

export default function DraftPanel({ ideaId }: Props) {
  const [open, setOpen] = useState(false);
  const [draft, setDraft] = useState<IdeaDraft | null>(null);
  const [notes, setNotes] = useState('');
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (!open) return;
    api.get(`/ideas/${ideaId}/draft`).then((res) => {
      if (res.data) {
        setDraft(res.data);
        setNotes(res.data.notes);
      }
    });
  }, [ideaId, open]);

  const saveDraft = async (update: IdeaDraftUpdate) => {
    setSaving(true);
    setSaved(false);
    try {
      const res = await api.put(`/ideas/${ideaId}/draft`, update);
      setDraft(res.data);
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } finally {
      setSaving(false);
    }
  };

  const handleNotesChange = (value: string) => {
    setNotes(value);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      saveDraft({ notes: value });
    }, 500);
  };

  const handleCheckbox = (field: keyof IdeaDraftUpdate, value: boolean) => {
    setDraft((prev) => (prev ? { ...prev, [field]: value } : prev));
    saveDraft({ [field]: value });
  };

  return (
    <div className="mt-3 border-t border-gray-100 pt-2">
      <button
        onClick={() => setOpen(!open)}
        className="text-xs text-indigo-600 hover:text-indigo-800 font-medium"
      >
        {open ? 'Hide my private notes' : 'My private notes'}
      </button>
      {open && (
        <div className="mt-2 space-y-2 bg-gray-50 rounded-lg p-3">
          <div className="flex items-center gap-4 text-sm">
            <label className="flex items-center gap-1.5">
              <input
                type="checkbox"
                checked={draft?.want_pros_cons || false}
                onChange={(e) => handleCheckbox('want_pros_cons', e.target.checked)}
                className="rounded border-gray-300 text-indigo-600"
              />
              <span className="text-gray-700">Pros/Cons</span>
            </label>
            <label className="flex items-center gap-1.5">
              <input
                type="checkbox"
                checked={draft?.want_feasibility || false}
                onChange={(e) => handleCheckbox('want_feasibility', e.target.checked)}
                className="rounded border-gray-300 text-indigo-600"
              />
              <span className="text-gray-700">Feasibility</span>
            </label>
            <label className="flex items-center gap-1.5">
              <input
                type="checkbox"
                checked={draft?.want_fairness || false}
                onChange={(e) => handleCheckbox('want_fairness', e.target.checked)}
                className="rounded border-gray-300 text-indigo-600"
              />
              <span className="text-gray-700">Fairness</span>
            </label>
          </div>
          <textarea
            value={notes}
            onChange={(e) => handleNotesChange(e.target.value)}
            placeholder="Your private notes on this idea..."
            rows={3}
            className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 resize-none"
          />
          <div className="text-xs text-gray-400 text-right">
            {saving ? 'Saving...' : saved ? 'Saved' : ''}
          </div>
        </div>
      )}
    </div>
  );
}
