# Claude Codeへの引き継ぎドキュメント

## 1. プロジェクト概要

### 目的
IPAプロジェクトマネージャ試験の午後Ⅰ記述式問題に対する、AI支援型一次採点システムの構築

### 技術スタック
- **バックエンド**: Python 3.10, FastAPI, SQLAlchemy, Celery
- **AI/ML**: Transformers, LangChain, PyTorch
- **フロントエンド**: React 18, TypeScript
- **データベース**: PostgreSQL 15, Redis 7
- **インフラ**: Docker Compose, Nginx
- **モニタリング**: Prometheus, Grafana

## 2. 作成済みファイル一覧と保存方法

以下のファイルを指定のパスに保存してください：

### 基本設定ファイル
```
プロジェクトルート/
├── docker-compose.yml          # アーティファクト: docker_compose_yaml
├── .env.example                # 後述のテンプレートから作成
├── setup.sh                    # アーティファクト: build_scripts (Linux/Mac用)
├── setup.bat                   # アーティファクト: windows_batch_scripts (Windows用)
├── build.sh / build.bat
├── start.sh / start.bat
├── stop.sh / stop.bat
└── logs.sh / logs.bat
```

### 設計書（docsディレクトリに保存）
```
docs/
├── system_design.md            # アーティファクト: pm_scoring_system_design
└── docker_additional_design.md # アーティファクト: docker_additional_design
```

## 3. Claude Codeへの依頼テンプレート

以下の依頼文をClaude Codeに送信してください：

```
PM試験AI採点システムの実装をお願いします。

## プロジェクト情報
- 設計書が docs/ ディレクトリにあります
- Docker環境は構築済みです（docker-compose.yml）
- 基本的なディレクトリ構造は作成済みです

## 実装依頼内容

### Phase 1: 基礎実装（優先度：高）

1. **FastAPI基本実装** (src/api/main.py)
   - ヘルスチェックエンドポイント（/health）
   - 基本的なCORS設定
   - エラーハンドリング
   - ロギング設定

2. **データベースモデル** (src/api/models/)
   - SQLAlchemyモデルの定義（exams, questions, candidates, answers, scoring_results）
   - Alembicマイグレーション設定
   - 初期データ投入スクリプト

3. **採点APIエンドポイント** (src/api/routers/scoring.py)
   - POST /api/scoring/submit - 解答提出
   - GET /api/scoring/results/{exam_id} - 採点結果取得
   - POST /api/scoring/evaluate - AI採点実行

4. **AI採点エンジンの基本実装** (src/ai_engine/)
   - ルールベース採点クラス
   - 意味理解採点クラス（モック実装でOK）
   - スコア統合ロジック

### Phase 2: フロントエンド実装（優先度：中）

1. **React基本セットアップ** (src/web/)
   - Create React Appまたは Next.js
   - TypeScript設定
   - Material-UIまたはAnt Designの導入

2. **基本画面の実装**
   - ログイン画面（認証は後回しでOK）
   - 採点一覧画面
   - 採点詳細画面
   - 採点修正画面

### Phase 3: 非同期処理実装（優先度：中）

1. **Celeryタスク** (src/api/tasks/)
   - 大量採点の非同期処理
   - 進捗管理
   - エラーハンドリング

2. **WebSocket通知**
   - 採点完了通知
   - リアルタイム進捗表示

## 制約事項と注意点

1. **AI採点の安定性**
   - Temperature = 0.1 で固定
   - 複数回評価して中央値を採用
   - すべての採点理由を記録

2. **データベース設計**
   - docker/postgres/init/01_init.sql のスキーマに従う
   - UTC時刻で統一
   - 採点結果は必ず監査ログを残す

3. **セキュリティ**
   - 受験者情報は必ず匿名化
   - SQLインジェクション対策
   - 適切なバリデーション

4. **テスト**
   - 各機能に対して最低限のユニットテストを作成
   - docker-compose.test.yml でテスト環境を構築

## 開発の進め方

1. まず `./setup.sh` (Windows: `setup.bat`) を実行
2. `./build.sh` でDockerイメージをビルド
3. `./start.sh` でコンテナ起動
4. 実装しながら `docker-compose logs -f api` でログ確認
5. ホットリロードが有効なので、コード変更は即座に反映

## 質問や確認事項
- 不明な点があれば、docs/system_design.md を参照
- AI採点のロジックは docs/system_design.md の「3. 採点アルゴリズム」を参照
- Docker環境の詳細は docs/docker_additional_design.md を参照

よろしくお願いします。
```

## 4. .env ファイルテンプレート

```.env
# データベース設定
DB_USER=scoring_user
DB_PASSWORD=scoring_pass_change_in_production
DB_NAME=pm_scoring

# API設定
SECRET_KEY=your-secret-key-change-in-production
ENVIRONMENT=development
LOG_LEVEL=INFO

# AI設定
AI_MODEL=gpt-4
OPENAI_API_KEY=your-openai-api-key-here
TEMPERATURE=0.1
MAX_TOKENS=1000

# Redis設定
REDIS_URL=redis://redis:6379

# 開発ツール設定
PGADMIN_EMAIL=admin@example.com
PGADMIN_PASSWORD=admin
JUPYTER_TOKEN=scoring2024

# その他
API_URL=http://localhost:8000
NODE_ENV=development
TZ=Asia/Tokyo
```

## 5. 必要なディレクトリ構造

Claude Codeに以下のディレクトリ構造を作成してもらってください：

```
pm-scoring-system/
├── docker/
│   ├── postgres/init/01_init.sql
│   ├── ai_engine/Dockerfile
│   ├── api/Dockerfile
│   ├── web/Dockerfile
│   └── nginx/
│       └── conf.d/default.conf
├── src/
│   ├── api/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── exam.py
│   │   │   ├── question.py
│   │   │   ├── answer.py
│   │   │   └── scoring.py
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   ├── health.py
│   │   │   ├── scoring.py
│   │   │   └── admin.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── scoring_service.py
│   │   │   └── ai_service.py
│   │   ├── tasks/
│   │   │   ├── __init__.py
│   │   │   └── scoring_tasks.py
│   │   └── utils/
│   │       ├── __init__.py
│   │       └── validators.py
│   ├── ai_engine/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── scoring/
│   │   │   ├── __init__.py
│   │   │   ├── rule_based.py
│   │   │   ├── semantic.py
│   │   │   ├── comprehensive.py
│   │   │   └── integrator.py
│   │   └── utils/
│   │       ├── __init__.py
│   │       └── text_processing.py
│   └── web/
│       ├── package.json
│       ├── tsconfig.json
│       ├── public/
│       └── src/
│           ├── App.tsx
│           ├── index.tsx
│           ├── components/
│           ├── pages/
│           ├── services/
│           └── utils/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── data/
│   ├── input/
│   └── output/
├── models/
├── notebooks/
├── logs/
├── docs/
│   ├── system_design.md
│   └── docker_additional_design.md
├── docker-compose.yml
├── docker-compose.override.yml
├── docker-compose.test.yml
├── .env.example
├── .gitignore
├── README.md
├── requirements_api.txt
├── requirements_ai.txt
└── requirements_jupyter.txt
```

## 6. 実装の優先順位とマイルストーン

### Milestone 1: 基本動作確認（1-2日）
- [ ] Docker環境の起動確認
- [ ] ヘルスチェックエンドポイントの実装
- [ ] データベース接続確認
- [ ] 基本的なCRUD操作

### Milestone 2: 採点機能の実装（3-5日）
- [ ] 採点APIの実装
- [ ] ルールベース採点の実装
- [ ] 採点結果の保存と取得
- [ ] テストデータでの動作確認

### Milestone 3: UI実装（3-5日）
- [ ] 基本的な画面レイアウト
- [ ] APIとの接続
- [ ] 採点結果の表示
- [ ] 採点修正機能

### Milestone 4: AI統合（5-7日）
- [ ] LLM接続設定
- [ ] 意味理解採点の実装
- [ ] 総合評価採点の実装
- [ ] 採点精度の検証

### Milestone 5: 本番準備（3-5日）
- [ ] パフォーマンステスト
- [ ] セキュリティチェック
- [ ] ドキュメント整備
- [ ] デプロイメント準備

## 7. テスト用サンプルデータ

```python
# tests/fixtures/sample_data.py
SAMPLE_EXAM = {
    "year": 2024,
    "season": "autumn",
    "question_number": "問1",
    "question_text": "プロジェクトでリスクが顕在化した理由を40字以内で述べよ。",
    "model_answer": "要員のスキル不足により、設計段階での品質問題が見過ごされ、後工程で大規模な手戻りが発生したため。",
    "grading_intention": "リスク管理の理解度と、具体的な原因分析能力を評価する。",
    "keywords": ["スキル不足", "品質問題", "手戻り", "要員", "設計段階"]
}

SAMPLE_ANSWERS = [
    {
        "candidate_id": "TEST001",
        "answer_text": "メンバーの技術力が不足していたため、初期段階でのレビューが不十分となり、後に修正が必要となった。"
    },
    {
        "candidate_id": "TEST002",
        "answer_text": "プロジェクト開始時のリスク評価が甘く、必要なスキルを持つ要員の確保が遅れたため。"
    }
]
```

## 8. トラブルシューティング

### よくある問題と解決策

| 問題 | 解決策 |
|------|--------|
| ポート競合 | `.env` でポート番号を変更 |
| メモリ不足 | Docker Desktop設定でメモリ割り当てを増やす |
| ビルドエラー | `docker system prune -a` 後に再ビルド |
| DB接続エラー | `docker-compose logs postgres` でログ確認 |
| ホットリロード無効 | volumeマウントの確認 |

## 9. 参考リンク

- FastAPI: https://fastapi.tiangolo.com/
- SQLAlchemy: https://www.sqlalchemy.org/
- React TypeScript: https://react-typescript-cheatsheet.netlify.app/
- Docker Compose: https://docs.docker.com/compose/
- Celery: https://docs.celeryproject.org/

## 10. Claude Codeへの追加依頼事項

必要に応じて以下も依頼してください：

1. **GitHub Actions設定**
   - `.github/workflows/ci.yml` の作成
   - 自動テスト実行
   - Dockerイメージのビルド

2. **API仕様書**
   - OpenAPI/Swagger定義
   - Postmanコレクション

3. **デプロイメント設定**
   - Kubernetes manifest
   - Helm chart
   - Terraform設定

## 重要な注意事項

1. **採点の一貫性**: 同じ解答に対して必ず同じスコアが出るようにする
2. **監査ログ**: すべての採点操作を記録する
3. **エラーハンドリング**: 適切なエラーメッセージとリトライ機構
4. **パフォーマンス**: 1000件/2時間の処理性能を目標
5. **セキュリティ**: 個人情報の適切な管理とアクセス制御