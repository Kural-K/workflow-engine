import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import { Zap, Lock, User, ArrowRight, Eye, EyeOff } from 'lucide-react';

// Demo credentials
const USERS = [
  { username: 'admin', password: 'admin123', role: 'Admin' },
  { username: 'manager', password: 'manager123', role: 'Manager' },
  { username: 'user', password: 'user123', role: 'User' },
];

export default function Login({ onLogin }) {
  const [form, setForm] = useState({ username: '', password: '' });
  const [showPass, setShowPass] = useState(false);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    if (!form.username || !form.password) return toast.error('Please fill in all fields');
    setLoading(true);
    await new Promise(r => setTimeout(r, 800)); // simulate API call
    const user = USERS.find(u => u.username === form.username && u.password === form.password);
    if (user) {
      localStorage.setItem('fe_user', JSON.stringify(user));
      onLogin(user);
      toast.success(`Welcome back, ${user.username}! 👋`);
      navigate('/workflows');
    } else {
      toast.error('Invalid username or password');
    }
    setLoading(false);
  };

  return (
    <div style={{
      minHeight: '100vh',
      background: 'var(--bg)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '20px',
      backgroundImage: `
        radial-gradient(ellipse at 20% 20%, rgba(124,58,237,0.15) 0%, transparent 50%),
        radial-gradient(ellipse at 80% 80%, rgba(232,121,249,0.1) 0%, transparent 50%)
      `,
      fontFamily: 'var(--sans)',
    }}>
      {/* Animated bg dots */}
      <div style={{ position: 'fixed', inset: 0, overflow: 'hidden', pointerEvents: 'none' }}>
        {[...Array(6)].map((_, i) => (
          <div key={i} style={{
            position: 'absolute',
            width: `${200 + i * 80}px`,
            height: `${200 + i * 80}px`,
            borderRadius: '50%',
            border: '1px solid rgba(124,58,237,0.06)',
            top: `${10 + i * 12}%`,
            left: `${5 + i * 10}%`,
            animation: `float ${6 + i}s ease-in-out infinite alternate`,
          }} />
        ))}
      </div>

      <div style={{ width: '100%', maxWidth: '420px', position: 'relative', zIndex: 1 }}>
        {/* Logo */}
        <div style={{ textAlign: 'center', marginBottom: 36 }}>
          <div style={{
            width: 60, height: 60,
            background: 'linear-gradient(135deg, var(--accent), var(--pink))',
            borderRadius: 16,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: 28,
            margin: '0 auto 16px',
            boxShadow: '0 0 40px rgba(124,58,237,0.4)',
          }}>⚡</div>
          <h1 style={{
            fontFamily: 'var(--mono)',
            fontSize: 26,
            fontWeight: 800,
            background: 'linear-gradient(135deg, var(--text), var(--accent3))',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            marginBottom: 6,
          }}>FlowEngine</h1>
          <p style={{ color: 'var(--text3)', fontSize: 14 }}>Workflow Automation System</p>
        </div>

        {/* Card */}
        <div style={{
          background: 'var(--bg2)',
          border: '1px solid var(--border2)',
          borderRadius: 20,
          padding: '32px',
          boxShadow: '0 20px 60px rgba(0,0,0,0.5), 0 0 0 1px rgba(124,58,237,0.1)',
        }}>
          <h2 style={{
            fontFamily: 'var(--mono)',
            fontSize: 18,
            fontWeight: 700,
            color: 'var(--text)',
            marginBottom: 6,
          }}>Welcome back</h2>
          <p style={{ color: 'var(--text3)', fontSize: 13.5, marginBottom: 28 }}>
            Sign in to your account to continue
          </p>

          <form onSubmit={handleLogin}>
            {/* Username */}
            <div className="form-group">
              <label>Username</label>
              <div style={{ position: 'relative' }}>
                <User size={15} style={{
                  position: 'absolute', left: 12, top: '50%',
                  transform: 'translateY(-50%)', color: 'var(--text3)'
                }} />
                <input
                  type="text"
                  placeholder="Enter your username"
                  value={form.username}
                  onChange={e => setForm(f => ({ ...f, username: e.target.value }))}
                  style={{ paddingLeft: 36 }}
                />
              </div>
            </div>

            {/* Password */}
            <div className="form-group" style={{ marginBottom: 24 }}>
              <label>Password</label>
              <div style={{ position: 'relative' }}>
                <Lock size={15} style={{
                  position: 'absolute', left: 12, top: '50%',
                  transform: 'translateY(-50%)', color: 'var(--text3)'
                }} />
                <input
                  type={showPass ? 'text' : 'password'}
                  placeholder="Enter your password"
                  value={form.password}
                  onChange={e => setForm(f => ({ ...f, password: e.target.value }))}
                  style={{ paddingLeft: 36, paddingRight: 40 }}
                />
                <button type="button" onClick={() => setShowPass(s => !s)} style={{
                  position: 'absolute', right: 12, top: '50%',
                  transform: 'translateY(-50%)',
                  background: 'none', border: 'none',
                  color: 'var(--text3)', cursor: 'pointer', padding: 0,
                  display: 'flex', alignItems: 'center',
                }}>
                  {showPass ? <EyeOff size={15} /> : <Eye size={15} />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              className="btn btn-primary"
              disabled={loading}
              style={{ width: '100%', justifyContent: 'center', padding: '11px 18px', fontSize: 14 }}
            >
              {loading ? 'Signing in...' : <>Sign In <ArrowRight size={15} /></>}
            </button>
          </form>

          {/* Demo credentials */}
          <div style={{
            marginTop: 24,
            padding: '14px 16px',
            background: 'rgba(124,58,237,0.08)',
            border: '1px solid rgba(124,58,237,0.2)',
            borderRadius: 10,
          }}>
            <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--accent3)', marginBottom: 8, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
              Demo Credentials
            </div>
            {USERS.map(u => (
              <div key={u.username}
                onClick={() => setForm({ username: u.username, password: u.password })}
                style={{
                  display: 'flex', justifyContent: 'space-between',
                  fontSize: 12.5, color: 'var(--text2)', padding: '4px 0',
                  cursor: 'pointer', borderRadius: 4,
                  transition: 'color 0.15s',
                }}
                onMouseEnter={e => e.currentTarget.style.color = 'var(--text)'}
                onMouseLeave={e => e.currentTarget.style.color = 'var(--text2)'}
              >
                <span style={{ fontFamily: 'var(--mono)', fontSize: 12 }}>
                  {u.username} / {u.password}
                </span>
                <span className="badge badge-purple" style={{ fontSize: 10, padding: '1px 7px' }}>{u.role}</span>
              </div>
            ))}
            <div style={{ fontSize: 11, color: 'var(--text3)', marginTop: 6 }}>
              💡 Click any row to auto-fill
            </div>
          </div>
        </div>
      </div>

      <style>{`
        @keyframes float {
          from { transform: translateY(0px) rotate(0deg); }
          to { transform: translateY(-20px) rotate(5deg); }
        }
      `}</style>
    </div>
  );
}
