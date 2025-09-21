import React, { useState } from 'react';
import {
  Container,
  Typography,
  Paper,
  Box,
  TextField,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Card,
  CardContent,
  Grid,
  Chip,
  CircularProgress,
  Alert,
  Divider
} from '@mui/material';
import { Assessment, Send, Clear } from '@mui/icons-material';
import { apiService } from '../services/apiService';

interface Question {
  id: number;
  exam_id: number;
  title: string;
  question_number: string;
  background_text: string;
  question_text: string;
  sub_questions: string[] | null;
  model_answer: string;
  max_chars: number;
  points: number;
  grading_intention: string | null;
  grading_commentary: string | null;
  keywords: string[] | null;
  has_sub_questions: boolean;
  display_name: string;
}

interface ScoringResult {
  id: number;
  total_score: number;
  max_score: number;
  percentage: number;
  confidence: number;
  grade: string;
  detailed_feedback?: string;
  aspect_scores?: Record<string, number>;
}

// データベースから問題を取得する

const AnswerSubmission: React.FC = () => {
  const [selectedQuestion, setSelectedQuestion] = useState<Question | null>(null);
  const [candidateId, setCandidateId] = useState<string>('');
  const [answerText, setAnswerText] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [scoringResult, setScoringResult] = useState<ScoringResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isScoring, setIsScoring] = useState<boolean>(false);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  // 問題を取得
  const fetchQuestions = async () => {
    try {
      setLoading(true);
      // 試験ID=1から問題を取得（実際にはプルダウンで選択可能にすることも可能）
      const response = await fetch('/api/admin/questions?exam_id=1');
      if (response.ok) {
        const data = await response.json();
        setQuestions(data);
      } else {
        setError('問題の取得に失敗しました');
      }
    } catch (err) {
      setError('問題の取得中にエラーが発生しました');
    } finally {
      setLoading(false);
    }
  };

  // コンポーネント読み込み時に問題を取得
  React.useEffect(() => {
    fetchQuestions();
  }, []);

  const handleQuestionSelect = (questionId: number) => {
    const question = questions.find(q => q.id === questionId);
    setSelectedQuestion(question || null);
    setAnswerText('');
    setScoringResult(null);
    setError(null);
  };

  const handleSubmitAnswer = async () => {
    if (!selectedQuestion || !candidateId.trim() || !answerText.trim()) {
      setError('すべての項目を入力してください');
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      // 解答提出
      const submission = await apiService.submitAnswer({
        exam_id: 1,
        question_id: selectedQuestion.id,
        candidate_id: candidateId,
        answer_text: answerText
      });

      // AI採点実行
      setIsScoring(true);
      const evaluation = await apiService.evaluateAnswer({
        answer_id: submission.id
      });

      setScoringResult(evaluation);

    } catch (err: any) {
      setError(err.message || '採点処理に失敗しました');
    } finally {
      setIsSubmitting(false);
      setIsScoring(false);
    }
  };

  const handleClear = () => {
    setAnswerText('');
    setScoringResult(null);
    setError(null);
  };

  const getGradeColor = (grade: string) => {
    switch (grade) {
      case 'A': return 'success';
      case 'B': return 'info';
      case 'C': return 'warning';
      case 'D': return 'error';
      default: return 'default';
    }
  };

  const getScoreColor = (percentage: number) => {
    if (percentage >= 80) return 'success';
    if (percentage >= 60) return 'info';
    if (percentage >= 40) return 'warning';
    return 'error';
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        PM試験AI採点システム
      </Typography>

      <Grid container spacing={3}>
        {/* 問題選択・解答入力エリア */}
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              解答入力
            </Typography>

            {/* 受験者ID入力 */}
            <TextField
              fullWidth
              label="受験者ID"
              value={candidateId}
              onChange={(e) => setCandidateId(e.target.value)}
              sx={{ mb: 2 }}
              placeholder="例: PM2024001"
            />

            {/* 問題選択 */}
            <FormControl fullWidth sx={{ mb: 2 }}>
              <InputLabel>問題を選択</InputLabel>
              <Select
                value={selectedQuestion?.id || ''}
                onChange={(e) => handleQuestionSelect(Number(e.target.value))}
                label="問題を選択"
                disabled={loading}
              >
                {loading ? (
                  <MenuItem disabled>
                    <CircularProgress size={20} sx={{ mr: 1 }} />
                    問題を読み込み中...
                  </MenuItem>
                ) : (
                  questions.map((question) => (
                    <MenuItem key={question.id} value={question.id}>
                      {question.display_name} ({question.max_chars}字以内)
                    </MenuItem>
                  ))
                )}
              </Select>
            </FormControl>

            {/* 選択された問題の表示 */}
            {selectedQuestion && (
              <Card sx={{ mb: 2, bgcolor: 'grey.50' }}>
                <CardContent>
                  <Box display="flex" alignItems="center" mb={2}>
                    <Assessment color="primary" sx={{ mr: 1 }} />
                    <Typography variant="h6">
                      {selectedQuestion.question_number}: {selectedQuestion.title}
                    </Typography>
                    <Chip
                      label={`${selectedQuestion.points}点`}
                      size="small"
                      color="primary"
                      sx={{ ml: 1 }}
                    />
                  </Box>

                  {/* 背景情報 */}
                  {selectedQuestion.background_text && (
                    <>
                      <Typography variant="subtitle2" sx={{ fontWeight: 'bold', color: 'primary.main', mb: 1 }}>
                        【背景情報・プロジェクト概要】
                      </Typography>
                      <Typography variant="body2" sx={{ mb: 2, whiteSpace: 'pre-line', bgcolor: 'background.paper', p: 2, borderRadius: 1 }}>
                        {selectedQuestion.background_text}
                      </Typography>
                    </>
                  )}

                  {/* 設問 */}
                  <Typography variant="subtitle2" sx={{ fontWeight: 'bold', color: 'primary.main', mb: 1 }}>
                    【設問】
                  </Typography>
                  <Typography variant="body1" sx={{ mb: 2 }}>
                    {selectedQuestion.question_text}
                  </Typography>

                  {/* 複数設問がある場合 */}
                  {selectedQuestion.has_sub_questions && selectedQuestion.sub_questions && (
                    <>
                      <Typography variant="subtitle2" sx={{ fontWeight: 'bold', color: 'primary.main', mb: 1 }}>
                        【詳細設問】
                      </Typography>
                      <Box sx={{ ml: 2, mb: 2 }}>
                        {selectedQuestion.sub_questions.map((subQ, index) => (
                          <Typography key={index} variant="body2" sx={{ mb: 1 }}>
                            {index + 1}. {subQ}
                          </Typography>
                        ))}
                      </Box>
                    </>
                  )}
                </CardContent>
              </Card>
            )}

            {/* 解答入力 */}
            <TextField
              fullWidth
              multiline
              rows={6}
              label="解答"
              value={answerText}
              onChange={(e) => setAnswerText(e.target.value)}
              disabled={!selectedQuestion}
              placeholder={selectedQuestion ? `${selectedQuestion.max_chars}字以内で解答を入力してください` : "問題を選択してください"}
              sx={{ mb: 2 }}
              helperText={
                selectedQuestion && answerText
                  ? `${answerText.length}/${selectedQuestion.max_chars}文字`
                  : ''
              }
              error={selectedQuestion ? answerText.length > selectedQuestion.max_chars : false}
            />

            {/* エラー表示 */}
            {error && (
              <Alert severity="error" sx={{ mb: 2 }}>
                {error}
              </Alert>
            )}

            {/* ボタン */}
            <Box display="flex" gap={2}>
              <Button
                variant="contained"
                startIcon={isSubmitting || isScoring ? <CircularProgress size={20} /> : <Send />}
                onClick={handleSubmitAnswer}
                disabled={
                  !selectedQuestion ||
                  !candidateId.trim() ||
                  !answerText.trim() ||
                  isSubmitting ||
                  isScoring ||
                  (selectedQuestion && answerText.length > selectedQuestion.max_chars)
                }
                size="large"
              >
                {isSubmitting ? '提出中...' : isScoring ? 'AI採点中...' : '提出・採点'}
              </Button>

              <Button
                variant="outlined"
                startIcon={<Clear />}
                onClick={handleClear}
                disabled={isSubmitting || isScoring}
              >
                クリア
              </Button>
            </Box>
          </Paper>
        </Grid>

        {/* 採点結果表示エリア */}
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              採点結果
            </Typography>

            {scoringResult ? (
              <Box>
                {/* 総合得点 */}
                <Card sx={{ mb: 2, bgcolor: 'primary.50' }}>
                  <CardContent>
                    <Typography variant="h4" align="center" color="primary">
                      {scoringResult.total_score.toFixed(1)}点
                    </Typography>
                    <Typography variant="body2" align="center" color="text.secondary">
                      / {scoringResult.max_score}点
                    </Typography>
                    <Box display="flex" justifyContent="center" mt={1}>
                      <Chip
                        label={`${scoringResult.percentage.toFixed(1)}%`}
                        color={getScoreColor(scoringResult.percentage)}
                        size="small"
                      />
                      <Chip
                        label={`評価: ${scoringResult.grade}`}
                        color={getGradeColor(scoringResult.grade)}
                        size="small"
                        sx={{ ml: 1 }}
                      />
                    </Box>
                  </CardContent>
                </Card>

                {/* 詳細評価 */}
                {scoringResult.aspect_scores && (
                  <Card sx={{ mb: 2 }}>
                    <CardContent>
                      <Typography variant="subtitle1" gutterBottom>
                        詳細評価
                      </Typography>
                      {Object.entries(scoringResult.aspect_scores).map(([aspect, score]) => (
                        <Box key={aspect} display="flex" justifyContent="space-between" mb={1}>
                          <Typography variant="body2">{aspect}:</Typography>
                          <Typography variant="body2" fontWeight="bold">
                            {score.toFixed(1)}/5.0
                          </Typography>
                        </Box>
                      ))}
                    </CardContent>
                  </Card>
                )}

                {/* AI信頼度 */}
                <Card sx={{ mb: 2 }}>
                  <CardContent>
                    <Typography variant="subtitle1" gutterBottom>
                      AI信頼度
                    </Typography>
                    <Typography variant="h6" color="primary">
                      {(scoringResult.confidence * 100).toFixed(1)}%
                    </Typography>
                  </CardContent>
                </Card>

                {/* フィードバック */}
                {scoringResult.detailed_feedback && (
                  <Card>
                    <CardContent>
                      <Typography variant="subtitle1" gutterBottom>
                        詳細フィードバック
                      </Typography>
                      <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                        {scoringResult.detailed_feedback}
                      </Typography>
                    </CardContent>
                  </Card>
                )}
              </Box>
            ) : (
              <Typography variant="body2" color="text.secondary">
                解答を提出すると、AI採点結果がここに表示されます。
              </Typography>
            )}
          </Paper>
        </Grid>
      </Grid>
    </Container>
  );
};

export default AnswerSubmission;