import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Container,
  Typography,
  Card,
  CardContent,
  Grid,
  Chip,
  Button,
  Box,
  Alert,
  CircularProgress,
  Divider
} from '@mui/material';
import { ArrowBack } from '@mui/icons-material';
import { apiService } from '../services/apiService';

interface ScoringResult {
  id: number;
  answer_id: number;
  status: string;
  total_score: number | null;
  max_score: number | null;
  percentage: number | null;
  confidence: number | null;
  rule_based_score: number | null;
  semantic_score: number | null;
  comprehensive_score: number | null;
  is_reviewed: boolean;
  final_score: number | null;
  grade: string;
}

const ScoringDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [result, setResult] = useState<ScoringResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchResult = async () => {
      if (!id) return;

      try {
        const data = await apiService.getScoringResult(parseInt(id));
        setResult(data);
      } catch (err) {
        setError('採点結果の取得に失敗しました');
      } finally {
        setLoading(false);
      }
    };

    fetchResult();
  }, [id]);

  if (loading) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4, display: 'flex', justifyContent: 'center' }}>
        <CircularProgress />
      </Container>
    );
  }

  if (error || !result) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4 }}>
        <Alert severity="error">
          {error || '採点結果が見つかりません'}
        </Alert>
        <Button
          startIcon={<ArrowBack />}
          onClick={() => navigate('/scoring')}
          sx={{ mt: 2 }}
        >
          一覧に戻る
        </Button>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Box display="flex" alignItems="center" mb={3}>
        <Button
          startIcon={<ArrowBack />}
          onClick={() => navigate('/scoring')}
          sx={{ mr: 2 }}
        >
          戻る
        </Button>
        <Typography variant="h4" component="h1">
          採点結果詳細 #{result.id}
        </Typography>
      </Box>

      <Grid container spacing={3}>
        {/* 基本情報 */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                基本情報
              </Typography>
              <Box mb={2}>
                <Typography variant="body2" color="text.secondary">
                  解答ID: {result.answer_id}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  状態: <Chip label={result.status} size="small" />
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  レビュー状態: {result.is_reviewed ? 'レビュー済み' : '未レビュー'}
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* スコア情報 */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                総合スコア
              </Typography>
              <Box display="flex" alignItems="center" mb={2}>
                <Typography variant="h3" component="div" sx={{ mr: 2 }}>
                  {result.final_score !== null
                    ? result.final_score.toFixed(1)
                    : 'N/A'
                  }
                </Typography>
                <Box>
                  <Typography variant="body1">
                    / {result.max_score || 'N/A'} 点
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {result.percentage !== null
                      ? `${result.percentage.toFixed(1)}%`
                      : 'N/A'
                    }
                  </Typography>
                </Box>
              </Box>
              <Box display="flex" alignItems="center" gap={1}>
                <Typography variant="body2">成績:</Typography>
                <Chip label={result.grade} color="primary" />
              </Box>
              {result.confidence !== null && (
                <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                  信頼度: {(result.confidence * 100).toFixed(1)}%
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* 詳細スコア */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                詳細スコア
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={4}>
                  <Box textAlign="center" p={2} border={1} borderColor="grey.300" borderRadius={1}>
                    <Typography variant="h6">
                      {result.rule_based_score !== null
                        ? result.rule_based_score.toFixed(1)
                        : 'N/A'
                      }
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      ルールベース (30%)
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={12} sm={4}>
                  <Box textAlign="center" p={2} border={1} borderColor="grey.300" borderRadius={1}>
                    <Typography variant="h6">
                      {result.semantic_score !== null
                        ? result.semantic_score.toFixed(1)
                        : 'N/A'
                      }
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      意味理解 (40%)
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={12} sm={4}>
                  <Box textAlign="center" p={2} border={1} borderColor="grey.300" borderRadius={1}>
                    <Typography variant="h6">
                      {result.comprehensive_score !== null
                        ? result.comprehensive_score.toFixed(1)
                        : 'N/A'
                      }
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      総合評価 (30%)
                    </Typography>
                  </Box>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* 将来の拡張用（採点理由、改善提案など） */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                採点詳細情報
              </Typography>
              <Typography variant="body2" color="text.secondary">
                詳細な採点理由や改善提案は今後の実装で追加予定です。
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Container>
  );
};

export default ScoringDetail;