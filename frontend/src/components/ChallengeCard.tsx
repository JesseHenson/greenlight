import { Link } from 'react-router-dom';
import type { Challenge } from '../types';

const statusConfig = {
  ideate: { label: 'Ideating', color: 'bg-emerald-50 text-emerald-700' },
  build: { label: 'Building', color: 'bg-amber-50 text-amber-700' },
  approved_for_analysis: { label: 'Ready for Analysis', color: 'bg-sky-50 text-sky-700' },
  analysis_in_progress: { label: 'Analyzing...', color: 'bg-sky-50 text-sky-700' },
  analysis_complete: { label: 'Complete', color: 'bg-emerald-50 text-emerald-700' },
};

interface Props {
  challenge: Challenge;
  onArchive: (id: number) => void;
}

export default function ChallengeCard({ challenge, onArchive }: Props) {
  const status = challenge.session_status
    ? statusConfig[challenge.session_status]
    : statusConfig.ideate;

  return (
    <div className="relative bg-white rounded-lg border border-slate-200/60 shadow-sm p-6 hover:shadow-md hover:border-slate-300 transition-all">
      <button
        onClick={(e) => {
          e.preventDefault();
          if (confirm('Archive this challenge? It will be hidden but not deleted.')) {
            onArchive(challenge.id);
          }
        }}
        className="absolute top-3 right-3 text-slate-300 hover:text-slate-500 transition-colors"
        title="Archive"
      >
        <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
          <path d="M4 3a2 2 0 100 4h12a2 2 0 100-4H4z" />
          <path fillRule="evenodd" d="M3 8h14v7a2 2 0 01-2 2H5a2 2 0 01-2-2V8zm5 3a1 1 0 011-1h2a1 1 0 110 2H9a1 1 0 01-1-1z" clipRule="evenodd" />
        </svg>
      </button>
      <Link
        to={
          challenge.session_status === 'analysis_complete'
            ? `/challenges/${challenge.id}/analysis`
            : `/challenges/${challenge.id}`
        }
        className="block"
      >
        <div className="flex items-start justify-between pr-6">
          <h3 className="text-base font-semibold text-slate-900">{challenge.title}</h3>
          <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium ${status.color}`}>
            {status.label}
          </span>
        </div>
        <p className="mt-2 text-slate-500 text-sm line-clamp-2">{challenge.description}</p>
        <div className="mt-4 text-sm text-slate-400">
          {challenge.idea_count} idea{challenge.idea_count !== 1 ? 's' : ''}
        </div>
      </Link>
    </div>
  );
}
