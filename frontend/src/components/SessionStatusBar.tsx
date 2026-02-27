import type { BrainstormSession } from '../types';

interface Props {
  session: BrainstormSession | null;
  ideaCount: number;
  currentUserId: number;
  onApprove: () => void;
  approving: boolean;
}

const statusLabels: Record<string, { label: string; color: string }> = {
  brainstorming: { label: 'Brainstorming Phase', color: 'bg-blue-100 text-blue-800' },
  approved_for_analysis: { label: 'Approved - Starting Analysis', color: 'bg-yellow-100 text-yellow-800' },
  analysis_in_progress: { label: 'Analysis In Progress', color: 'bg-yellow-100 text-yellow-800' },
  analysis_complete: { label: 'Analysis Complete', color: 'bg-green-100 text-green-800' },
};

export default function SessionStatusBar({ session, ideaCount, currentUserId, onApprove, approving }: Props) {
  if (!session) return null;

  const status = statusLabels[session.status] || statusLabels.brainstorming;
  const currentUserApproved = session.approvals?.some(a => a.user_id === currentUserId);
  const approvalCount = session.approvals?.length || 0;

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 flex items-center justify-between">
      <div className="flex items-center gap-3">
        <span className={`px-3 py-1 rounded-full text-sm font-medium ${status.color}`}>
          {status.label}
        </span>
        <span className="text-sm text-gray-500">{ideaCount} ideas submitted</span>
        {session.status === 'brainstorming' && approvalCount > 0 && (
          <span className="text-sm text-gray-400">
            ({approvalCount}/{session.total_collaborators} approved)
          </span>
        )}
      </div>
      {session.status === 'brainstorming' && ideaCount > 0 && (
        currentUserApproved ? (
          <span className="px-4 py-2 bg-gray-100 text-gray-600 rounded-lg text-sm font-medium">
            Waiting for your co-parent to approve...
          </span>
        ) : (
          <button
            onClick={onApprove}
            disabled={approving}
            className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 font-medium"
          >
            {approving ? 'Approving...' : 'Ready for Analysis'}
          </button>
        )
      )}
    </div>
  );
}
