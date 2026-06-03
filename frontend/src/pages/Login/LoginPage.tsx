/**
 * Login / Register page.
 * Provides email/password authentication.
 */
import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  TextField,
  Button,
  Typography,
  Tab,
  Tabs,
  Alert,
  InputAdornment,
  IconButton,
} from '@mui/material';
import { Visibility, VisibilityOff, AutoAwesome } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '@/store/authStore';

const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const { login, register, isLoading, error, clearError } = useAuthStore();

  const [tab, setTab] = useState(0);
  const [email, setEmail] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    clearError();
    try {
      if (tab === 0) {
        await login(email, password);
      } else {
        await register(email, username, password);
      }
      navigate('/');
    } catch {
      // Error is handled in the store
    }
  };

  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        bgcolor: '#FAFAF9',
        px: 3,
      }}
    >
      <Card
        sx={{
          maxWidth: 420,
          width: '100%',
          borderRadius: '20px',
          boxShadow: '0 4px 8px rgba(0,0,0,0.04), 0 8px 16px rgba(0,0,0,0.06)',
        }}
      >
        <CardContent sx={{ p: 5 }}>
          {/* Brand */}
          <Box sx={{ textAlign: 'center', mb: 4 }}>
            <AutoAwesome sx={{ fontSize: 40, color: 'primary.main', mb: 1 }} />
            <Typography
              variant="h4"
              sx={{ fontWeight: 600, color: 'primary.main', letterSpacing: '-0.01em' }}
            >
              TopicAI
            </Typography>
            <Typography variant="body2" sx={{ color: 'text.secondary', mt: 0.5 }}>
              智能选题推荐Agent
            </Typography>
          </Box>

          {/* Tabs */}
          <Tabs
            value={tab}
            onChange={(_, v) => {
              setTab(v);
              clearError();
            }}
            variant="fullWidth"
            sx={{ mb: 3, '& .MuiTab-root': { textTransform: 'none', fontWeight: 500 } }}
          >
            <Tab label="登录" />
            <Tab label="注册" />
          </Tabs>

          {/* Error alert */}
          {error && (
            <Alert severity="error" sx={{ mb: 2, borderRadius: 2 }} onClose={clearError}>
              {error}
            </Alert>
          )}

          {/* Form */}
          <Box component="form" onSubmit={handleSubmit}>
            <TextField
              fullWidth
              label="邮箱"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              size="small"
              sx={{ mb: 2 }}
            />

            {tab === 1 && (
              <TextField
                fullWidth
                label="用户名"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                size="small"
                inputProps={{ minLength: 3, maxLength: 50 }}
                sx={{ mb: 2 }}
              />
            )}

            <TextField
              fullWidth
              label="密码"
              type={showPassword ? 'text' : 'password'}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              size="small"
              inputProps={{ minLength: 8 }}
              sx={{ mb: 3 }}
              InputProps={{
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton
                      aria-label={showPassword ? '隐藏密码' : '显示密码'}
                      size="small"
                      onClick={() => setShowPassword(!showPassword)}
                      edge="end"
                    >
                      {showPassword ? <VisibilityOff fontSize="small" /> : <Visibility fontSize="small" />}
                    </IconButton>
                  </InputAdornment>
                ),
              }}
            />

            <Button
              type="submit"
              fullWidth
              variant="contained"
              size="large"
              disabled={isLoading}
              sx={{
                py: 1.5,
                fontSize: '0.9375rem',
                fontWeight: 500,
              }}
            >
              {isLoading ? '处理中...' : tab === 0 ? '登录' : '注册'}
            </Button>
          </Box>

          <Typography
            variant="caption"
            sx={{ display: 'block', textAlign: 'center', mt: 3, color: 'text.disabled' }}
          >
            每日免费 20 次 AI 调用 · 无需信用卡
          </Typography>
        </CardContent>
      </Card>
    </Box>
  );
};

export default LoginPage;
