# プロジェクトマネージャ試験 記述式問題 AI一次採点システム設計書

## 1. システム概要

### 1.1 目的
IPAプロジェクトマネージャ試験の午後Ⅰ記述式問題に対する受験者の解答を、生成AIとプログラムを組み合わせて一次採点し、人間による二次採点の効率化と採点品質の向上を実現する。

### 1.2 基本方針
- **採点の安定性を最優先**：確率的なばらつきを最小化
- **透明性の確保**：採点理由を明確に提示
- **人間採点者の支援**：最終判断は人間が実施

## 2. システムアーキテクチャ

### 2.1 全体構成

```
┌─────────────────────────────────────────┐
│             入力データ層                  │
├─────────────────────────────────────────┤
│  ・問題文 ・設問 ・解答例                 │
│  ・出題趣旨 ・採点講評 ・受験者解答       │
└─────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────┐
│           前処理モジュール                │
├─────────────────────────────────────────┤
│  ・データ検証 ・形式正規化               │
│  ・キーワード抽出                        │
└─────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────┐
│         AI採点エンジン（3段階）           │
├─────────────────────────────────────────┤
│  1. ルールベース採点                     │
│  2. 意味理解採点                         │
│  3. 総合評価採点                         │
└─────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────┐
│           後処理モジュール                │
├─────────────────────────────────────────┤
│  ・スコア統合 ・信頼度算出               │
│  ・採点理由生成                          │
└─────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────┐
│         人間採点者インターフェース        │
├─────────────────────────────────────────┤
│  ・一次採点結果表示 ・修正機能           │
│  ・最終承認機能                          │
└─────────────────────────────────────────┘
```

## 3. 採点アルゴリズム

### 3.1 三層採点アプローチ

#### 第1層：ルールベース採点（30%）
```python
class RuleBasedScoring:
    def __init__(self):
        self.keyword_weights = {}  # キーワードと配点の対応表
        self.pattern_rules = []    # 解答パターンのルール
    
    def score(self, answer, model_answer, keywords):
        score = 0
        max_score = 100
        
        # キーワードマッチング
        for keyword, weight in keywords.items():
            if keyword in answer:
                score += weight
        
        # 文字数チェック
        if len(answer) < MIN_LENGTH or len(answer) > MAX_LENGTH:
            score *= 0.8
        
        # 必須要素チェック
        required_elements = self.extract_required_elements(model_answer)
        for element in required_elements:
            if element not in answer:
                score -= 10
        
        return min(score, max_score) / 100
```

#### 第2層：意味理解採点（40%）
```python
class SemanticScoring:
    def __init__(self, llm_model):
        self.llm = llm_model
        self.embedding_model = load_embedding_model()
    
    def score(self, answer, model_answer, context):
        # ベクトル類似度による評価
        answer_vec = self.embedding_model.encode(answer)
        model_vec = self.embedding_model.encode(model_answer)
        similarity = cosine_similarity(answer_vec, model_vec)
        
        # LLMによる意味的妥当性評価
        prompt = f"""
        【問題文】{context['question']}
        【模範解答】{model_answer}
        【受験者解答】{answer}
        【出題趣旨】{context['purpose']}
        
        受験者解答を以下の観点で評価してください：
        1. 出題趣旨との合致度（40点）
        2. 論理的整合性（30点）
        3. 専門用語の適切な使用（20点）
        4. 具体性と実践性（10点）
        
        各観点の点数と理由を明記してください。
        """
        
        llm_score = self.llm.evaluate(prompt)
        
        # 複数回評価して平均を取る（安定性向上）
        scores = []
        for _ in range(3):
            scores.append(self.llm.evaluate(prompt))
        
        return np.median(scores) / 100
```

#### 第3層：総合評価採点（30%）
```python
class ComprehensiveScoring:
    def __init__(self):
        self.context_analyzer = ContextAnalyzer()
        
    def score(self, answer, all_answers, question_context):
        # 問題全体の文脈での一貫性評価
        consistency_score = self.evaluate_consistency(answer, all_answers)
        
        # プロジェクトマネジメント観点での評価
        pm_perspective_score = self.evaluate_pm_perspective(answer, question_context)
        
        # 実務的妥当性の評価
        practical_score = self.evaluate_practicality(answer)
        
        return (consistency_score * 0.4 + 
                pm_perspective_score * 0.4 + 
                practical_score * 0.2)
```

### 3.2 スコア統合と信頼度計算

```python
class ScoreIntegrator:
    def integrate_scores(self, rule_score, semantic_score, comprehensive_score):
        # 重み付き平均
        weights = [0.3, 0.4, 0.3]
        base_score = (rule_score * weights[0] + 
                     semantic_score * weights[1] + 
                     comprehensive_score * weights[2])
        
        # 信頼度の計算
        score_variance = np.var([rule_score, semantic_score, comprehensive_score])
        confidence = 1 - min(score_variance * 2, 0.5)  # 最大50%の不確実性
        
        return {
            'score': base_score * 100,
            'confidence': confidence,
            'component_scores': {
                'rule_based': rule_score,
                'semantic': semantic_score,
                'comprehensive': comprehensive_score
            }
        }
```

## 4. 採点の安定性確保メカニズム

### 4.1 Temperature制御
```python
LLM_CONFIG = {
    'temperature': 0.1,  # 低温度で出力の確定性を高める
    'top_p': 0.95,
    'frequency_penalty': 0,
    'presence_penalty': 0
}
```

### 4.2 複数評価とアンサンブル
```python
def ensemble_scoring(answer, evaluators, n_iterations=5):
    all_scores = []
    
    for evaluator in evaluators:
        iteration_scores = []
        for _ in range(n_iterations):
            score = evaluator.evaluate(answer)
            iteration_scores.append(score)
        
        # 外れ値を除外してmedianを採用
        filtered_scores = remove_outliers(iteration_scores)
        all_scores.append(np.median(filtered_scores))
    
    return np.mean(all_scores)
```

### 4.3 キャリブレーション
```python
class ScoreCalibrator:
    def __init__(self):
        self.historical_scores = []
        self.human_scores = []
    
    def calibrate(self, ai_score):
        # 過去の採点データから補正係数を学習
        if len(self.historical_scores) > 100:
            correction_factor = self.calculate_correction_factor()
            calibrated_score = ai_score * correction_factor
        else:
            calibrated_score = ai_score
        
        return np.clip(calibrated_score, 0, 100)
```

## 5. データ構造とインターフェース

### 5.1 入力データフォーマット
```json
{
  "exam_info": {
    "year": "2024",
    "season": "autumn",
    "question_number": "問1"
  },
  "question_data": {
    "problem_statement": "プロジェクト概要...",
    "sub_questions": [
      {
        "id": "設問1",
        "question": "リスクが顕在化した理由を40字以内で述べよ",
        "max_chars": 40,
        "points": 25
      }
    ]
  },
  "reference_data": {
    "model_answer": "要員のスキル不足により...",
    "grading_intention": "リスク管理の理解度を問う",
    "grading_commentary": "多くの受験者が...",
    "keywords": ["スキル不足", "要員", "リスク管理"]
  },
  "candidate_answer": "プロジェクトメンバーの..."
}
```

### 5.2 出力フォーマット
```json
{
  "scoring_result": {
    "total_score": 18,
    "max_score": 25,
    "percentage": 72,
    "confidence": 0.85,
    "grade": "B"
  },
  "detailed_scores": {
    "rule_based": 70,
    "semantic": 75,
    "comprehensive": 69
  },
  "scoring_reasons": [
    {
      "aspect": "キーワードの網羅性",
      "score": 8,
      "max": 10,
      "comment": "主要キーワード3つ中2つを含んでいます"
    },
    {
      "aspect": "論理的整合性",
      "score": 7,
      "max": 10,
      "comment": "因果関係が明確に述べられています"
    }
  ],
  "suggestions_for_human_reviewer": [
    "実務的観点での妥当性を確認してください",
    "専門用語の使用が適切か再確認が必要です"
  ],
  "similar_answers": [
    {
      "id": "candidate_042",
      "similarity": 0.89,
      "note": "類似解答の可能性があります"
    }
  ]
}
```

## 6. 人間採点者向けインターフェース

### 6.1 ダッシュボード機能
- **一覧表示**：全受験者の一次採点結果一覧
- **フィルタリング**：信頼度、スコア範囲での絞り込み
- **ソート**：各種項目でのソート機能
- **一括処理**：複数解答の一括承認/却下

### 6.2 詳細採点画面
```html
<!-- 採点詳細画面のモックアップ -->
<div class="scoring-detail">
  <div class="original-answer">
    <!-- 受験者解答（ハイライト付き） -->
  </div>
  <div class="ai-scoring">
    <!-- AI採点結果と根拠 -->
  </div>
  <div class="reference-info">
    <!-- 模範解答、出題趣旨 -->
  </div>
  <div class="human-override">
    <!-- スコア修正、コメント追加 -->
  </div>
</div>
```

## 7. 品質保証メカニズム

### 7.1 継続的学習
```python
class ContinuousLearning:
    def update_model(self, ai_scores, human_scores):
        # 人間の採点結果を基に補正モデルを更新
        differences = human_scores - ai_scores
        
        # 誤差パターンの分析
        error_patterns = self.analyze_patterns(differences)
        
        # ファインチューニング用データセットの生成
        training_data = self.generate_training_data(error_patterns)
        
        # モデルの再学習（定期的に実施）
        self.retrain_model(training_data)
```

### 7.2 監査ログ
```python
class AuditLogger:
    def log_scoring_event(self, event_data):
        log_entry = {
            'timestamp': datetime.now(),
            'exam_id': event_data['exam_id'],
            'ai_score': event_data['ai_score'],
            'human_score': event_data.get('human_score'),
            'modifications': event_data.get('modifications', []),
            'reviewer_id': event_data.get('reviewer_id')
        }
        
        # 改竄防止のためのハッシュ値を付与
        log_entry['hash'] = self.calculate_hash(log_entry)
        
        self.save_to_database(log_entry)
```

## 8. システム要件

### 8.1 ハードウェア要件
- CPU: 16コア以上
- メモリ: 64GB以上
- GPU: NVIDIA A100 40GB以上（推論用）
- ストレージ: SSD 1TB以上

### 8.2 ソフトウェア要件
- OS: Ubuntu 22.04 LTS
- Python: 3.10以上
- 主要ライブラリ:
  - transformers 4.35以上
  - langchain 0.1以上
  - numpy, pandas, scikit-learn
  - FastAPI（APIサーバー）
  - PostgreSQL 15（データベース）

## 9. セキュリティとプライバシー

### 9.1 データ保護
- 受験者情報の匿名化処理
- 採点データの暗号化（AES-256）
- アクセス制御（RBAC）の実装

### 9.2 監査証跡
- 全操作のログ記録
- 改竄防止機能
- 定期的なセキュリティ監査

## 10. 運用フロー

### 10.1 標準採点プロセス
1. **データ投入**：試験終了後、解答データを一括投入
2. **前処理**：データ検証と正規化（30分）
3. **AI採点**：並列処理による一次採点（2時間/1000件）
4. **品質チェック**：異常値検出と再採点（30分）
5. **人間レビュー**：採点者による確認と修正（1-2日）
6. **最終承認**：責任者による最終確認
7. **結果出力**：採点結果のエクスポート

### 10.2 例外処理
- 文字数超過/不足
- 白紙解答
- 不適切な内容
- システムエラー時の復旧

## 11. 期待効果とKPI

### 11.1 期待効果
- **採点時間の短縮**：従来比60%削減
- **採点品質の向上**：採点者間のばらつき50%削減
- **透明性の向上**：採点根拠の明確化

### 11.2 KPI設定
- AI採点と人間採点の相関係数: 0.85以上
- 採点修正率: 15%以下
- システム稼働率: 99.5%以上
- 処理時間: 1000件/2時間以内

## 12. 今後の拡張計画

### Phase 1（6ヶ月）
- 基本システムの構築と検証
- パイロット運用（100件規模）

### Phase 2（12ヶ月）
- 本格運用開始
- 他の記述式試験への展開

### Phase 3（18ヶ月）
- 論述式（午後Ⅱ）への対応
- 他資格試験への展開

## 付録A：プロンプトテンプレート例

```python
SCORING_PROMPT_TEMPLATE = """
あなたはIPAプロジェクトマネージャ試験の採点者です。
以下の情報を基に、受験者の解答を採点してください。

【採点基準】
1. 出題趣旨との合致度（40%）
2. キーワードの適切な使用（20%）
3. 論理的整合性（20%）
4. 実務的妥当性（20%）

【問題文】
{question_text}

【模範解答】
{model_answer}

【出題趣旨】
{grading_intention}

【受験者解答】
{candidate_answer}

【採点指示】
- 各基準について0-100点で評価
- 評価理由を具体的に記述
- 総合点数を算出
- 改善点があれば指摘

出力フォーマット：
```json
{
  "scores": {
    "criteria_1": 点数,
    "criteria_2": 点数,
    "criteria_3": 点数,
    "criteria_4": 点数
  },
  "total_score": 総合点,
  "reasons": ["理由1", "理由2", ...],
  "improvements": ["改善点1", "改善点2", ...]
}
```
"""
```

## 付録B：実装優先順位

1. **必須機能**（Phase 1）
   - ルールベース採点
   - 基本的なLLM採点
   - 採点結果の可視化

2. **推奨機能**（Phase 2）
   - アンサンブル採点
   - 信頼度算出
   - 人間レビュー機能

3. **拡張機能**（Phase 3）
   - 継続学習機能
   - 高度な分析機能
   - 他試験への対応