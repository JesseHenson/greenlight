import { useEffect, useState } from 'react';
import api from '../api/client';

interface Props {
  problemId: number;
  onComplete: () => void;
}

interface AnalysisStatus {
  session_status: string;
  total_analyses: number;
  completed_analyses: number;
  progress: number;
}

export default function AnalysisProgress({ problemId, onComplete }: Props) {
  const [status, setStatus] = useState<AnalysisStatus | null>(null);

  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        const res = await api.get(`/problems/${problemId}/analysis-status`);
        setStatus(res.data);
        if (res.data.session_status === 'analysis_complete') {
          clearInterval(interval);
          onComplete();
        }
      } catch {
        // ignore
      }
    }, 3000);

    return () => clearInterval(interval);
  }, [problemId, onComplete]);

  if (!status) return null;

  const pct = Math.round(status.progress * 100);

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6 text-center">
      <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-indigo-600 mx-auto mb-4" />
      <h3 className="text-lg font-semibold text-gray-900">Analysis In Progress</h3>
      <p className="text-sm text-gray-500 mt-1">
        {status.completed_analyses} of {status.total_analyses} analyses complete
      </p>
      <div className="mt-4 w-full bg-gray-200 rounded-full h-2">
        <div
          className="bg-indigo-600 h-2 rounded-full transition-all duration-500"
          style={{ width: `${pct}%` }}
        />
      </div>
      <p className="text-sm text-gray-500 mt-2">{pct}%</p>
    </div>
  );
}
