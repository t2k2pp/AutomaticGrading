import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000,
});

// レスポンスインターセプター（エラーハンドリング）
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);

export const apiService = {
  // ヘルスチェック
  async getHealthStatus() {
    const response = await apiClient.get('/health');
    return response.data;
  },

  // 採点結果一覧取得
  async getScoringResults(examId: number, candidateId?: string) {
    const params: any = {};
    if (candidateId) {
      params.candidate_id = candidateId;
    }

    const response = await apiClient.get(`/api/scoring/results/${examId}`, { params });
    return response.data;
  },

  // 採点結果詳細取得
  async getScoringResult(resultId: number) {
    const response = await apiClient.get(`/api/scoring/result/${resultId}`);
    return response.data;
  },

  // 解答提出
  async submitAnswer(answerData: {
    exam_id: number;
    question_id: number;
    candidate_id: string;
    answer_text: string;
  }) {
    const response = await apiClient.post('/api/scoring/submit', answerData);
    return response.data;
  },

  // AI採点実行
  async evaluateAnswer(evaluationData: { answer_id: number }) {
    const response = await apiClient.post('/api/scoring/evaluate', evaluationData);
    return response.data;
  },

  // システム情報取得
  async getSystemInfo() {
    const response = await apiClient.get('/');
    return response.data;
  }
};

export default apiService;