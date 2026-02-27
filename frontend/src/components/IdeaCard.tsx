import type { BrainstormIdea, User } from '../types';
import DraftPanel from './DraftPanel';

interface Props {
  idea: BrainstormIdea;
  currentUser: User;
  onDelete: (id: number) => void;
  isBrainstorming?: boolean;
}

export default function IdeaCard({ idea, currentUser, onDelete, isBrainstorming }: Props) {
  const isOwner = idea.created_by === currentUser.id;

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4 shadow-sm">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-gray-900">{idea.content}</p>
          {idea.tone_flag && (
            <div className="mt-2 bg-amber-50 border border-amber-200 rounded-lg p-2 text-sm">
              <span className="text-amber-600 font-medium">Tone warning</span>
              {idea.suggested_alternative && (
                <p className="text-amber-700 mt-1">
                  Suggested: "{idea.suggested_alternative}"
                </p>
              )}
            </div>
          )}
        </div>
        {isOwner && (
          <button
            onClick={() => onDelete(idea.id)}
            className="ml-2 text-gray-400 hover:text-red-500 text-sm"
          >
            Remove
          </button>
        )}
      </div>
      <div className="mt-3 text-xs text-gray-500">
        by {idea.creator_name || 'Unknown'}
      </div>
      {isBrainstorming && <DraftPanel ideaId={idea.id} />}
    </div>
  );
}
