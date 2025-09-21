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
  Divider,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Paper,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Tab,
  Tabs,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Slider,
  FormHelperText
} from '@mui/material';
import {
  ArrowBack,
  Edit,
  Save,
  Cancel,
  CheckCircle,
  Warning,
  Error,
  ThumbUp,
  ThumbDown,
  Lightbulb,
  Assessment,
  School,
  Psychology
} from '@mui/icons-material';

interface AspectDetail {
  criteria: string;
  score: number;
  reasoning: string;
  evidence: string[];
}

interface DetailedAnalysis {
  strengths: string[];
  weaknesses: string[];
  missing_elements: string[];
  specific_issues: string[];
}

interface AIFeedback {
  aspect_scores: AspectDetail[];
  detailed_analysis: DetailedAnalysis;
  improvement_suggestions: string[];
  confidence_reasoning: string;
  rubric_alignment: string;
}

interface Answer {
  id: number;
  student_id: string;
  student_name: string;
  answer_text: string;
  submitted_at: string;
}

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
  answer: Answer;
  question: Question;
  status: string;
  total_score: number;
  max_score: number;
  percentage: number;
  confidence: number;
  is_reviewed: boolean;
  final_score: number | null;
  reviewer_notes: string | null;
  grade: string;
  ai_feedback: AIFeedback;
  scored_at: string;
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`scoring-tabpanel-${index}`}
      aria-labelledby={`scoring-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

export const ScoringReview: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [result, setResult] = useState<ScoringResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tabValue, setTabValue] = useState(0);
  const [isEditing, setIsEditing] = useState(false);
  const [editedScore, setEditedScore] = useState<number>(0);
  const [reviewerNotes, setReviewerNotes] = useState<string>('');
  const [confirmDialog, setConfirmDialog] = useState(false);

  useEffect(() => {
    const fetchResult = async () => {
      if (!id) return;

      try {
        // 実際のAPIでは詳細な採点結果を取得
        // ここではサンプルデータを使用
        const sampleResult: ScoringResult = {
          id: parseInt(id),
          answer: {
            id: 1,
            student_id: "PM2024001",
            student_name: "田中太郎",
            answer_text: "プロジェクトマネジメントにおけるリスク管理は、プロジェクトの成功を左右する重要な要素です。リスクの特定、分析、対応策の策定、監視という一連のプロセスを通じて、不確実性による悪影響を最小限に抑えることができます。私の経験では、定期的なリスクレビュー会議の実施と、全チームメンバーによるリスク情報の共有が特に効果的でした。",
            submitted_at: "2024-09-21T10:00:00Z"
          },
          question: {
            id: 1,
            exam_id: 1,
            title: "リスク管理",
            question_number: "問2",
            background_text: "あなたは、IT企業のプロジェクトマネージャとして、様々なプロジェクトを経験してきました。",
            question_text: "ITプロジェクトにおけるリスク管理について、あなたの経験を踏まえて論述してください。",
            sub_questions: null,
            model_answer: "リスク管理は特定、分析、対応、監視の各段階からなる継続的なプロセスです。",
            max_chars: 400,
            points: 25,
            grading_intention: "リスク管理に関する知識と実務経験の活用能力を評価する",
            grading_commentary: "具体的な経験に基づく実践的な提案を評価する",
            keywords: ["リスク特定", "リスク分析", "対応策", "監視"],
            has_sub_questions: false,
            display_name: "問2: リスク管理"
          },
          status: "completed",
          total_score: 18.5,
          max_score: 25,
          percentage: 74.0,
          confidence: 0.85,
          is_reviewed: false,
          final_score: null,
          reviewer_notes: null,
          grade: "B",
          ai_feedback: {
            aspect_scores: [
              {
                criteria: "リスク管理プロセスの理解",
                score: 8.0,
                reasoning: "リスクの特定、分析、対応策、監視という基本的なプロセスが適切に記述されています",
                evidence: ["特定、分析、対応策の策定、監視", "一連のプロセス"]
              },
              {
                criteria: "実務経験の活用",
                score: 6.5,
                reasoning: "定期的なレビュー会議と情報共有について具体的な経験が述べられています",
                evidence: ["定期的なリスクレビュー会議", "チームメンバーによるリスク情報の共有"]
              },
              {
                criteria: "論理的構成",
                score: 4.0,
                reasoning: "基本的な構成はできていますが、より具体的な事例や効果測定が不足しています",
                evidence: ["論理的な流れ", "経験に基づく記述"]
              }
            ],
            detailed_analysis: {
              strengths: [
                "リスク管理の基本プロセス（特定→分析→対応→監視）を正確に理解している",
                "定期的なレビュー会議という具体的な手法を提示している",
                "チーム全体でのリスク情報共有の重要性を認識している"
              ],
              weaknesses: [
                "具体的なプロジェクト事例の詳細が不足している",
                "リスクの定量的な評価方法について言及がない",
                "対応策の優先順位付けについて記述が不十分"
              ],
              missing_elements: [
                "リスクレジスタやリスクマトリックスなどのツール活用",
                "ステークホルダーとのリスクコミュニケーション",
                "リスク対応の効果測定方法"
              ],
              specific_issues: [
                "文字数に余裕があるため、より具体的な事例を追加できる",
                "「効果的でした」という表現の根拠が不明確"
              ]
            },
            improvement_suggestions: [
              "具体的なプロジェクト規模や業界を明記し、リアリティを向上させる",
              "リスク管理ツール（リスクレジスタ、確率影響マトリックス等）の活用例を追加",
              "リスク対応の効果を定量的に示す（コスト削減額、遅延回避等）",
              "ステークホルダーとのコミュニケーション方法について具体的に記述"
            ],
            confidence_reasoning: "基本的なリスク管理概念は正確に理解されており、実務経験も一定程度記述されているが、具体性と深さの面で改善余地がある。PM試験の評価基準に照らすと中程度の評価が適切。",
            rubric_alignment: "IPA PM試験の採点基準（知識・理解40%、実務適用30%、論理性30%）に基づき、知識理解は良好だが実務適用と論理性に改善余地あり。"
          },
          scored_at: "2024-09-21T10:05:00Z"
        };

        setResult(sampleResult);
        setEditedScore(sampleResult.total_score);
        setReviewerNotes(sampleResult.reviewer_notes || '');
      } catch (err) {
        setError('採点結果の取得に失敗しました');
      } finally {
        setLoading(false);
      }
    };

    fetchResult();
  }, [id]);

  const handleSaveReview = async () => {
    if (!result) return;

    try {
      // 実際のAPIでレビュー結果を保存
      console.log('保存中:', {
        id: result.id,
        final_score: editedScore,
        reviewer_notes: reviewerNotes,
        is_reviewed: true
      });

      setResult({
        ...result,
        final_score: editedScore,
        reviewer_notes: reviewerNotes,
        is_reviewed: true
      });

      setIsEditing(false);
      setConfirmDialog(false);
    } catch (err) {
      setError('レビュー結果の保存に失敗しました');
    }
  };

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
      {/* ヘッダー */}
      <Box display="flex" alignItems="center" justifyContent="space-between" mb={3}>
        <Box display="flex" alignItems="center">
          <Button
            startIcon={<ArrowBack />}
            onClick={() => navigate('/scoring')}
            sx={{ mr: 2 }}
          >
            戻る
          </Button>
          <Box>
            <Typography variant="h4" component="h1">
              2次採点レビュー
            </Typography>
            <Typography variant="subtitle1" color="text.secondary">
              受験者: {result.answer.student_name} ({result.answer.student_id})
            </Typography>
          </Box>
        </Box>

        <Box display="flex" gap={1}>
          {result.is_reviewed && (
            <Chip
              icon={<CheckCircle />}
              label="レビュー済み"
              color="success"
              variant="outlined"
            />
          )}
          {!isEditing ? (
            <Button
              variant="contained"
              startIcon={<Edit />}
              onClick={() => setIsEditing(true)}
            >
              スコア修正
            </Button>
          ) : (
            <>
              <Button
                variant="outlined"
                startIcon={<Cancel />}
                onClick={() => {
                  setIsEditing(false);
                  setEditedScore(result.total_score);
                  setReviewerNotes(result.reviewer_notes || '');
                }}
              >
                キャンセル
              </Button>
              <Button
                variant="contained"
                startIcon={<Save />}
                onClick={() => setConfirmDialog(true)}
              >
                保存
              </Button>
            </>
          )}
        </Box>
      </Box>

      <Grid container spacing={3}>
        {/* 左側: 解答内容と基本情報 */}
        <Grid item xs={12} md={4}>
          <Card sx={{ mb: 2 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom color="primary">
                📝 {result.question.question_number}: {result.question.title}
              </Typography>

              {/* 背景情報 */}
              {result.question.background_text && (
                <>
                  <Typography variant="subtitle2" sx={{ fontWeight: 'bold', color: 'primary.main', mb: 1 }}>
                    【背景情報・プロジェクト概要】
                  </Typography>
                  <Typography variant="body2" sx={{ mb: 2, whiteSpace: 'pre-line', bgcolor: 'background.paper', p: 2, borderRadius: 1 }}>
                    {result.question.background_text}
                  </Typography>
                </>
              )}

              {/* 設問 */}
              <Typography variant="subtitle2" sx={{ fontWeight: 'bold', color: 'primary.main', mb: 1 }}>
                【設問】
              </Typography>
              <Typography variant="body2" sx={{ mb: 2 }}>
                {result.question.question_text}
              </Typography>

              {/* 複数設問がある場合 */}
              {result.question.has_sub_questions && result.question.sub_questions && (
                <>
                  <Typography variant="subtitle2" sx={{ fontWeight: 'bold', color: 'primary.main', mb: 1 }}>
                    【詳細設問】
                  </Typography>
                  <Box sx={{ ml: 2, mb: 2 }}>
                    {result.question.sub_questions.map((subQ, index) => (
                      <Typography key={index} variant="body2" sx={{ mb: 1 }}>
                        {index + 1}. {subQ}
                      </Typography>
                    ))}
                  </Box>
                </>
              )}

              <Divider sx={{ my: 2 }} />
              <Typography variant="body2" color="text.secondary">
                配点: {result.question.points}点 | 制限: {result.question.max_chars}文字
              </Typography>
            </CardContent>
          </Card>

          <Card sx={{ mb: 2 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom color="primary">
                ✍️ 受験者回答
              </Typography>
              <Paper variant="outlined" sx={{ p: 2, bgcolor: 'grey.50' }}>
                <Typography variant="body2" sx={{ lineHeight: 1.6 }}>
                  {result.answer.answer_text}
                </Typography>
              </Paper>
              <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                文字数: {result.answer.answer_text.length}文字 / 提出日時: {new Date(result.answer.submitted_at).toLocaleString()}
              </Typography>
            </CardContent>
          </Card>

          {/* スコア修正エリア */}
          {isEditing && (
            <Card sx={{ mb: 2, border: '2px solid', borderColor: 'warning.main' }}>
              <CardContent>
                <Typography variant="h6" gutterBottom color="warning.main">
                  ⚠️ スコア修正
                </Typography>
                <Box sx={{ mb: 3 }}>
                  <Typography variant="body2" sx={{ mb: 1 }}>
                    最終スコア: {editedScore.toFixed(1)} / {result.max_score}
                  </Typography>
                  <Slider
                    value={editedScore}
                    onChange={(_, value) => setEditedScore(value as number)}
                    min={0}
                    max={result.max_score}
                    step={0.5}
                    marks
                    valueLabelDisplay="auto"
                  />
                </Box>
                <TextField
                  fullWidth
                  multiline
                  rows={4}
                  label="2次採点者コメント"
                  value={reviewerNotes}
                  onChange={(e) => setReviewerNotes(e.target.value)}
                  placeholder="AI採点結果に対する修正理由や追加コメントを入力..."
                  variant="outlined"
                />
              </CardContent>
            </Card>
          )}
        </Grid>

        {/* 右側: AI採点詳細 */}
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              {/* スコア概要 */}
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
                <Box>
                  <Typography variant="h3" component="div" color="primary">
                    {result.is_reviewed && result.final_score !== null
                      ? result.final_score.toFixed(1)
                      : result.total_score.toFixed(1)
                    }
                    <Typography variant="h6" component="span" color="text.secondary">
                      / {result.max_score}点
                    </Typography>
                  </Typography>
                  <Chip
                    label={`${result.percentage.toFixed(1)}% (${result.grade})`}
                    color="primary"
                    sx={{ mt: 1 }}
                  />
                </Box>
                <Box textAlign="center">
                  <Typography variant="body2" color="text.secondary">
                    AI信頼度
                  </Typography>
                  <Typography variant="h4" color={result.confidence >= 0.8 ? 'success.main' : 'warning.main'}>
                    {(result.confidence * 100).toFixed(0)}%
                  </Typography>
                </Box>
              </Box>

              <Divider sx={{ mb: 2 }} />

              {/* タブナビゲーション */}
              <Tabs value={tabValue} onChange={(_, newValue) => setTabValue(newValue)}>
                <Tab icon={<Assessment />} label="詳細採点" />
                <Tab icon={<Psychology />} label="AI分析" />
                <Tab icon={<Lightbulb />} label="改善提案" />
                <Tab icon={<School />} label="採点根拠" />
              </Tabs>

              {/* 詳細採点タブ */}
              <TabPanel value={tabValue} index={0}>
                <Grid container spacing={2}>
                  {result.ai_feedback.aspect_scores.map((aspect, index) => (
                    <Grid item xs={12} key={index}>
                      <Paper variant="outlined" sx={{ p: 2 }}>
                        <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                          <Typography variant="h6">{aspect.criteria}</Typography>
                          <Chip
                            label={`${aspect.score.toFixed(1)}点`}
                            color={aspect.score >= 7 ? 'success' : aspect.score >= 5 ? 'warning' : 'error'}
                          />
                        </Box>
                        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                          {aspect.reasoning}
                        </Typography>
                        <Box>
                          <Typography variant="body2" sx={{ fontWeight: 'bold', mb: 1 }}>
                            根拠となる記述:
                          </Typography>
                          {aspect.evidence.map((evidence, idx) => (
                            <Chip
                              key={idx}
                              label={evidence}
                              variant="outlined"
                              size="small"
                              sx={{ mr: 1, mb: 1 }}
                            />
                          ))}
                        </Box>
                      </Paper>
                    </Grid>
                  ))}
                </Grid>
              </TabPanel>

              {/* AI分析タブ */}
              <TabPanel value={tabValue} index={1}>
                <Grid container spacing={3}>
                  <Grid item xs={12} md={6}>
                    <Box>
                      <Typography variant="h6" color="success.main" sx={{ mb: 2 }}>
                        <ThumbUp sx={{ mr: 1 }} />
                        優れている点
                      </Typography>
                      <List dense>
                        {result.ai_feedback.detailed_analysis.strengths.map((strength, index) => (
                          <ListItem key={index}>
                            <ListItemIcon>
                              <CheckCircle color="success" fontSize="small" />
                            </ListItemIcon>
                            <ListItemText primary={strength} />
                          </ListItem>
                        ))}
                      </List>
                    </Box>
                  </Grid>

                  <Grid item xs={12} md={6}>
                    <Box>
                      <Typography variant="h6" color="warning.main" sx={{ mb: 2 }}>
                        <ThumbDown sx={{ mr: 1 }} />
                        改善が必要な点
                      </Typography>
                      <List dense>
                        {result.ai_feedback.detailed_analysis.weaknesses.map((weakness, index) => (
                          <ListItem key={index}>
                            <ListItemIcon>
                              <Warning color="warning" fontSize="small" />
                            </ListItemIcon>
                            <ListItemText primary={weakness} />
                          </ListItem>
                        ))}
                      </List>
                    </Box>
                  </Grid>

                  <Grid item xs={12}>
                    <Typography variant="h6" color="error.main" sx={{ mb: 2 }}>
                      <Error sx={{ mr: 1 }} />
                      不足している要素
                    </Typography>
                    <List dense>
                      {result.ai_feedback.detailed_analysis.missing_elements.map((element, index) => (
                        <ListItem key={index}>
                          <ListItemIcon>
                            <Error color="error" fontSize="small" />
                          </ListItemIcon>
                          <ListItemText primary={element} />
                        </ListItem>
                      ))}
                    </List>
                  </Grid>
                </Grid>
              </TabPanel>

              {/* 改善提案タブ */}
              <TabPanel value={tabValue} index={2}>
                <Typography variant="h6" sx={{ mb: 2 }}>
                  📈 受験者向け改善アドバイス
                </Typography>
                <List>
                  {result.ai_feedback.improvement_suggestions.map((suggestion, index) => (
                    <ListItem key={index}>
                      <ListItemIcon>
                        <Lightbulb color="info" />
                      </ListItemIcon>
                      <ListItemText
                        primary={suggestion}
                        sx={{ '& .MuiListItemText-primary': { lineHeight: 1.6 } }}
                      />
                    </ListItem>
                  ))}
                </List>
              </TabPanel>

              {/* 採点根拠タブ */}
              <TabPanel value={tabValue} index={3}>
                <Typography variant="h6" sx={{ mb: 2 }}>
                  🎯 AI採点の信頼性分析
                </Typography>
                <Paper variant="outlined" sx={{ p: 2, mb: 3, bgcolor: 'info.50' }}>
                  <Typography variant="body2" sx={{ lineHeight: 1.6 }}>
                    {result.ai_feedback.confidence_reasoning}
                  </Typography>
                </Paper>

                <Typography variant="h6" sx={{ mb: 2 }}>
                  📊 IPA採点基準との整合性
                </Typography>
                <Paper variant="outlined" sx={{ p: 2, bgcolor: 'success.50' }}>
                  <Typography variant="body2" sx={{ lineHeight: 1.6 }}>
                    {result.ai_feedback.rubric_alignment}
                  </Typography>
                </Paper>
              </TabPanel>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* 確認ダイアログ */}
      <Dialog open={confirmDialog} onClose={() => setConfirmDialog(false)}>
        <DialogTitle>レビュー結果を保存しますか？</DialogTitle>
        <DialogContent>
          <Typography variant="body1" sx={{ mb: 2 }}>
            以下の内容で最終採点結果を保存します：
          </Typography>
          <Typography variant="body2">
            • AI採点: {result.total_score.toFixed(1)}点 → 最終採点: {editedScore.toFixed(1)}点
          </Typography>
          <Typography variant="body2">
            • 修正理由: {reviewerNotes || '(なし)'}
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setConfirmDialog(false)}>キャンセル</Button>
          <Button onClick={handleSaveReview} variant="contained">保存</Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default ScoringReview;