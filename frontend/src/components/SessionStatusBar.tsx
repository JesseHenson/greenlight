import type { GreenlightSession } from '../types';

interface Props {
  session: GreenlightSession | null;
  ideaCount: number;
  currentUserId: number;
  onApprove: () => void;
  approving: boolean;
}

const statusLabels: Record<string, { label: string; color: string }> = {
  ideate: { label: 'Ideating — all ideas welcome!', color: 'bg-emerald-50 text-emerald-700' },
  build: { label: 'Building — Yes, And!', color: 'bg-amber-50 text-amber-700' },
  approved_for_analysis: { label: 'Approved - Starting Analysis', color: 'bg-sky-50 text-sky-700' },
  analysis_in_progress: { label: 'Analysis In Progress', color: 'bg-sky-50 text-sky-700' },
  analysis_complete: { label: 'Analysis Complete', color: 'bg-emerald-50 text-emerald-700' },
};

const stageProgress: Record<string, number> = {
  ideate: 1,
  build: 2,
  approved_for_analysis: 3,
  analysis_in_progress: 3,
  analysis_complete: 4,
};

const stages = ['Define', 'Ideate', 'Build', 'Converge'];

export default function SessionStatusBar({ session, ideaCount, currentUserId, onApprove, approving }: Props) {
  if (!session) return null;

  const status = statusLabels[session.status] || statusLabels.ideate;
  const currentUserApproved = session.approvals?.some(a => a.user_id === currentUserId);
  const approvalCount = session.approvals?.length || 0;
  const currentStage = stageProgress[session.status] || 1;

  const isGateable = session.status === 'ideate' || session.status === 'build';
  const gateButtonText = session.status === 'ideate' ? 'Ready to Build' : 'Ready to Converge';

  return (
    <div className="bg-white border border-slate-200/60 rounded-lg shadow-sm p-4 space-y-3">
      {/* Stage progress indicator */}
      <div className="flex items-center gap-1">
        {stages.map((stage, i) => {
          const stageNum = i + 1;
          const isActive = stageNum === currentStage;
          const isComplete = stageNum < currentStage;
          return (
            <div key={stage} className="flex-1 flex items-center gap-1">
              <div className={`flex-1 h-1.5 rounded-full ${
                isComplete ? 'bg-emerald-600' : isActive ? 'bg-emerald-500' : 'bg-slate-200'
              }`} />
              <span className={`text-xs font-medium ${
                isActive ? 'text-emerald-700' : isComplete ? 'text-emerald-600' : 'text-slate-400'
              }`}>
                {stage}
              </span>
            </div>
          );
        })}
      </div>

      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium ${status.color}`}>
            {status.label}
          </span>
          <span className="text-sm text-slate-500">{ideaCount} ideas submitted</span>
          {isGateable && approvalCount > 0 && (
            <span className="text-sm text-slate-400">
              ({approvalCount}/{session.total_collaborators} approved)
            </span>
          )}
        </div>
        {isGateable && ideaCount > 0 && (
          currentUserApproved ? (
            <span className="px-4 py-2 bg-slate-100 text-slate-500 rounded-md text-sm font-medium">
              Waiting for team to approve...
            </span>
          ) : (
            <button
              onClick={onApprove}
              disabled={approving}
              className="px-4 py-2 bg-emerald-600 text-white rounded-md hover:bg-emerald-700 disabled:opacity-50 font-medium shadow-sm transition-colors"
            >
              {approving ? 'Approving...' : gateButtonText}
            </button>
          )
        )}
      </div>
    </div>
  );
}
