import { Link } from 'react-router-dom';
import type { Problem } from '../types';

const statusConfig = {
  brainstorming: { label: 'Brainstorming', color: 'bg-blue-100 text-blue-800' },
  approved_for_analysis: { label: 'Ready for Analysis', color: 'bg-yellow-100 text-yellow-800' },
  analysis_in_progress: { label: 'Analyzing...', color: 'bg-yellow-100 text-yellow-800' },
  analysis_complete: { label: 'Complete', color: 'bg-green-100 text-green-800' },
};

interface Props {
  problem: Problem;
  onArchive: (id: number) => void;
}

export default function ProblemCard({ problem, onArchive }: Props) {
  const status = problem.session_status
    ? statusConfig[problem.session_status]
    : statusConfig.brainstorming;

  return (
    <div className="relative bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
      <button
        onClick={(e) => {
          e.preventDefault();
          if (confirm('Archive this conversation? It will be hidden but not deleted.')) {
            onArchive(problem.id);
          }
        }}
        className="absolute top-3 right-3 text-gray-300 hover:text-gray-500 transition-colors"
        title="Archive"
      >
        <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
          <path d="M4 3a2 2 0 100 4h12a2 2 0 100-4H4z" />
          <path fillRule="evenodd" d="M3 8h14v7a2 2 0 01-2 2H5a2 2 0 01-2-2V8zm5 3a1 1 0 011-1h2a1 1 0 110 2H9a1 1 0 01-1-1z" clipRule="evenodd" />
        </svg>
      </button>
      <Link
        to={
          problem.session_status === 'analysis_complete'
            ? `/problems/${problem.id}/analysis`
            : `/problems/${problem.id}`
        }
        className="block"
      >
        <div className="flex items-start justify-between pr-6">
          <h3 className="text-lg font-semibold text-gray-900">{problem.title}</h3>
          <span className={`px-2 py-1 rounded-full text-xs font-medium ${status.color}`}>
            {status.label}
          </span>
        </div>
        <p className="mt-2 text-gray-600 text-sm line-clamp-2">{problem.description}</p>
        <div className="mt-4 text-sm text-gray-500">
          {problem.idea_count} idea{problem.idea_count !== 1 ? 's' : ''}
        </div>
      </Link>
    </div>
  );
}
