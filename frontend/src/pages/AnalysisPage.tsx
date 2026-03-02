import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import api from '../api/client';
import type { Challenge, Idea, GreenlightSession, Analysis } from '../types';
import AnalysisPanel from '../components/AnalysisPanel';
import AnalysisProgress from '../components/AnalysisProgress';

interface Recommendation {
  idea: string;
  why: string;
}

interface SummaryData {
  themes?: string[];
  top_recommendations?: Recommendation[];
  trade_offs?: string[];
  next_steps?: string[];
}

function parseJSON<T>(str: string): T | null {
  try {
    return JSON.parse(str) as T;
  } catch {
    return null;
  }
}

export default function AnalysisPage() {
  const { id } = useParams<{ id: string }>();
  const [challenge, setChallenge] = useState<Challenge | null>(null);
  const [ideas, setIdeas] = useState<Idea[]>([]);
  const [session, setSession] = useState<GreenlightSession | null>(null);
  const [summary, setSummary] = useState<Analysis | null>(null);

  const [reloadKey, setReloadKey] = useState(0);
  const reload = () => setReloadKey((k) => k + 1);

  useEffect(() => {
    async function load() {
      const [cRes, iRes, sRes] = await Promise.all([
        api.get(`/challenges/${id}`),
        api.get(`/challenges/${id}/ideas`),
        api.get(`/challenges/${id}/session`),
      ]);
      setChallenge(cRes.data);
      setIdeas(iRes.data);
      setSession(sRes.data);

      if (
        sRes.data.status === 'analysis_complete' ||
        sRes.data.status === 'analysis_in_progress'
      ) {
        try {
          const sumRes = await api.get(`/challenges/${id}/analysis-summary`);
          setSummary(sumRes.data);
        } catch {
          // ignore
        }
      }
    }
    load();
  }, [id, reloadKey]);

  if (!challenge || !session) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600" />
      </div>
    );
  }

  const isInProgress =
    session.status === 'analysis_in_progress' ||
    session.status === 'approved_for_analysis';

  const summaryData = summary ? parseJSON<SummaryData>(summary.content) : null;

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-slate-900">
        <div className="max-w-5xl mx-auto px-4 py-4 flex items-center gap-4">
          <Link to="/" className="text-slate-400 hover:text-white transition-colors">
            &larr; Dashboard
          </Link>
          <h1 className="text-lg font-semibold text-white tracking-tight">{challenge.title} — Analysis</h1>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 py-8 space-y-6">
        {isInProgress && (
          <AnalysisProgress challengeId={challenge.id} onComplete={reload} />
        )}

        {summaryData && (
          <div className="bg-white border border-slate-200/60 rounded-lg shadow-sm p-6">
            <h2 className="text-lg font-semibold text-slate-900 mb-4">Session Summary</h2>

            {summaryData.themes && (
              <div className="mb-4">
                <h3 className="text-sm font-semibold text-slate-700 mb-2">Key Themes</h3>
                <div className="flex flex-wrap gap-2">
                  {summaryData.themes.map((t: string, i: number) => (
                    <span
                      key={i}
                      className="px-3 py-1 bg-emerald-50 text-emerald-700 rounded-full text-sm"
                    >
                      {t}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {summaryData.top_recommendations && (
              <div className="mb-4">
                <h3 className="text-sm font-semibold text-slate-700 mb-2">
                  Top Recommendations
                </h3>
                <div className="space-y-2">
                  {summaryData.top_recommendations.map((r, i) => (
                    <div key={i} className="bg-emerald-50/50 border border-emerald-200/60 p-3 rounded-lg">
                      <p className="font-medium text-emerald-800">{r.idea}</p>
                      <p className="text-sm text-emerald-600 mt-1">{r.why}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {summaryData.trade_offs && (
              <div className="mb-4">
                <h3 className="text-sm font-semibold text-slate-700 mb-2">Trade-offs to Discuss</h3>
                <ul className="space-y-1">
                  {summaryData.trade_offs.map((t: string, i: number) => (
                    <li key={i} className="text-sm text-slate-600 flex gap-2">
                      <span className="text-amber-400">*</span> {t}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {summaryData.next_steps && (
              <div>
                <h3 className="text-sm font-semibold text-slate-700 mb-2">Next Steps</h3>
                <ol className="space-y-1">
                  {summaryData.next_steps.map((s: string, i: number) => (
                    <li key={i} className="text-sm text-slate-600">
                      {i + 1}. {s}
                    </li>
                  ))}
                </ol>
              </div>
            )}
          </div>
        )}

        <div className="space-y-3">
          <h2 className="text-lg font-semibold text-slate-900">Per-Idea Analysis</h2>
          {ideas.map((idea) => (
            <AnalysisPanel key={idea.id} idea={idea} />
          ))}
        </div>
      </main>
    </div>
  );
}
