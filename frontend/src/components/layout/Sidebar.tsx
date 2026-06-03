/**
 * Sidebar navigation component.
 * Collapsible sidebar with sectioned navigation items.
 */
import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  Box,
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Typography,
  Divider,
  Avatar,
  IconButton,
} from '@mui/material';
import {
  Home as HomeIcon,
  Lightbulb,
  TrendingUp,
  Psychology,
  Title,
  Analytics,
  Schedule,
  Person,
  Assessment,
  MenuOpen,
} from '@mui/icons-material';
import { useAuthStore } from '@/store/authStore';
import { useAppStore } from '@/store/appStore';

const NAV_SECTIONS = [
  {
    label: '核心功能',
    items: [
      { path: '/', label: '首页', icon: <HomeIcon /> },
      { path: '/topics', label: '选题推荐', icon: <Lightbulb /> },
      { path: '/viral', label: '爆款拆解', icon: <TrendingUp /> },
      { path: '/ideas', label: '想法推进', icon: <Psychology /> },
    ],
  },
  {
    label: '辅助工具',
    items: [
      { path: '/titles', label: '标题优化', icon: <Title /> },
      { path: '/tracks', label: '赛道诊断', icon: <Analytics /> },
      { path: '/publish', label: '发布时间', icon: <Schedule /> },
    ],
  },
  {
    label: '个人中心',
    items: [
      { path: '/profile', label: '创作画像', icon: <Person /> },
      { path: '/review', label: '效果复盘', icon: <Assessment /> },
    ],
  },
];

const Sidebar: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const user = useAuthStore((s) => s.user);
  const sidebarOpen = useAppStore((s) => s.sidebarOpen);
  const toggleSidebar = useAppStore((s) => s.toggleSidebar);

  return (
    <Drawer
      variant="permanent"
      sx={{
        width: sidebarOpen ? 240 : 64,
        flexShrink: 0,
        '& .MuiDrawer-paper': {
          width: sidebarOpen ? 240 : 64,
          transition: 'width 0.25s cubic-bezier(0.16, 1, 0.3, 1)',
          overflowX: 'hidden',
          borderRight: '1px solid',
          borderColor: 'divider',
          bgcolor: '#F5F5F4',
        },
      }}
    >
      {/* Brand */}
      <Box
        sx={{
          p: sidebarOpen ? 2.5 : 1.5,
          borderBottom: '1px solid',
          borderColor: 'grey.200',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        {sidebarOpen && (
          <Box>
            <Typography
              variant="h6"
              sx={{
                color: 'primary.main',
                fontWeight: 600,
                fontSize: '1.25rem',
                letterSpacing: '-0.01em',
              }}
            >
              TopicAI
            </Typography>
            <Typography
              variant="caption"
              sx={{ color: 'text.disabled', fontSize: '0.6875rem' }}
            >
              智能选题推荐Agent
            </Typography>
          </Box>
        )}
        <IconButton aria-label="折叠侧边栏" onClick={toggleSidebar} size="small" sx={{ color: 'text.secondary' }}>
          <MenuOpen fontSize="small" sx={{ transform: sidebarOpen ? 'none' : 'rotate(180deg)' }} />
        </IconButton>
      </Box>

      {/* Navigation */}
      <Box sx={{ flex: 1, overflowY: 'auto', py: 1 }}>
        {NAV_SECTIONS.map((section) => (
          <Box key={section.label}>
            {sidebarOpen && (
              <Typography
                variant="caption"
                sx={{
                  px: 2.5,
                  py: 1.5,
                  pb: 0.5,
                  display: 'block',
                  color: 'text.disabled',
                  fontSize: '0.625rem',
                  fontWeight: 500,
                  textTransform: 'uppercase',
                  letterSpacing: '0.02em',
                }}
              >
                {section.label}
              </Typography>
            )}
            <List disablePadding>
              {section.items.map((item) => {
                const isActive = location.pathname === item.path;
                return (
                  <ListItem key={item.path} disablePadding sx={{ px: 1.5, mb: 0.1 }}>
                    <ListItemButton
                      onClick={() => navigate(item.path)}
                      sx={{
                        borderRadius: 1,
                        py: sidebarOpen ? 1.2 : 1.5,
                        px: sidebarOpen ? 2 : 1.5,
                        justifyContent: sidebarOpen ? 'flex-start' : 'center',
                        bgcolor: isActive ? 'primary.light' : 'transparent',
                        color: isActive ? 'primary.main' : 'text.secondary',
                        '&:hover': {
                          bgcolor: isActive ? 'primary.light' : 'grey.200',
                          color: isActive ? 'primary.main' : 'text.primary',
                        },
                        transition: 'all 0.15s ease',
                      }}
                    >
                      <ListItemIcon
                        sx={{
                          minWidth: sidebarOpen ? 36 : 0,
                          color: 'inherit',
                          '& .MuiSvgIcon-root': { fontSize: 18 },
                        }}
                      >
                        {item.icon}
                      </ListItemIcon>
                      {sidebarOpen && (
                        <ListItemText
                          primary={item.label}
                          primaryTypographyProps={{
                            fontSize: '0.8125rem',
                            fontWeight: isActive ? 500 : 400,
                          }}
                        />
                      )}
                    </ListItemButton>
                  </ListItem>
                );
              })}
            </List>
          </Box>
        ))}
      </Box>

      {/* Footer — User info */}
      <Divider />
      <Box sx={{ p: sidebarOpen ? 2 : 1, display: 'flex', alignItems: 'center', gap: 1.5 }}>
        <Avatar
          sx={{
            width: 32,
            height: 32,
            bgcolor: 'primary.light',
            color: 'primary.main',
            fontSize: '0.75rem',
            fontWeight: 500,
          }}
        >
          {user?.username?.charAt(0)?.toUpperCase() || 'U'}
        </Avatar>
        {sidebarOpen && (
          <Typography
            variant="body2"
            sx={{ color: 'text.secondary', fontSize: '0.8125rem', overflow: 'hidden' }}
          >
            {user?.username || '未登录'}
          </Typography>
        )}
      </Box>
    </Drawer>
  );
};

export default Sidebar;
