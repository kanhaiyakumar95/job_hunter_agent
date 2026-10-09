import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Lock, User } from 'lucide-react';

export default function Login({ onLoginSuccess }) {
  const [isRegistering, setIsRegistering] = useState(false);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    const endpoint = isRegistering ? '/api/register' : '/api/login';
    try {
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        setError(data.detail || 'Authentication failed');
      } else {
        if (isRegistering) {
          // Auto login after register
          setIsRegistering(false);
          setError("Registration successful! Please log in.");
        } else {
          // Store token and notify parent
          localStorage.setItem('auth_token', data.access_token);
          onLoginSuccess(data.access_token);
        }
      }
    } catch (err) {
      setError("Server error. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh'}}>
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass-card" 
        style={{width: '100%', maxWidth: '400px', padding: '2rem'}}
      >
        <div style={{textAlign: 'center', marginBottom: '2rem'}}>
          <div style={{display: 'inline-block', padding: '15px', borderRadius: '50%', background: 'var(--glass-bg)', border: '1px solid var(--glass-border)', marginBottom: '1rem'}}>
            <Lock size={32} color="var(--accent-primary)" />
          </div>
          <h2>{isRegistering ? 'Create Account' : 'Welcome Back'}</h2>
          <p style={{color: 'var(--text-secondary)'}}>Secure access to Autonomous Job Hunter</p>
        </div>

        {error && <div style={{color: '#ef4444', marginBottom: '1rem', textAlign: 'center', fontSize: '0.9rem'}}>{error}</div>}

        <form onSubmit={handleSubmit} style={{display: 'flex', flexDirection: 'column', gap: '1rem'}}>
          <div style={{position: 'relative'}}>
            <User size={18} style={{position: 'absolute', left: '12px', top: '14px', color: 'var(--text-secondary)'}} />
            <input 
              type="text" 
              placeholder="Username" 
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              style={{
                width: '100%', padding: '12px 12px 12px 40px', 
                background: 'var(--glass-bg)', border: '1px solid var(--glass-border)', 
                borderRadius: '8px', color: 'white', outline: 'none'
              }}
            />
          </div>
          
          <div style={{position: 'relative'}}>
            <Lock size={18} style={{position: 'absolute', left: '12px', top: '14px', color: 'var(--text-secondary)'}} />
            <input 
              type="password" 
              placeholder="Password" 
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              style={{
                width: '100%', padding: '12px 12px 12px 40px', 
                background: 'var(--glass-bg)', border: '1px solid var(--glass-border)', 
                borderRadius: '8px', color: 'white', outline: 'none'
              }}
            />
          </div>

          <button type="submit" className="primary-btn" style={{width: '100%', justifyContent: 'center', marginTop: '0.5rem'}} disabled={loading}>
            {loading ? <div className="spinner" style={{width: '16px', height: '16px', borderWidth: '2px'}}></div> : (isRegistering ? 'Register' : 'Login')}
          </button>
        </form>

        <div style={{textAlign: 'center', marginTop: '1.5rem', fontSize: '0.9rem'}}>
          <span style={{color: 'var(--text-secondary)'}}>
            {isRegistering ? 'Already have an account? ' : "Don't have an account? "}
          </span>
          <button 
            onClick={() => {setIsRegistering(!isRegistering); setError('');}}
            style={{background: 'none', border: 'none', color: 'var(--accent-primary)', cursor: 'pointer', fontWeight: 'bold'}}
          >
            {isRegistering ? 'Log in' : 'Sign up'}
          </button>
        </div>
      </motion.div>
    </div>
  );
}
