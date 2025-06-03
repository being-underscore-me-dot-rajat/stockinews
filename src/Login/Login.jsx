import '../App.css';
import './Login.css'
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Footer from '../home/navbar/footer/Footer';

const Login = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [msg, setMsg] = useState(null);
  const navigate = useNavigate();

  const handleAuth = async (e) => {
    e.preventDefault();
    setMsg(null);

    const url = isLogin ? 'http://localhost:5000/login' : 'http://localhost:5000/signup';
    const payload = isLogin
      ? { email, password }
      : { name, email, password };

    try {
      const res = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      const data = await res.json();

      if (res.ok) {
        localStorage.setItem('token', data.token || '');
        navigate("/dashboard")

      } else {
        setMsg(data.error || 'Something went wrong');
      }
    } catch (err) {
      console.error(err);
      setMsg('❌ Network error.');
    }
  };

  return (
    <>
      <div className="auth-page">
        <div className="auth-left">
          <img src="/images/logo.png" alt="Stockinews Logo" className="brand-logo" />
          <h1 className="brand-title">Stockinews</h1>
          <p className="brand-tagline">Smart Sentiments. Smarter Investments.</p>
        </div>

        <div className="auth-right">
          <form onSubmit={handleAuth} className="auth-form">
            <h2>{isLogin ? 'Login' : 'Sign Up'} to Stockinews</h2>

            {!isLogin && (
              <input
                type="text"
                placeholder="Name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
              />
            )}

            <input
              type="email"
              placeholder="Email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />

            <input
              type="password"
              placeholder="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />

            <button type="submit">{isLogin ? 'Login' : 'Sign Up'}</button>
            <p
              onClick={() => setIsLogin(!isLogin)}
              style={{ cursor: 'pointer', color: 'var(--accent-blue)', marginTop: '1rem' }}
            >
              {isLogin ? "Don't have an account? Sign Up" : 'Already have an account? Login'}
            </p>

            {msg && <p className="message">{msg}</p>}
          </form>
        </div>
      </div>
      <Footer />
    </>
  );
};

export default Login;
