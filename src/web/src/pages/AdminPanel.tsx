import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Box,
  Tab,
  Tabs,
  Card,
  CardContent,
  Button,
  TextField,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  IconButton,
  Chip
} from '@mui/material';
import {
  Add,
  Edit,
  Delete,
  School,
  Quiz,
  Save,
  Cancel,
  CloudUpload,
  FileUpload
} from '@mui/icons-material';

interface Exam {
  id: number;
  title: string;
  description: string | null;
  created_at: string;
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
      id={`admin-tabpanel-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

export const AdminPanel: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  const [exams, setExams] = useState<Exam[]>([]);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [selectedExamId, setSelectedExamId] = useState<number | null>(null);

  // ダイアログ状態
  const [examDialogOpen, setExamDialogOpen] = useState(false);
  const [questionDialogOpen, setQuestionDialogOpen] = useState(false);
  const [editingExam, setEditingExam] = useState<Exam | null>(null);
  const [editingQuestion, setEditingQuestion] = useState<Question | null>(null);

  // CSV アップロード状態
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [csvExamName, setCsvExamName] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<{
    uploadId?: string;
    status?: string;
    message?: string;
    progress?: number;
  }>({});

  // フォーム状態
  const [examForm, setExamForm] = useState({ title: '', description: '' });
  const [questionForm, setQuestionForm] = useState({
    title: '',
    question_number: '',
    background_text: '',
    question_text: '',
    sub_questions: [''],
    model_answer: '',
    max_chars: 400,
    points: 25,
    grading_intention: '',
    grading_commentary: '',
    keywords: ['']
  });

  const [alert, setAlert] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  useEffect(() => {
    fetchExams();
  }, []);

  useEffect(() => {
    if (selectedExamId) {
      fetchQuestions(selectedExamId);
    }
  }, [selectedExamId]);

  const fetchExams = async () => {
    try {
      const response = await fetch('/api/admin/exams');
      if (response.ok) {
        const data = await response.json();
        setExams(data);
        if (data.length > 0 && !selectedExamId) {
          setSelectedExamId(data[0].id);
        }
      }
    } catch (error) {
      showAlert('error', '試験一覧の取得に失敗しました');
    }
  };

  const fetchQuestions = async (examId: number) => {
    try {
      const response = await fetch(`/api/admin/questions?exam_id=${examId}`);
      if (response.ok) {
        const data = await response.json();
        setQuestions(data);
      }
    } catch (error) {
      showAlert('error', '問題一覧の取得に失敗しました');
    }
  };

  const showAlert = (type: 'success' | 'error', message: string) => {
    setAlert({ type, message });
    setTimeout(() => setAlert(null), 3000);
  };

  const handleCreateExam = async () => {
    try {
      const response = await fetch('/api/admin/exams', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(examForm)
      });

      if (response.ok) {
        showAlert('success', '試験を作成しました');
        setExamDialogOpen(false);
        setExamForm({ title: '', description: '' });
        fetchExams();
      } else {
        showAlert('error', '試験の作成に失敗しました');
      }
    } catch (error) {
      showAlert('error', '試験の作成に失敗しました');
    }
  };

  const handleCreateQuestion = async () => {
    if (!selectedExamId) {
      showAlert('error', '試験を選択してください');
      return;
    }

    try {
      const response = await fetch('/api/admin/questions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...questionForm,
          exam_id: selectedExamId
        })
      });

      if (response.ok) {
        showAlert('success', '問題を作成しました');
        setQuestionDialogOpen(false);
        setQuestionForm({
          title: '',
          question_number: '',
          background_text: '',
          question_text: '',
          sub_questions: [''],
          model_answer: '',
          max_chars: 400,
          points: 25,
          grading_intention: '',
          grading_commentary: '',
          keywords: ['']
        });
        fetchQuestions(selectedExamId);
      } else {
        showAlert('error', '問題の作成に失敗しました');
      }
    } catch (error) {
      showAlert('error', '問題の作成に失敗しました');
    }
  };

  const handleUpdateQuestion = async () => {
    if (!editingQuestion) return;

    try {
      const response = await fetch(`/api/admin/questions/${editingQuestion.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(questionForm)
      });

      if (response.ok) {
        showAlert('success', '問題を更新しました');
        setQuestionDialogOpen(false);
        setEditingQuestion(null);
        if (selectedExamId) fetchQuestions(selectedExamId);
      } else {
        showAlert('error', '問題の更新に失敗しました');
      }
    } catch (error) {
      showAlert('error', '問題の更新に失敗しました');
    }
  };

  const handleDeleteQuestion = async (questionId: number) => {
    if (!window.confirm('この問題を削除してもよろしいですか？')) return;

    try {
      const response = await fetch(`/api/admin/questions/${questionId}`, {
        method: 'DELETE'
      });

      if (response.ok) {
        showAlert('success', '問題を削除しました');
        if (selectedExamId) fetchQuestions(selectedExamId);
      } else {
        showAlert('error', '問題の削除に失敗しました');
      }
    } catch (error) {
      showAlert('error', '問題の削除に失敗しました');
    }
  };

  const openQuestionDialog = (question?: Question) => {
    if (question) {
      setEditingQuestion(question);
      setQuestionForm({
        title: question.title,
        question_number: question.question_number,
        background_text: question.background_text,
        question_text: question.question_text,
        sub_questions: question.sub_questions || [''],
        model_answer: question.model_answer,
        max_chars: question.max_chars,
        points: question.points,
        grading_intention: question.grading_intention || '',
        grading_commentary: question.grading_commentary || '',
        keywords: question.keywords || ['']
      });
    } else {
      setEditingQuestion(null);
      setQuestionForm({
        title: '',
        question_number: '',
        background_text: '',
        question_text: '',
        sub_questions: [''],
        model_answer: '',
        max_chars: 400,
        points: 25,
        grading_intention: '',
        grading_commentary: '',
        keywords: ['']
      });
    }
    setQuestionDialogOpen(true);
  };

  // CSV アップロード処理
  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedFile(file);
    }
  };

  const handleCSVUpload = async () => {
    if (!selectedFile || !csvExamName.trim()) {
      showAlert('error', 'CSVファイルと試験名を入力してください');
      return;
    }

    setIsUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('exam_name', csvExamName);

      const response = await fetch('/api/admin/questions/csv/execute', {
        method: 'POST',
        body: formData
      });

      if (response.ok) {
        const result = await response.json();
        setUploadProgress({
          uploadId: result.upload_id,
          status: 'processing',
          message: result.message
        });
        showAlert('success', result.message);

        // アップロード状況を監視
        monitorUploadProgress(result.upload_id);

        // フォームをリセット
        setSelectedFile(null);
        setCsvExamName('');

        // 試験一覧を更新
        fetchExams();
      } else {
        const error = await response.json();
        showAlert('error', error.detail || 'アップロードに失敗しました');
      }
    } catch (error) {
      showAlert('error', 'アップロードに失敗しました');
    } finally {
      setIsUploading(false);
    }
  };

  const monitorUploadProgress = async (uploadId: string) => {
    try {
      const response = await fetch(`/api/admin/questions/csv/status/${uploadId}`);
      if (response.ok) {
        const status = await response.json();
        setUploadProgress(status);

        if (status.status === 'processing') {
          // 3秒後に再チェック
          setTimeout(() => monitorUploadProgress(uploadId), 3000);
        }
      }
    } catch (error) {
      console.error('Progress monitoring error:', error);
    }
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      {alert && (
        <Alert severity={alert.type} sx={{ mb: 2 }}>
          {alert.message}
        </Alert>
      )}

      <Typography variant="h4" component="h1" gutterBottom>
        ⚙️ 管理者パネル
      </Typography>

      <Paper sx={{ width: '100%' }}>
        <Tabs value={tabValue} onChange={(_, newValue) => setTabValue(newValue)}>
          <Tab icon={<School />} label="試験管理" />
          <Tab icon={<Quiz />} label="問題管理" />
          <Tab icon={<CloudUpload />} label="CSV一括登録" />
        </Tabs>

        {/* 試験管理タブ */}
        <TabPanel value={tabValue} index={0}>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
            <Typography variant="h5">試験一覧</Typography>
            <Button
              variant="contained"
              startIcon={<Add />}
              onClick={() => setExamDialogOpen(true)}
            >
              新しい試験を作成
            </Button>
          </Box>

          <TableContainer component={Paper} variant="outlined">
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>ID</TableCell>
                  <TableCell>試験名</TableCell>
                  <TableCell>説明</TableCell>
                  <TableCell>作成日</TableCell>
                  <TableCell>操作</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {exams.map((exam) => (
                  <TableRow
                    key={exam.id}
                    selected={selectedExamId === exam.id}
                    onClick={() => setSelectedExamId(exam.id)}
                    sx={{ cursor: 'pointer' }}
                  >
                    <TableCell>{exam.id}</TableCell>
                    <TableCell>{exam.title}</TableCell>
                    <TableCell>{exam.description || '-'}</TableCell>
                    <TableCell>{new Date(exam.created_at).toLocaleDateString()}</TableCell>
                    <TableCell>
                      <Chip
                        label={selectedExamId === exam.id ? "選択中" : "選択"}
                        color={selectedExamId === exam.id ? "primary" : "default"}
                        size="small"
                      />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </TabPanel>

        {/* 問題管理タブ */}
        <TabPanel value={tabValue} index={1}>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
            <Typography variant="h5">
              問題一覧 {selectedExamId && `(試験ID: ${selectedExamId})`}
            </Typography>
            <Button
              variant="contained"
              startIcon={<Add />}
              onClick={() => openQuestionDialog()}
              disabled={!selectedExamId}
            >
              新しい問題を作成
            </Button>
          </Box>

          {!selectedExamId && (
            <Alert severity="info" sx={{ mb: 2 }}>
              試験を選択してください
            </Alert>
          )}

          <TableContainer component={Paper} variant="outlined">
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>ID</TableCell>
                  <TableCell>問題番号</TableCell>
                  <TableCell>タイトル</TableCell>
                  <TableCell>設問文</TableCell>
                  <TableCell>配点</TableCell>
                  <TableCell>文字制限</TableCell>
                  <TableCell>操作</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {questions.map((question) => (
                  <TableRow key={question.id}>
                    <TableCell>{question.id}</TableCell>
                    <TableCell>{question.question_number}</TableCell>
                    <TableCell>{question.title}</TableCell>
                    <TableCell sx={{ maxWidth: 300 }}>
                      {question.question_text.length > 100
                        ? `${question.question_text.substring(0, 100)}...`
                        : question.question_text
                      }
                    </TableCell>
                    <TableCell>{question.points}点</TableCell>
                    <TableCell>{question.max_chars}文字</TableCell>
                    <TableCell>
                      <Box display="flex" gap={1}>
                        <IconButton
                          size="small"
                          onClick={() => openQuestionDialog(question)}
                        >
                          <Edit />
                        </IconButton>
                        <IconButton
                          size="small"
                          color="error"
                          onClick={() => handleDeleteQuestion(question.id)}
                        >
                          <Delete />
                        </IconButton>
                      </Box>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </TabPanel>

        {/* CSV一括登録タブ */}
        <TabPanel value={tabValue} index={2}>
          <Typography variant="h5" gutterBottom>
            📋 問題CSV一括登録
          </Typography>

          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                CSV形式の要件
              </Typography>
              <Typography variant="body2" color="text.secondary" paragraph>
                以下の形式でCSVファイルを準備してください：
              </Typography>
              <Box component="pre" sx={{ backgroundColor: 'grey.100', p: 2, borderRadius: 1, fontSize: 12 }}>
{`問題番号,タイトル,背景情報,設問文,模範解答,配点,文字制限,出題趣旨,採点講評,キーワード
問1,リスク管理,プロジェクト背景...,設問内容...,模範解答...,25,400,出題趣旨...,採点講評...,キーワード1,キーワード2`}
              </Box>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                • 必須項目：問題番号、タイトル、設問文、模範解答
                <br />
                • 任意項目：背景情報、配点（デフォルト25点）、文字制限（デフォルト400文字）、出題趣旨、採点講評、キーワード
              </Typography>
            </CardContent>
          </Card>

          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                ファイルアップロード
              </Typography>

              <Box sx={{ mb: 3 }}>
                <TextField
                  fullWidth
                  label="試験名"
                  value={csvExamName}
                  onChange={(e) => setCsvExamName(e.target.value)}
                  placeholder="例：2024年度 プロジェクトマネジメント試験"
                  sx={{ mb: 2 }}
                  required
                />

                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                  <Button
                    component="label"
                    variant="outlined"
                    startIcon={<FileUpload />}
                    disabled={isUploading}
                  >
                    CSVファイルを選択
                    <input
                      type="file"
                      accept=".csv"
                      hidden
                      onChange={handleFileChange}
                    />
                  </Button>
                  {selectedFile && (
                    <Typography variant="body2" color="text.secondary">
                      選択済み: {selectedFile.name}
                    </Typography>
                  )}
                </Box>

                <Button
                  variant="contained"
                  startIcon={<CloudUpload />}
                  onClick={handleCSVUpload}
                  disabled={!selectedFile || !csvExamName.trim() || isUploading}
                  sx={{ mb: 2 }}
                >
                  {isUploading ? 'アップロード中...' : 'アップロード実行'}
                </Button>
              </Box>

              {uploadProgress.uploadId && (
                <Card variant="outlined" sx={{ mt: 2 }}>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      処理状況
                    </Typography>
                    <Box sx={{ mb: 2 }}>
                      <Typography variant="body2">
                        アップロードID: {uploadProgress.uploadId}
                      </Typography>
                      <Typography variant="body2">
                        ステータス: {uploadProgress.status}
                      </Typography>
                      <Typography variant="body2">
                        メッセージ: {uploadProgress.message}
                      </Typography>
                      {uploadProgress.progress !== undefined && (
                        <Typography variant="body2">
                          進捗: {uploadProgress.progress}%
                        </Typography>
                      )}
                    </Box>
                    {uploadProgress.status === 'processing' && (
                      <Alert severity="info" sx={{ mt: 1 }}>
                        処理中です。しばらくお待ちください...
                      </Alert>
                    )}
                    {uploadProgress.status === 'completed' && (
                      <Alert severity="success" sx={{ mt: 1 }}>
                        アップロードが完了しました！
                      </Alert>
                    )}
                    {uploadProgress.status === 'error' && (
                      <Alert severity="error" sx={{ mt: 1 }}>
                        アップロード中にエラーが発生しました
                      </Alert>
                    )}
                  </CardContent>
                </Card>
              )}
            </CardContent>
          </Card>
        </TabPanel>
      </Paper>

      {/* 試験作成ダイアログ */}
      <Dialog open={examDialogOpen} onClose={() => setExamDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>新しい試験を作成</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="試験名"
            value={examForm.title}
            onChange={(e) => setExamForm({ ...examForm, title: e.target.value })}
            margin="normal"
            required
          />
          <TextField
            fullWidth
            label="説明"
            value={examForm.description}
            onChange={(e) => setExamForm({ ...examForm, description: e.target.value })}
            margin="normal"
            multiline
            rows={3}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setExamDialogOpen(false)} startIcon={<Cancel />}>
            キャンセル
          </Button>
          <Button onClick={handleCreateExam} variant="contained" startIcon={<Save />}>
            作成
          </Button>
        </DialogActions>
      </Dialog>

      {/* 問題作成・編集ダイアログ */}
      <Dialog open={questionDialogOpen} onClose={() => setQuestionDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          {editingQuestion ? '問題を編集' : '新しい問題を作成'}
        </DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="問題番号（例：問1、設問1）"
            value={questionForm.question_number}
            onChange={(e) => setQuestionForm({ ...questionForm, question_number: e.target.value })}
            margin="normal"
            required
          />
          <TextField
            fullWidth
            label="問題タイトル"
            value={questionForm.title}
            onChange={(e) => setQuestionForm({ ...questionForm, title: e.target.value })}
            margin="normal"
            required
          />
          <TextField
            fullWidth
            label="背景情報・プロジェクト概要"
            value={questionForm.background_text}
            onChange={(e) => setQuestionForm({ ...questionForm, background_text: e.target.value })}
            margin="normal"
            multiline
            rows={4}
            required
            helperText="プロジェクトの背景情報、組織・体制、技術的制約など"
          />
          <TextField
            fullWidth
            label="設問文"
            value={questionForm.question_text}
            onChange={(e) => setQuestionForm({ ...questionForm, question_text: e.target.value })}
            margin="normal"
            multiline
            rows={3}
            required
            helperText="実際の設問内容"
          />
          <TextField
            fullWidth
            label="模範解答"
            value={questionForm.model_answer}
            onChange={(e) => setQuestionForm({ ...questionForm, model_answer: e.target.value })}
            margin="normal"
            multiline
            rows={4}
            required
            helperText="AI採点の参考となる模範解答"
          />
          <TextField
            fullWidth
            label="出題趣旨"
            value={questionForm.grading_intention}
            onChange={(e) => setQuestionForm({ ...questionForm, grading_intention: e.target.value })}
            margin="normal"
            multiline
            rows={2}
            helperText="この問題で評価したいポイント（任意）"
          />
          <TextField
            fullWidth
            label="採点講評"
            value={questionForm.grading_commentary}
            onChange={(e) => setQuestionForm({ ...questionForm, grading_commentary: e.target.value })}
            margin="normal"
            multiline
            rows={2}
            helperText="採点時の注意点や補足情報（任意）"
          />
          <Box display="flex" gap={2} mt={2}>
            <TextField
              label="配点"
              type="number"
              value={questionForm.points}
              onChange={(e) => setQuestionForm({ ...questionForm, points: parseInt(e.target.value) || 25 })}
              sx={{ width: 120 }}
            />
            <TextField
              label="文字制限"
              type="number"
              value={questionForm.max_chars}
              onChange={(e) => setQuestionForm({ ...questionForm, max_chars: parseInt(e.target.value) || 400 })}
              sx={{ width: 120 }}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setQuestionDialogOpen(false)} startIcon={<Cancel />}>
            キャンセル
          </Button>
          <Button
            onClick={editingQuestion ? handleUpdateQuestion : handleCreateQuestion}
            variant="contained"
            startIcon={<Save />}
          >
            {editingQuestion ? '更新' : '作成'}
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default AdminPanel;