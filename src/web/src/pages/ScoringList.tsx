import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  Button,
  Box,
  Alert,
  CircularProgress
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { Visibility, RateReview, Download, Assessment } from '@mui/icons-material';
import { apiService } from '../services/apiService';

interface ScoringResult {
  id: number;
  answer_id: number;
  status: string;
  total_score: number | null;
  max_score: number | null;
  percentage: number | null;
  confidence: number | null;
  is_reviewed: boolean;
  grade: string;
}

const ScoringList: React.FC = () => {
  const [results, setResults] = useState<ScoringResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [exporting, setExporting] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchResults = async () => {
      try {
        // 仮のexam_id=1で採点結果を取得
        const data = await apiService.getScoringResults(1);
        setResults(data);
      } catch (err) {
        setError('採点結果の取得に失敗しました');
      } finally {
        setLoading(false);
      }
    };

    fetchResults();
  }, []);

  const getStatusChip = (status: string) => {
    const statusMap: { [key: string]: { label: string; color: any } } = {
      pending: { label: '待機中', color: 'default' },
      in_progress: { label: '処理中', color: 'info' },
      completed: { label: '完了', color: 'success' },
      failed: { label: '失敗', color: 'error' },
      reviewed: { label: 'レビュー済み', color: 'primary' }
    };

    const statusInfo = statusMap[status] || { label: status, color: 'default' };
    return <Chip label={statusInfo.label} color={statusInfo.color} size="small" />;
  };

  const getGradeChip = (grade: string) => {
    const gradeColors: { [key: string]: any } = {
      'A': 'success',
      'B': 'info',
      'C': 'warning',
      'D': 'warning',
      'F': 'error'
    };

    return (
      <Chip
        label={grade}
        color={gradeColors[grade] || 'default'}
        size="small"
        variant="outlined"
      />
    );
  };

  const handleExport = async (reviewedOnly: boolean = false) => {
    setExporting(true);
    try {
      const examId = 1; // 実際には動的に設定
      const url = `/api/export/scoring-results/${examId}?format=csv&reviewed_only=${reviewedOnly}`;

      const response = await fetch(url);
      if (!response.ok) {
        throw new Error('エクスポートに失敗しました');
      }

      const blob = await response.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = `採点結果_${new Date().toISOString().split('T')[0]}.csv`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(downloadUrl);

    } catch (error) {
      console.error('Export error:', error);
      alert('エクスポートに失敗しました');
    } finally {
      setExporting(false);
    }
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
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1">
          採点結果一覧
        </Typography>
        <Box display="flex" gap={2}>
          <Button
            variant="outlined"
            startIcon={<Assessment />}
            onClick={() => window.open('/api/export/summary/1', '_blank')}
          >
            統計レポート
          </Button>
          <Button
            variant="outlined"
            startIcon={<Download />}
            onClick={() => handleExport(false)}
            disabled={exporting}
          >
            {exporting ? 'エクスポート中...' : '全件CSV出力'}
          </Button>
          <Button
            variant="contained"
            startIcon={<Download />}
            onClick={() => handleExport(true)}
            disabled={exporting}
          >
            レビュー済みCSV出力
          </Button>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>ID</TableCell>
              <TableCell>解答ID</TableCell>
              <TableCell>状態</TableCell>
              <TableCell>スコア</TableCell>
              <TableCell>割合</TableCell>
              <TableCell>信頼度</TableCell>
              <TableCell>成績</TableCell>
              <TableCell>レビュー</TableCell>
              <TableCell>操作</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {results.length === 0 ? (
              <TableRow>
                <TableCell colSpan={9} align="center">
                  <Typography variant="body2" color="text.secondary">
                    採点結果がありません
                  </Typography>
                </TableCell>
              </TableRow>
            ) : (
              results.map((result) => (
                <TableRow key={result.id}>
                  <TableCell>{result.id}</TableCell>
                  <TableCell>{result.answer_id}</TableCell>
                  <TableCell>{getStatusChip(result.status)}</TableCell>
                  <TableCell>
                    {result.total_score !== null && result.max_score !== null
                      ? `${result.total_score.toFixed(1)}/${result.max_score}`
                      : '-'
                    }
                  </TableCell>
                  <TableCell>
                    {result.percentage !== null
                      ? `${result.percentage.toFixed(1)}%`
                      : '-'
                    }
                  </TableCell>
                  <TableCell>
                    {result.confidence !== null
                      ? `${(result.confidence * 100).toFixed(1)}%`
                      : '-'
                    }
                  </TableCell>
                  <TableCell>{getGradeChip(result.grade)}</TableCell>
                  <TableCell>
                    <Chip
                      label={result.is_reviewed ? '済' : '未'}
                      color={result.is_reviewed ? 'success' : 'default'}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    <Box display="flex" gap={1}>
                      <Button
                        size="small"
                        startIcon={<Visibility />}
                        onClick={() => navigate(`/scoring/${result.id}`)}
                      >
                        詳細
                      </Button>
                      <Button
                        size="small"
                        variant="outlined"
                        color="primary"
                        startIcon={<RateReview />}
                        onClick={() => navigate(`/scoring/${result.id}/review`)}
                      >
                        2次採点
                      </Button>
                    </Box>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>
    </Container>
  );
};

export default ScoringList;