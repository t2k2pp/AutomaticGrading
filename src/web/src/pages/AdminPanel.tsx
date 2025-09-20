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
  Cancel
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
  text: string;
  max_score: number;
  char_limit: number;
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

  // フォーム状態
  const [examForm, setExamForm] = useState({ title: '', description: '' });
  const [questionForm, setQuestionForm] = useState({
    title: '',
    text: '',
    max_score: 25,
    char_limit: 400
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
        setQuestionForm({ title: '', text: '', max_score: 25, char_limit: 400 });
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
    if (!confirm('この問題を削除してもよろしいですか？')) return;

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
        text: question.text,
        max_score: question.max_score,
        char_limit: question.char_limit
      });
    } else {
      setEditingQuestion(null);
      setQuestionForm({ title: '', text: '', max_score: 25, char_limit: 400 });
    }
    setQuestionDialogOpen(true);
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
                  <TableCell>タイトル</TableCell>
                  <TableCell>問題文</TableCell>
                  <TableCell>満点</TableCell>
                  <TableCell>文字制限</TableCell>
                  <TableCell>操作</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {questions.map((question) => (
                  <TableRow key={question.id}>
                    <TableCell>{question.id}</TableCell>
                    <TableCell>{question.title}</TableCell>
                    <TableCell sx={{ maxWidth: 300 }}>
                      {question.text.length > 100
                        ? `${question.text.substring(0, 100)}...`
                        : question.text
                      }
                    </TableCell>
                    <TableCell>{question.max_score}点</TableCell>
                    <TableCell>{question.char_limit}文字</TableCell>
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
            label="問題タイトル"
            value={questionForm.title}
            onChange={(e) => setQuestionForm({ ...questionForm, title: e.target.value })}
            margin="normal"
            required
          />
          <TextField
            fullWidth
            label="問題文"
            value={questionForm.text}
            onChange={(e) => setQuestionForm({ ...questionForm, text: e.target.value })}
            margin="normal"
            multiline
            rows={6}
            required
          />
          <Box display="flex" gap={2} mt={2}>
            <TextField
              label="満点"
              type="number"
              value={questionForm.max_score}
              onChange={(e) => setQuestionForm({ ...questionForm, max_score: parseInt(e.target.value) || 25 })}
              sx={{ width: 120 }}
            />
            <TextField
              label="文字制限"
              type="number"
              value={questionForm.char_limit}
              onChange={(e) => setQuestionForm({ ...questionForm, char_limit: parseInt(e.target.value) || 400 })}
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