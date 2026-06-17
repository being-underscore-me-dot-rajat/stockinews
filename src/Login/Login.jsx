import '../App.css';
import './Login.css';
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { API_BASE } from '../lib/api';

const Login = () => {
  const [authMode, setAuthMode] = useState('login');
  const [email, setEmail]       = useState('');
  const [password, setPassword] = useState('');
  const [name, setName]         = useState('');
  const [msg, setMsg]           = useState(null);
  const [msgType, setMsgType]   = useState('error');
  const navigate = useNavigate();

  const isLogin  = authMode === 'login';
  const isSignup = authMode === 'signup';
  const isReset  = authMode === 'reset';

  const handleAuth = async (e) => {
    e.preventDefault();
    setMsg(null);
    const urls  = { login: `${API_BASE}/login`, signup: `${API_BASE}/signup`, reset: `${API_BASE}/reset-password` };
    const body  = isSignup ? { name, email, password } : { email, password };
    try {
      const res  = await fetch(urls[authMode], {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      const data = await res.json();
      if (res.ok) {
        if (isReset) {
          setMsg('Password reset successful. You can now log in.');
          setMsgType('success');
          setPassword('');
          setAuthMode('login');
          return;
        }
        localStorage.setItem('token', data.token || '');
        navigate('/dashboard');
      } else {
        setMsg(data.detail || data.error || 'Something went wrong');
        setMsgType('error');
      }
    } catch {
      setMsg('Network error. Please try again.');
      setMsgType('error');
    }
  };

  const setMode = (mode) => {
    setMsg(null);
    setPassword('');
    if (mode !== 'signup') setName('');
    setAuthMode(mode);
  };

  const title    = isReset ? 'Reset password' : isLogin ? 'Welcome back' : 'Create account';
  const subtitle = isReset
    ? 'Enter your email and a new password'
    : isLogin
      ? 'Sign in to your StockiNews account'
      : 'Start your investment research journey';

  return (
    <div className="auth-page">
      {/* ── Left — brand ───────────────────────────────── */}
      <div className="auth-left">
        <div className="auth-brand">
          <img src="/images/logo.png" alt="StockiNews" className="brand-logo" />
          <h1 className="brand-title">
            Stocki<span>News</span>
          </h1>
          <p className="brand-tagline">
            Real-time intelligence for<br />Indian equity markets.
          </p>
        </div>

        <div className="auth-stats">
          <div className="auth-stat">
            <span className="auth-stat-value">5,000+</span>
            <span className="auth-stat-label">NSE tickers</span>
          </div>
          <div className="auth-stat">
            <span className="auth-stat-value">9</span>
            <span className="auth-stat-label">Data layers</span>
          </div>
          <div className="auth-stat">
            <span className="auth-stat-value">AI</span>
            <span className="auth-stat-label">Powered</span>
          </div>
        </div>
      </div>

      {/* ── Right — form ───────────────────────────────── */}
      <div className="auth-right">
        <div className="auth-form-wrap">
          <div className="auth-form-header">
            <h2>{title}</h2>
            <p>{subtitle}</p>
          </div>

          <form onSubmit={handleAuth} className="auth-form">
            {isSignup && (
              <div className="input-group">
                <label className="input-label">Full name</label>
                <input
                  type="text"
                  placeholder="Rajat Sharma"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                  autoComplete="name"
                />
              </div>
            )}

            <div className="input-group">
              <label className="input-label">Email address</label>
              <input
                type="email"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                autoComplete="email"
              />
            </div>

            <div className="input-group">
              <label className="input-label">
                {isReset ? 'New password' : 'Password'}
              </label>
              <input
                type="password"
                placeholder={isReset ? 'Min. 8 characters' : '••••••••'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                autoComplete={isLogin ? 'current-password' : 'new-password'}
              />
            </div>

            <button type="submit" className="auth-submit">
              {isReset ? 'Reset password' : isLogin ? 'Sign in' : 'Create account'}
            </button>

            <div className="auth-divider" />

            <div className="auth-actions">
              {isLogin ? (
                <>
                  <button type="button" className="link-button" onClick={() => setMode('signup')}>
                    No account? <strong>Sign up free</strong>
                  </button>
                  <button type="button" className="link-button" onClick={() => setMode('reset')}>
                    Forgot password?
                  </button>
                </>
              ) : (
                <button type="button" className="link-button" onClick={() => setMode('login')}>
                  Already have an account? <strong>Sign in</strong>
                </button>
              )}
            </div>

            {msg && (
              <div className={`auth-message ${msgType}`}>{msg}</div>
            )}
          </form>
        </div>
      </div>
    </div>
  );
};

export default Login;
