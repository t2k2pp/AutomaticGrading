import React, { useState, useRef } from 'react';
import {
  Box,
  Typography,
  Button,
  Card,
  CardContent,
  Stepper,
  Step,
  StepLabel,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Alert,
  AlertTitle,
  Divider,
  LinearProgress,
  Chip,
  Paper,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  CircularProgress
} from '@mui/material';
import {
  CloudUpload,
  FilePresent,
  PreviewSharp,
  PlayArrow,
  CheckCircle,
  Error,
  Warning,
  Info
} from '@mui/icons-material';

interface UploadPreview {
  total_rows: number;
  sample_data: Array<{[key: string]: string}>;
  column_mapping: {[key: string]: string};
  detected_issues: string[];
}

interface BatchUploadRequest {
  exam_name: string;
  question_text: string;
  question_title: string;
  max_score: number;
  char_limit: number;
}

interface UploadStatus {
  upload_id: string;
  status: 'uploading' | 'processing' | 'completed' | 'error';
  total_count: number;
  processed_count: number;
  success_count: number;
  error_count: number;
  progress_percentage: number;
  message: string;
  errors: string[];
}

export const BatchUpload: React.FC = () => {
  const [currentStep, setCurrentStep] = useState(0);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<UploadPreview | null>(null);
  const [uploadRequest, setUploadRequest] = useState<BatchUploadRequest>({
    exam_name: '2024年度社内PM試験',
    question_text: 'ITプロジェクトにおけるリスク管理について、あなたの経験を踏まえて論述してください。',
    question_title: 'リスク管理',
    max_score: 25,
    char_limit: 400
  });
  const [uploadStatus, setUploadStatus] = useState<UploadStatus | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const steps = [
    'CSVファイル選択',
    'データ確認',
    '試験設定',
    'アップロード実行'
  ];

  const handleFileSelect = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setSelectedFile(file);
    setIsLoading(true);

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch('/api/batch-upload/upload/preview', {
        method: 'POST',
        body: formData
      });

      if (response.ok) {
        const previewData: UploadPreview = await response.json();
        setPreview(previewData);
        setCurrentStep(1);
      } else {
        const error = await response.json();
        alert(`エラー: ${error.detail}`);
      }
    } catch (error) {
      alert('ファイル読み込み中にエラーが発生しました');
    } finally {
      setIsLoading(false);
    }
  };

  const handleUploadExecute = async () => {
    if (!selectedFile) return;

    setIsLoading(true);
    try {
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('upload_request', JSON.stringify(uploadRequest));

      const response = await fetch('/api/batch-upload/upload/execute', {
        method: 'POST',
        body: formData
      });

      if (response.ok) {
        const result = await response.json();
        setCurrentStep(3);
        // 処理状況の監視を開始
        monitorUploadProgress(result.upload_id);
      } else {
        const error = await response.json();
        alert(`アップロードエラー: ${error.detail}`);
      }
    } catch (error) {
      alert('アップロード中にエラーが発生しました');
    } finally {
      setIsLoading(false);
    }
  };

  const monitorUploadProgress = (uploadId: string) => {
    const checkProgress = async () => {
      try {
        const response = await fetch(`/api/batch-upload/upload/status/${uploadId}`);
        if (response.ok) {
          const status: UploadStatus = await response.json();
          setUploadStatus(status);

          if (status.status === 'processing') {
            setTimeout(checkProgress, 2000); // 2秒後に再確認
          }
        }
      } catch (error) {
        console.error('進捗確認エラー:', error);
      }
    };
    checkProgress();
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'success';
      case 'error': return 'error';
      case 'processing': return 'warning';
      default: return 'info';
    }
  };

  return (
    <Box sx={{ maxWidth: '1200px', mx: 'auto', p: 3 }}>
      <Typography variant="h4" gutterBottom sx={{ textAlign: 'center', mb: 4, fontWeight: 'bold' }}>
        📁 CSV一括アップロード
      </Typography>

      <Paper elevation={2} sx={{ p: 3, mb: 4 }}>
        <Typography variant="h6" sx={{ mb: 2, color: 'primary.main' }}>
          🔍 このページでできること
        </Typography>
        <List dense>
          <ListItem>
            <ListItemIcon><CheckCircle sx={{ color: 'success.main' }} /></ListItemIcon>
            <ListItemText primary="Moodleから出力したCSVファイルを一度に処理" />
          </ListItem>
          <ListItem>
            <ListItemIcon><CheckCircle sx={{ color: 'success.main' }} /></ListItemIcon>
            <ListItemText primary="最大100人分の回答を自動AI採点" />
          </ListItem>
          <ListItem>
            <ListItemIcon><CheckCircle sx={{ color: 'success.main' }} /></ListItemIcon>
            <ListItemText primary="2次採点者向けの詳細な採点理由を自動生成" />
          </ListItem>
        </List>
      </Paper>

      <Stepper activeStep={currentStep} sx={{ mb: 4 }}>
        {steps.map((label) => (
          <Step key={label}>
            <StepLabel sx={{
              '& .MuiStepLabel-label': { fontSize: '1.1rem', fontWeight: 'bold' }
            }}>
              {label}
            </StepLabel>
          </Step>
        ))}
      </Stepper>

      {/* ステップ1: ファイル選択 */}
      {currentStep === 0 && (
        <Card elevation={3} sx={{ mb: 4 }}>
          <CardContent sx={{ textAlign: 'center', py: 6 }}>
            <CloudUpload sx={{ fontSize: 80, color: 'primary.main', mb: 2 }} />
            <Typography variant="h5" gutterBottom sx={{ fontWeight: 'bold' }}>
              CSVファイルを選択してください
            </Typography>
            <Typography variant="body1" sx={{ mb: 4, color: 'text.secondary' }}>
              MoodleからエクスポートしたCSVファイルをドラッグ&ドロップまたはクリックして選択
            </Typography>

            <Button
              variant="contained"
              size="large"
              onClick={handleFileSelect}
              disabled={isLoading}
              sx={{
                py: 2,
                px: 6,
                fontSize: '1.2rem',
                borderRadius: 3,
                minHeight: 60
              }}
            >
              {isLoading ? (
                <>
                  <CircularProgress size={24} sx={{ mr: 2 }} />
                  ファイル読み込み中...
                </>
              ) : (
                <>
                  <FilePresent sx={{ mr: 2 }} />
                  ファイルを選択
                </>
              )}
            </Button>

            <input
              type="file"
              accept=".csv"
              onChange={handleFileChange}
              ref={fileInputRef}
              style={{ display: 'none' }}
            />

            {selectedFile && (
              <Alert severity="success" sx={{ mt: 3, maxWidth: 400, mx: 'auto' }}>
                <AlertTitle>選択されたファイル</AlertTitle>
                📄 {selectedFile.name}
              </Alert>
            )}
          </CardContent>
        </Card>
      )}

      {/* ステップ2: データ確認 */}
      {currentStep === 1 && preview && (
        <Card elevation={3} sx={{ mb: 4 }}>
          <CardContent>
            <Typography variant="h5" gutterBottom sx={{ fontWeight: 'bold', color: 'primary.main' }}>
              📊 データ確認
            </Typography>

            <Box sx={{ display: 'flex', gap: 2, mb: 3 }}>
              <Chip
                label={`${preview.total_rows} 人分のデータ`}
                color="primary"
                size="large"
                sx={{ fontSize: '1rem', py: 2 }}
              />
              {preview.detected_issues.length === 0 && (
                <Chip
                  label="✅ 問題なし"
                  color="success"
                  size="large"
                  sx={{ fontSize: '1rem', py: 2 }}
                />
              )}
            </Box>

            {preview.detected_issues.length > 0 && (
              <Alert severity="warning" sx={{ mb: 3 }}>
                <AlertTitle>⚠️ 確認が必要な項目</AlertTitle>
                <List dense>
                  {preview.detected_issues.map((issue, index) => (
                    <ListItem key={index}>
                      <ListItemIcon><Warning color="warning" /></ListItemIcon>
                      <ListItemText primary={issue} />
                    </ListItem>
                  ))}
                </List>
              </Alert>
            )}

            <Typography variant="h6" sx={{ mb: 2 }}>
              📋 サンプルデータ（最初の5件）
            </Typography>
            <Box sx={{ overflowX: 'auto' }}>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    {Object.keys(preview.sample_data[0] || {}).map((header) => (
                      <TableCell key={header} sx={{ fontWeight: 'bold', bgcolor: 'grey.100' }}>
                        {header}
                      </TableCell>
                    ))}
                  </TableRow>
                </TableHead>
                <TableBody>
                  {preview.sample_data.map((row, index) => (
                    <TableRow key={index}>
                      {Object.values(row).map((value, cellIndex) => (
                        <TableCell key={cellIndex} sx={{ maxWidth: 200 }}>
                          {value.length > 50 ? `${value.substring(0, 50)}...` : value}
                        </TableCell>
                      ))}
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </Box>

            <Box sx={{ mt: 4, display: 'flex', gap: 2, justifyContent: 'center' }}>
              <Button
                variant="outlined"
                size="large"
                onClick={() => setCurrentStep(0)}
                sx={{ px: 4, py: 1.5 }}
              >
                戻る
              </Button>
              <Button
                variant="contained"
                size="large"
                onClick={() => setCurrentStep(2)}
                sx={{ px: 4, py: 1.5 }}
              >
                次へ進む
              </Button>
            </Box>
          </CardContent>
        </Card>
      )}

      {/* ステップ3: 試験設定 */}
      {currentStep === 2 && (
        <Card elevation={3} sx={{ mb: 4 }}>
          <CardContent>
            <Typography variant="h5" gutterBottom sx={{ fontWeight: 'bold', color: 'primary.main' }}>
              ⚙️ 試験設定
            </Typography>

            <Box sx={{ display: 'grid', gap: 3, gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' } }}>
              <Box>
                <Typography variant="h6" sx={{ mb: 1 }}>📝 試験名</Typography>
                <input
                  type="text"
                  value={uploadRequest.exam_name}
                  onChange={(e) => setUploadRequest({...uploadRequest, exam_name: e.target.value})}
                  style={{
                    width: '100%',
                    padding: '12px',
                    fontSize: '16px',
                    border: '2px solid #ddd',
                    borderRadius: '8px'
                  }}
                />
              </Box>

              <Box>
                <Typography variant="h6" sx={{ mb: 1 }}>🎯 問題タイトル</Typography>
                <input
                  type="text"
                  value={uploadRequest.question_title}
                  onChange={(e) => setUploadRequest({...uploadRequest, question_title: e.target.value})}
                  style={{
                    width: '100%',
                    padding: '12px',
                    fontSize: '16px',
                    border: '2px solid #ddd',
                    borderRadius: '8px'
                  }}
                />
              </Box>
            </Box>

            <Box sx={{ mt: 3 }}>
              <Typography variant="h6" sx={{ mb: 1 }}>❓ 問題文</Typography>
              <textarea
                value={uploadRequest.question_text}
                onChange={(e) => setUploadRequest({...uploadRequest, question_text: e.target.value})}
                rows={4}
                style={{
                  width: '100%',
                  padding: '12px',
                  fontSize: '16px',
                  border: '2px solid #ddd',
                  borderRadius: '8px',
                  resize: 'vertical'
                }}
              />
            </Box>

            <Box sx={{ display: 'grid', gap: 3, gridTemplateColumns: '1fr 1fr', mt: 3 }}>
              <Box>
                <Typography variant="h6" sx={{ mb: 1 }}>💯 満点</Typography>
                <input
                  type="number"
                  value={uploadRequest.max_score}
                  onChange={(e) => setUploadRequest({...uploadRequest, max_score: parseInt(e.target.value)})}
                  style={{
                    width: '100%',
                    padding: '12px',
                    fontSize: '16px',
                    border: '2px solid #ddd',
                    borderRadius: '8px'
                  }}
                />
              </Box>

              <Box>
                <Typography variant="h6" sx={{ mb: 1 }}>📏 文字数制限</Typography>
                <input
                  type="number"
                  value={uploadRequest.char_limit}
                  onChange={(e) => setUploadRequest({...uploadRequest, char_limit: parseInt(e.target.value)})}
                  style={{
                    width: '100%',
                    padding: '12px',
                    fontSize: '16px',
                    border: '2px solid #ddd',
                    borderRadius: '8px'
                  }}
                />
              </Box>
            </Box>

            <Box sx={{ mt: 4, display: 'flex', gap: 2, justifyContent: 'center' }}>
              <Button
                variant="outlined"
                size="large"
                onClick={() => setCurrentStep(1)}
                sx={{ px: 4, py: 1.5 }}
              >
                戻る
              </Button>
              <Button
                variant="contained"
                size="large"
                onClick={handleUploadExecute}
                disabled={isLoading}
                sx={{ px: 4, py: 1.5 }}
              >
                {isLoading ? (
                  <>
                    <CircularProgress size={24} sx={{ mr: 2 }} />
                    処理開始中...
                  </>
                ) : (
                  <>
                    <PlayArrow sx={{ mr: 1 }} />
                    AI採点を開始
                  </>
                )}
              </Button>
            </Box>
          </CardContent>
        </Card>
      )}

      {/* ステップ4: 処理進捗 */}
      {currentStep === 3 && uploadStatus && (
        <Card elevation={3} sx={{ mb: 4 }}>
          <CardContent>
            <Typography variant="h5" gutterBottom sx={{ fontWeight: 'bold', color: 'primary.main' }}>
              ⏳ 処理進捗
            </Typography>

            <Box sx={{ mb: 3 }}>
              <Chip
                label={uploadStatus.status === 'processing' ? '🔄 処理中' :
                       uploadStatus.status === 'completed' ? '✅ 完了' : '❌ エラー'}
                color={getStatusColor(uploadStatus.status) as 'default'}
                size="large"
                sx={{ fontSize: '1.1rem', py: 2, mb: 2 }}
              />
              <Typography variant="body1" sx={{ mb: 2 }}>
                {uploadStatus.message}
              </Typography>

              <LinearProgress
                variant="determinate"
                value={uploadStatus.progress_percentage}
                sx={{ height: 12, borderRadius: 6, mb: 2 }}
              />
              <Typography variant="body2" color="text.secondary">
                {uploadStatus.processed_count} / {uploadStatus.total_count} 件処理済み
                （成功: {uploadStatus.success_count}件、エラー: {uploadStatus.error_count}件）
              </Typography>
            </Box>

            {uploadStatus.errors.length > 0 && (
              <Alert severity="error" sx={{ mt: 3 }}>
                <AlertTitle>⚠️ エラー詳細</AlertTitle>
                <List dense>
                  {uploadStatus.errors.map((error, index) => (
                    <ListItem key={index}>
                      <ListItemIcon><Error color="error" /></ListItemIcon>
                      <ListItemText primary={error} />
                    </ListItem>
                  ))}
                </List>
              </Alert>
            )}

            {uploadStatus.status === 'completed' && (
              <Box sx={{ mt: 4, textAlign: 'center' }}>
                <Button
                  variant="contained"
                  size="large"
                  sx={{ px: 6, py: 2 }}
                  href="/scoring-results"
                >
                  📊 採点結果を確認
                </Button>
              </Box>
            )}
          </CardContent>
        </Card>
      )}
    </Box>
  );
};

export default BatchUpload;