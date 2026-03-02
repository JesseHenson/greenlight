import { useEffect, useState } from 'react';
import api from '../api/client';
import type { Analysis, Idea } from '../types';
import CommentThread from './CommentThread';

interface ProsConsData {
  pros?: string[];
  cons?: string[];
  stakeholder_impact?: string;
}

interface FeasibilityData {
  score: number;
  logistics?: string;
  cost?: string;
  time?: string;
  complexity?: string;
}

interface ImpactData {
  score: number;
  team_impact?: string;
  user_impact?: string;
  balance_assessment?: string;
}

interface Props {
  idea: Idea;
}

function parseJSON<T>(str: string): T | null {
  try {
    return JSON.parse(str) as T;
  } catch {
    return null;
  }
}

function ScoreBar({ score, label }: { score: number; label: string }) {
  return (
    <div>
      <div className="flex justify-between text-sm mb-1">
        <span className="text-slate-600">{label}</span>
        <span className="font-medium">{score}/10</span>
      </div>
      <div className="w-full bg-slate-200 rounded-full h-2">
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
  const impact = analyses.find((a) => a.analysis_type === 'impact');

  const prosConsData = prosCons ? parseJSON<ProsConsData>(prosCons.content) : null;
  const feasibilityData = feasibility ? parseJSON<FeasibilityData>(feasibility.content) : null;
  const impactData = impact ? parseJSON<ImpactData>(impact.content) : null;

  return (
    <div className="bg-white border border-slate-200/60 rounded-lg shadow-sm overflow-hidden">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full px-4 py-3 flex items-center justify-between hover:bg-slate-50 transition-colors"
      >
        <div className="flex items-center gap-3">
          <span className="text-slate-800 font-medium text-left">{idea.content}</span>
        </div>
        <div className="flex items-center gap-2">
          {feasibilityData && (
            <span className="text-xs px-2 py-1 bg-sky-50 text-sky-700 rounded">
              Feasibility: {feasibilityData.score}/10
            </span>
          )}
          {impactData && (
            <span className="text-xs px-2 py-1 bg-indigo-50 text-indigo-700 rounded">
              Impact: {impactData.score}/10
            </span>
          )}
          <span className="text-slate-400">{expanded ? '\u2212' : '+'}</span>
        </div>
      </button>

      {expanded && (
        <div className="px-4 pb-4 space-y-4 border-t border-slate-100 pt-4">
          {prosConsData && (
            <div>
              <h4 className="text-sm font-semibold text-slate-700 mb-2">Pros & Cons</h4>
              <div className="grid md:grid-cols-2 gap-3">
                <div>
                  <p className="text-xs font-medium text-green-700 mb-1">Pros</p>
                  <ul className="space-y-1">
                    {prosConsData.pros?.map((p: string, i: number) => (
                      <li key={i} className="text-sm text-slate-600 flex gap-1">
                        <span className="text-green-500">+</span> {p}
                      </li>
                    ))}
                  </ul>
                </div>
                <div>
                  <p className="text-xs font-medium text-red-700 mb-1">Cons</p>
                  <ul className="space-y-1">
                    {prosConsData.cons?.map((c: string, i: number) => (
                      <li key={i} className="text-sm text-slate-600 flex gap-1">
                        <span className="text-red-500">&minus;</span> {c}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
              {prosConsData.stakeholder_impact && (
                <p className="mt-2 text-sm text-slate-600 bg-sky-50/50 border border-sky-200/60 p-2 rounded">
                  <span className="font-medium">Stakeholder impact:</span>{' '}
                  {prosConsData.stakeholder_impact}
                </p>
              )}
            </div>
          )}

          {feasibilityData && (
            <div>
              <h4 className="text-sm font-semibold text-slate-700 mb-2">Feasibility</h4>
              <ScoreBar score={feasibilityData.score} label="Overall Score" />
              <div className="mt-2 grid md:grid-cols-2 gap-2 text-sm text-slate-600">
                <p><span className="font-medium">Logistics:</span> {feasibilityData.logistics}</p>
                <p><span className="font-medium">Cost:</span> {feasibilityData.cost}</p>
                <p><span className="font-medium">Time:</span> {feasibilityData.time}</p>
                <p><span className="font-medium">Complexity:</span> {feasibilityData.complexity}</p>
              </div>
            </div>
          )}

          {impactData && (
            <div>
              <h4 className="text-sm font-semibold text-slate-700 mb-2">Impact</h4>
              <ScoreBar score={impactData.score} label="Overall Score" />
              <div className="mt-2 space-y-1 text-sm text-slate-600">
                <p><span className="font-medium">Team:</span> {impactData.team_impact}</p>
                <p><span className="font-medium">Users:</span> {impactData.user_impact}</p>
                <p><span className="font-medium">Balance:</span> {impactData.balance_assessment}</p>
              </div>
            </div>
          )}

          <div className="border-t border-slate-100 pt-4">
            <CommentThread ideaId={idea.id} />
          </div>
        </div>
      )}
    </div>
  );
}
