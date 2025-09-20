import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Grid,
  Card,
  CardContent,
  Box,
  Alert,
  CircularProgress
} from '@mui/material';
import { Assessment, CheckCircle, Error, Schedule } from '@mui/icons-material';
import { apiService } from '../services/apiService';

interface SystemStatus {
  status: string;
  uptime_seconds: number;
  environment: string;
  services?: {
    database: { status: string };
    redis: { status: string };
    ai_engine: { status: string };
  };
}

const Dashboard: React.FC = () => {
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchSystemStatus = async () => {
      try {
        const status = await apiService.getHealthStatus();
        setSystemStatus(status);
      } catch (err) {
        setError('システム状態の取得に失敗しました');
      } finally {
        setLoading(false);
      }
    };

    fetchSystemStatus();
    const interval = setInterval(fetchSystemStatus, 30000); // 30秒ごとに更新

    return () => clearInterval(interval);
  }, []);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircle color="success" />;
      case 'degraded':
        return <Schedule color="warning" />;
      case 'unhealthy':
        return <Error color="error" />;
      default:
        return <CircularProgress size={20} />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'success';
      case 'degraded':
        return 'warning';
      case 'unhealthy':
        return 'error';
      default:
        return 'info';
    }
  };

  const formatUptime = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours}時間${minutes}分`;
  };

  if (loading) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4, display: 'flex', justifyContent: 'center' }}>
        <CircularProgress />
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        ダッシュボード
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* システム状態カード */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" mb={2}>
                <Assessment sx={{ mr: 1 }} />
                <Typography variant="h6">システム状態</Typography>
              </Box>

              {systemStatus && (
                <>
                  <Box display="flex" alignItems="center" mb={1}>
                    {getStatusIcon(systemStatus.status)}
                    <Typography variant="body1" sx={{ ml: 1 }}>
                      全体状態: {systemStatus.status}
                    </Typography>
                  </Box>

                  <Typography variant="body2" color="text.secondary">
                    稼働時間: {formatUptime(systemStatus.uptime_seconds)}
                  </Typography>

                  <Typography variant="body2" color="text.secondary">
                    環境: {systemStatus.environment}
                  </Typography>
                </>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* サービス状態カード */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                サービス状態
              </Typography>

              {systemStatus?.services && (
                <Box>
                  {Object.entries(systemStatus.services).map(([service, info]) => (
                    <Box key={service} display="flex" alignItems="center" mb={1}>
                      {getStatusIcon(info.status)}
                      <Typography variant="body2" sx={{ ml: 1 }}>
                        {service}: {info.status}
                      </Typography>
                    </Box>
                  ))}
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* 統計情報カード（将来の拡張用） */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                採点統計
              </Typography>
              <Typography variant="body2" color="text.secondary">
                統計情報は今後の実装で追加予定です。
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Container>
  );
};

export default Dashboard;