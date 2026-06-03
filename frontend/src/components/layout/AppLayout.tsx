/**
 * Main application layout component.
 * Sidebar + content area with responsive design.
 */
import React from 'react';
import { Box } from '@mui/material';
import Sidebar from './Sidebar';
import Header from './Header';

interface AppLayoutProps {
  children: React.ReactNode;
}

const AppLayout: React.FC<AppLayoutProps> = ({ children }) => {
  return (
    <Box sx={{ display: 'flex', minHeight: '100vh', bgcolor: 'background.default' }}>
      <Sidebar />
      <Box
        sx={{
          flex: 1,
          minWidth: 0,
          minHeight: '100vh',
          display: 'flex',
          flexDirection: 'column',
          transition: 'flex 0.25s cubic-bezier(0.16, 1, 0.3, 1)',
        }}
      >
        <Header />
        <Box
          component="main"
          sx={{
            flex: 1,
            maxWidth: '960px',
            width: '100%',
            px: { xs: 3, md: 6 },
            py: 0,
          }}
        >
          {children}
        </Box>
      </Box>
    </Box>
  );
};

export default AppLayout;
