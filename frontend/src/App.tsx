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
import ProblemDetailPage from './pages/ProblemDetailPage';
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
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600" />
      </div>
    );
  }

  if (!user) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center space-y-4">
          <p className="text-gray-500">Unable to load user profile.</p>
          {error && <p className="text-red-500 text-sm">{error}</p>}
          <button
            onClick={() => { setLoading(true); setError(''); fetchUser(); }}
            className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
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
      <Route path="/problems/:id" element={<ProblemDetailPage user={user} />} />
      <Route path="/problems/:id/analysis" element={<AnalysisPage />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

function SignInPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
      <div className="max-w-md w-full space-y-8 text-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">CommonGround</h1>
          <p className="mt-2 text-gray-600">Sign in to collaborate on parenting decisions</p>
        </div>
        <div className="bg-white p-8 rounded-xl shadow-sm space-y-4">
          <SignInButton mode="modal">
            <button className="w-full py-2 px-4 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 font-medium">
              Sign In
            </button>
          </SignInButton>
          <SignUpButton mode="modal">
            <button className="w-full py-2 px-4 bg-white border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 font-medium">
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
