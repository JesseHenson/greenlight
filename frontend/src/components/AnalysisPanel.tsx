import { useEffect, useState } from 'react';
import api from '../api/client';
import type { Analysis, BrainstormIdea } from '../types';
import CommentThread from './CommentThread';

interface Props {
  idea: BrainstormIdea;
}

function parseJSON(str: string): any {
  try {
    return JSON.parse(str);
  } catch {
    return null;
  }
}

function ScoreBar({ score, label }: { score: number; label: string }) {
  return (
    <div>
      <div className="flex justify-between text-sm mb-1">
        <span className="text-gray-600">{label}</span>
        <span className="font-medium">{score}/10</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2">
        <div
          className="h-2 rounded-full transition-all"
          style={{
            width: `${score * 10}%`,
            backgroundColor: score >= 7 ? '#22c55e' : score >= 4 ? '#eab308' : '#ef4444',
          }}
        />
      </div>
    </div>
  );
}

export default function AnalysisPanel({ idea }: Props) {
  const [analyses, setAnalyses] = useState<Analysis[]>([]);
  const [expanded, setExpanded] = useState(false);

  useEffect(() => {
    api.get(`/ideas/${idea.id}/analyses`).then((res) => setAnalyses(res.data));
  }, [idea.id]);

  const prosCons = analyses.find((a) => a.analysis_type === 'pros_cons');
  const feasibility = analyses.find((a) => a.analysis_type === 'feasibility');
  const fairness = analyses.find((a) => a.analysis_type === 'fairness');

  const prosConsData = prosCons ? parseJSON(prosCons.content) : null;
  const feasibilityData = feasibility ? parseJSON(feasibility.content) : null;
  const fairnessData = fairness ? parseJSON(fairness.content) : null;

  return (
    <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full px-4 py-3 flex items-center justify-between hover:bg-gray-50"
      >
        <div className="flex items-center gap-3">
          <span className="text-gray-900 font-medium text-left">{idea.content}</span>
        </div>
        <div className="flex items-center gap-2">
          {feasibilityData && (
            <span className="text-xs px-2 py-1 bg-blue-50 text-blue-700 rounded">
              Feasibility: {feasibilityData.score}/10
            </span>
          )}
          {fairnessData && (
            <span className="text-xs px-2 py-1 bg-purple-50 text-purple-700 rounded">
              Fairness: {fairnessData.score}/10
            </span>
          )}
          <span className="text-gray-400">{expanded ? '−' : '+'}</span>
        </div>
      </button>

      {expanded && (
        <div className="px-4 pb-4 space-y-4 border-t border-gray-100 pt-4">
          {prosConsData && (
            <div>
              <h4 className="text-sm font-semibold text-gray-700 mb-2">Pros & Cons</h4>
              <div className="grid md:grid-cols-2 gap-3">
                <div>
                  <p className="text-xs font-medium text-green-700 mb-1">Pros</p>
                  <ul className="space-y-1">
                    {prosConsData.pros?.map((p: string, i: number) => (
                      <li key={i} className="text-sm text-gray-700 flex gap-1">
                        <span className="text-green-500">+</span> {p}
                      </li>
                    ))}
                  </ul>
                </div>
                <div>
                  <p className="text-xs font-medium text-red-700 mb-1">Cons</p>
                  <ul className="space-y-1">
                    {prosConsData.cons?.map((c: string, i: number) => (
                      <li key={i} className="text-sm text-gray-700 flex gap-1">
                        <span className="text-red-500">−</span> {c}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
              {prosConsData.children_impact && (
                <p className="mt-2 text-sm text-gray-600 bg-blue-50 p-2 rounded">
                  <span className="font-medium">Children's impact:</span>{' '}
                  {prosConsData.children_impact}
                </p>
              )}
            </div>
          )}

          {feasibilityData && (
            <div>
              <h4 className="text-sm font-semibold text-gray-700 mb-2">Feasibility</h4>
              <ScoreBar score={feasibilityData.score} label="Overall Score" />
              <div className="mt-2 grid md:grid-cols-2 gap-2 text-sm text-gray-600">
                <p><span className="font-medium">Logistics:</span> {feasibilityData.logistics}</p>
                <p><span className="font-medium">Cost:</span> {feasibilityData.cost}</p>
                <p><span className="font-medium">Time:</span> {feasibilityData.time}</p>
                <p><span className="font-medium">Complexity:</span> {feasibilityData.complexity}</p>
              </div>
            </div>
          )}

          {fairnessData && (
            <div>
              <h4 className="text-sm font-semibold text-gray-700 mb-2">Fairness</h4>
              <ScoreBar score={fairnessData.score} label="Overall Score" />
              <div className="mt-2 space-y-1 text-sm text-gray-600">
                <p><span className="font-medium">Parent A:</span> {fairnessData.parent_a_impact}</p>
                <p><span className="font-medium">Parent B:</span> {fairnessData.parent_b_impact}</p>
                <p><span className="font-medium">Balance:</span> {fairnessData.balance_assessment}</p>
              </div>
            </div>
          )}

          <div className="border-t border-gray-100 pt-4">
            <CommentThread ideaId={idea.id} />
          </div>
        </div>
      )}
    </div>
  );
}
