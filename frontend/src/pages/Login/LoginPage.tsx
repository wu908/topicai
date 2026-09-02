/**
 * Login / Register — 原型 hifi-lumen.html 中央玻璃卡对齐。
 * 登录态为默认视图（占位符输入 + 胶囊「进入」）；注册以弱化链接切换。
 * E2E 契约：#login-email / #login-password；按钮文案「进入」（spec 同步）。
 */
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '@/store/authStore';

type Mode = 'login' | 'register';

const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const { login, register, isLoading, error, clearError } = useAuthStore();

  const [mode, setMode] = useState<Mode>('login');
  const [email, setEmail] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [formError, setFormError] = useState<string | null>(null);

  const switchMode = (next: Mode) => {
    setMode(next);
    clearError();
    setFormError(null);
  };

  const handleSubmit = async (e: React.FormEvent): Promise<void> => {
    e.preventDefault();
    clearError();
    setFormError(null);
    if (mode === 'register') {
      if (username.trim().length < 2) {
        setFormError('姓名至少需要 2 个字符，两个字的中文姓名也可以。');
        return;
      }
      if (password.length < 8) {
        setFormError('密码至少需要 8 位字符。');
        return;
      }
      if (confirmPassword !== password) {
        setFormError('两次输入的密码不一致，请检查后重新提交。');
        return;
      }
    }
    try {
      if (mode === 'login') {
        await login(email, password);
      } else {
        await register(email, username, password);
      }
      navigate('/');
    } catch {
      // Error is rendered from the store; nothing else to do here.
    }
  };

  return (
    <div className="lm-body lm-login">
      <div className="login-box glass">
        <div className="mark">T</div>
        <h1>TopicAI</h1>
        <p className="sub">把灵感交给它，把时间还给你。</p>

        {(formError || error) && (
          <p className="login-err" role="alert">{formError || error}</p>
        )}

        <form onSubmit={handleSubmit}>
          <input
            id="login-email"
            type="email"
            placeholder="邮箱"
            aria-label="邮箱"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
          {mode === 'register' && (
            <input
              id="login-username"
              type="text"
              placeholder="你的姓名"
              aria-label="姓名"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              maxLength={50}
            />
          )}
          <input
            id="login-password"
            type="password"
            placeholder={mode === 'register' ? '密码（至少 8 位）' : '密码'}
            aria-label="密码"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
          {mode === 'register' && (
            <input
              id="login-confirm-password"
              type="password"
              placeholder="再输入一次密码"
              aria-label="确认密码"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
              autoComplete="new-password"
            />
          )}
          <button className="btn btn-primary" type="submit" disabled={isLoading}>
            {isLoading ? '处理中…' : mode === 'login' ? '进入' : '创建账号'}
          </button>
        </form>

        <p className="login-hint">本地单机 · 数据不出你的电脑（素材授权默认最小）</p>
        <button
          type="button"
          className="login-alt"
          onClick={() => switchMode(mode === 'login' ? 'register' : 'login')}
        >
          {mode === 'login' ? '没有账号？注册' : '已有账号？登录'}
        </button>
      </div>
    </div>
  );
};

export default LoginPage;
