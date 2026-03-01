import type { Idea, User } from '../types';
import DraftPanel from './DraftPanel';

interface Props {
  idea: Idea;
  currentUser: User;
  onDelete: (id: number) => void;
  canEdit?: boolean;
}

export default function IdeaCard({ idea, currentUser, onDelete, canEdit }: Props) {
  const isOwner = idea.created_by === currentUser.id;

  return (
    <div className="bg-white rounded-lg border border-slate-200/60 p-4 shadow-sm">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-slate-800">{idea.content}</p>
          {idea.tone_flag && (
            <div className="mt-2 bg-amber-50 border border-amber-200 rounded-md p-2 text-sm">
              <span className="text-amber-600 font-medium">Creativity check</span>
              {idea.suggested_alternative && (
                <p className="text-amber-700 mt-1">
                  Try instead: "{idea.suggested_alternative}"
                </p>
              )}
            </div>
          )}
        </div>
        {isOwner && (
          <button
            onClick={() => onDelete(idea.id)}
            className="ml-2 text-slate-300 hover:text-red-500 text-sm transition-colors"
          >
            Remove
          </button>
        )}
      </div>
      <div className="mt-3 text-xs text-slate-400">
        by {idea.creator_name || 'Unknown'}
      </div>
      {canEdit && <DraftPanel ideaId={idea.id} />}
    </div>
  );
}
