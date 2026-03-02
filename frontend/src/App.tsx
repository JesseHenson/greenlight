import { useEffect, useState, useCallback } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import {
  SignedIn,
  SignedOut,
  SignInButton,
  SignUpButton,
  useAuth,
} from '@clerk/clerk-react';
import * as Sentry from '@sentry/react';
import { isAxiosError } from 'axios';
import { setTokenGetter } from './api/client';
import api from './api/client';
import type { User } from './types';
import DashboardPage from './pages/DashboardPage';
import ChallengeDetailPage from './pages/ChallengeDetailPage';
import AnalysisPage from './pages/AnalysisPage';

const IS_DEV = import.meta.env.DEV;

const DEMO_USERS = [
  { name: 'Alex Chen', initials: 'AC', email: 'alex@greenlight-test.com', color: 'bg-sky-500' },
  { name: 'Jordan Lee', initials: 'JL', email: 'jordan@greenlight-test.com', color: 'bg-amber-500' },
  { name: 'Sam Rivera', initials: 'SR', email: 'sam@greenlight-test.com', color: 'bg-indigo-500' },
];

function AuthenticatedApp({ user, onSignOut }: { user: User; onSignOut?: () => void }) {
  return (
    <Routes>
      <Route path="/" element={<DashboardPage user={user} onDevSignOut={onSignOut} />} />
      <Route path="/challenges/:id" element={<ChallengeDetailPage user={user} />} />
      <Route path="/challenges/:id/analysis" element={<AnalysisPage />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

function ClerkAuthenticatedApp() {
  const { getToken, isLoaded } = useAuth();
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchUser = useCallback(async () => {
    if (!isLoaded) return;
    setTokenGetter(getToken);
    try {
      const res = await api.get('/auth/me');
      setUser(res.data);
    } catch (err: unknown) {
      console.error('Failed to load user profile:', err);
      setError(isAxiosError(err) && err.response?.data?.detail || 'Failed to load profile');
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

  return <AuthenticatedApp user={user} />;
}

function SignInPage({ onDevLogin }: { onDevLogin?: (email: string) => void }) {
  const [signingIn, setSigningIn] = useState<string | null>(null);
  const [error, setError] = useState('');

  const handleDemoSignIn = async (demoUser: typeof DEMO_USERS[0]) => {
    if (!onDevLogin) return;
    setSigningIn(demoUser.email);
    setError('');
    try {
      onDevLogin(demoUser.email);
    } catch {
      setError(`Failed to sign in as ${demoUser.name}`);
    } finally {
      setSigningIn(null);
    }
  };

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

        {IS_DEV && (
          <div className="bg-white p-6 rounded-xl shadow-lg border border-slate-200/60">
            <p className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-4">Quick demo — sign in as</p>
            {error && <p className="text-red-500 text-xs mb-3">{error}</p>}
            <div className="flex justify-center gap-4">
              {DEMO_USERS.map((demoUser) => (
                <button
                  key={demoUser.email}
                  onClick={() => handleDemoSignIn(demoUser)}
                  disabled={signingIn !== null}
                  className="group flex flex-col items-center gap-2 disabled:opacity-50 transition-opacity"
                >
                  <div className={`w-12 h-12 rounded-full ${demoUser.color} flex items-center justify-center text-white font-semibold text-sm shadow-sm group-hover:scale-105 transition-transform ${signingIn === demoUser.email ? 'animate-pulse' : ''}`}>
                    {demoUser.initials}
                  </div>
                  <span className="text-xs text-slate-600 font-medium">{demoUser.name}</span>
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function App() {
  const [devUser, setDevUser] = useState<User | null>(null);
  const [devLoading, setDevLoading] = useState(
    () => IS_DEV && !!sessionStorage.getItem('dev_token')
  );

  // Check for existing dev session on mount
  useEffect(() => {
    const token = sessionStorage.getItem('dev_token');
    if (token && IS_DEV) {
      setTokenGetter(async () => token);
      api.get('/auth/me')
        .then((res) => setDevUser(res.data))
        .catch(() => { sessionStorage.removeItem('dev_token'); })
        .finally(() => setDevLoading(false));
    }
  }, []);

  const handleDevLogin = async (email: string) => {
    try {
      const res = await api.post('/auth/dev-login', { email });
      const { user, token } = res.data;
      sessionStorage.setItem('dev_token', token);
      setTokenGetter(async () => token);
      setDevUser(user);
    } catch (err) {
      console.error('Dev login failed:', err);
    }
  };

  const handleDevSignOut = () => {
    sessionStorage.removeItem('dev_token');
    setDevUser(null);
    setTokenGetter(async () => null);
  };

  if (devLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600" />
      </div>
    );
  }

  // Dev user is logged in — skip Clerk entirely
  if (devUser) {
    return (
      <Sentry.ErrorBoundary fallback={<p>Something went wrong</p>}>
        <BrowserRouter>
          <AuthenticatedApp user={devUser} onSignOut={handleDevSignOut} />
        </BrowserRouter>
      </Sentry.ErrorBoundary>
    );
  }

  return (
    <Sentry.ErrorBoundary fallback={<p>Something went wrong</p>}>
      <BrowserRouter>
        <SignedIn>
          <ClerkAuthenticatedApp />
        </SignedIn>
        <SignedOut>
          <SignInPage onDevLogin={IS_DEV ? handleDevLogin : undefined} />
        </SignedOut>
      </BrowserRouter>
    </Sentry.ErrorBoundary>
  );
}

export default App;
