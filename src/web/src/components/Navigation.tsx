import React from 'react';
import { AppBar, Toolbar, Typography, Button, Box } from '@mui/material';
import { Link as RouterLink, useLocation } from 'react-router-dom';
import { Assessment, Dashboard, List, Create, CloudUpload, Settings } from '@mui/icons-material';

const Navigation: React.FC = () => {
  const location = useLocation();

  return (
    <AppBar position="static">
      <Toolbar>
        <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
          PM試験AI採点システム
        </Typography>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            component={RouterLink}
            to="/"
            color="inherit"
            startIcon={<Dashboard />}
            sx={{
              backgroundColor: location.pathname === '/' ? 'rgba(255,255,255,0.1)' : 'transparent'
            }}
          >
            ダッシュボード
          </Button>
          <Button
            component={RouterLink}
            to="/answer"
            color="inherit"
            startIcon={<Create />}
            sx={{
              backgroundColor: location.pathname === '/answer' ? 'rgba(255,255,255,0.1)' : 'transparent'
            }}
          >
            解答・採点
          </Button>
          <Button
            component={RouterLink}
            to="/scoring"
            color="inherit"
            startIcon={<List />}
            sx={{
              backgroundColor: location.pathname === '/scoring' ? 'rgba(255,255,255,0.1)' : 'transparent'
            }}
          >
            採点一覧
          </Button>
          <Button
            component={RouterLink}
            to="/batch-upload"
            color="inherit"
            startIcon={<CloudUpload />}
            sx={{
              backgroundColor: location.pathname === '/batch-upload' ? 'rgba(255,255,255,0.1)' : 'transparent'
            }}
          >
            CSV一括アップロード
          </Button>
          <Button
            component={RouterLink}
            to="/admin"
            color="inherit"
            startIcon={<Settings />}
            sx={{
              backgroundColor: location.pathname === '/admin' ? 'rgba(255,255,255,0.1)' : 'transparent'
            }}
          >
            管理者
          </Button>
        </Box>
      </Toolbar>
    </AppBar>
  );
};

export default Navigation;