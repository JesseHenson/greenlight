import { useEffect, useState, useCallback } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import {
  SignedIn,
  SignedOut,
  SignInButton,
  SignUpButton,
  useAuth,
} from '@clerk/clerk-react';
import { setTokenGetter } from './api/client';
import api from './api/client';
import type { User } from './types';
import DashboardPage from './pages/DashboardPage';
import ChallengeDetailPage from './pages/ChallengeDetailPage';
import AnalysisPage from './pages/AnalysisPage';

function AuthenticatedApp() {
  const { getToken, isLoaded } = useAuth();
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchUser = useCallback(async () => {
    if (!isLoaded) return;

    // Wire up the token getter for all API calls
    setTokenGetter(getToken);

    try {
      const res = await api.get('/auth/me');
      setUser(res.data);
    } catch (err: any) {
      console.error('Failed to load user profile:', err);
      setError(err.response?.data?.detail || 'Failed to load profile');
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, [isLoaded, getToken]);

  useEffect(() => {
    fetchUser();
  }, [fetchUser]);

  if (!isLoaded || loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600" />
      </div>
    );
  }

  if (!user) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center space-y-4">
          <p className="text-slate-500">Unable to load user profile.</p>
          {error && <p className="text-red-500 text-sm">{error}</p>}
          <button
            onClick={() => { setLoading(true); setError(''); fetchUser(); }}
            className="px-4 py-2 bg-emerald-600 text-white rounded-md hover:bg-emerald-700 shadow-sm font-medium transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <Routes>
      <Route path="/" element={<DashboardPage user={user} />} />
      <Route path="/challenges/:id" element={<ChallengeDetailPage user={user} />} />
      <Route path="/challenges/:id/analysis" element={<AnalysisPage />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

function SignInPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 px-4">
      <div className="max-w-md w-full space-y-8 text-center">
        <div>
          <h1 className="text-3xl font-semibold text-slate-900 tracking-tight">Greenlight</h1>
          <p className="mt-2 text-slate-500">Sign in to brainstorm with your team</p>
        </div>
        <div className="bg-white p-8 rounded-xl shadow-lg border border-slate-200/60 space-y-4">
          <SignInButton mode="modal">
            <button className="w-full py-2 px-4 bg-emerald-600 text-white rounded-md hover:bg-emerald-700 font-medium shadow-sm transition-colors">
              Sign In
            </button>
          </SignInButton>
          <SignUpButton mode="modal">
            <button className="w-full py-2 px-4 bg-white border border-slate-300 text-slate-700 rounded-md hover:bg-slate-50 font-medium shadow-sm transition-colors">
              Create Account
            </button>
          </SignUpButton>
        </div>
      </div>
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <SignedIn>
        <AuthenticatedApp />
      </SignedIn>
      <SignedOut>
        <SignInPage />
      </SignedOut>
    </BrowserRouter>
  );
}

export default App;
