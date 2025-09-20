# PM試験AI採点システム

IPAプロジェクトマネージャ試験の午後Ⅰ記述式問題に対する、AI支援型一次採点システムです。

## 🎯 システム概要

### 目的
- PM試験記述式問題の一次採点を自動化
- 人間による二次採点の効率化と品質向上
- 採点の透明性と一貫性の確保

### 技術スタック
- **バックエンド**: Python 3.10, FastAPI, SQLAlchemy, Celery
- **AI/ML**: 3層採点アルゴリズム（ルールベース、意味理解、総合評価）
- **フロントエンド**: React 18, TypeScript, Material-UI
- **データベース**: PostgreSQL 15, Redis 7
- **インフラ**: Docker Compose, Nginx

## 🚀 クイックスタート

### 前提条件
- Docker Desktop がインストール済み
- Git がインストール済み
- 8GB以上のRAM（推奨）

### 1. セットアップ

```bash
# Windows
setup.bat

# Linux/Mac
chmod +x setup.sh
./setup.sh
```

### 2. 環境設定

`.env`ファイルを編集して必要な設定を行ってください：

```env
# 重要: 本番環境では必ず変更してください
DB_PASSWORD=your-secure-password
SECRET_KEY=your-secret-key
OPENAI_API_KEY=your-openai-api-key  # 将来のLLM統合用
```

### 3. ビルド・起動

```bash
# Windows
build.bat
start.bat

# Linux/Mac
./build.sh
./start.sh
```

### 4. アクセス

- **統合UI**: http://localhost:8080
- **API**: http://localhost:8000
- **Web**: http://localhost:3000
- **API文書**: http://localhost:8000/docs
- **Celery監視**: http://localhost:5555

## 📁 システム構成

```
pm-scoring-system/
├── src/
│   ├── api/                # FastAPIアプリケーション
│   │   ├── models/         # データベースモデル
│   │   ├── routers/        # APIエンドポイント
│   │   ├── services/       # ビジネスロジック
│   │   ├── tasks/          # Celeryタスク
│   │   └── utils/          # ユーティリティ
│   ├── ai_engine/          # AI採点エンジン
│   │   └── scoring/        # 採点アルゴリズム
│   └── web/                # Reactフロントエンド
├── docker/                 # Docker設定
├── docs/                   # 設計書
└── tests/                  # テストコード
```

## 🧠 AI採点アルゴリズム

### 3層採点アプローチ

1. **ルールベース採点** (30%)
   - キーワードマッチング
   - 文字数チェック
   - 構造分析

2. **意味理解採点** (40%)
   - 語彙的類似度
   - 意味的妥当性
   - 論理的整合性

3. **総合評価採点** (30%)
   - PM観点評価
   - 実務的妥当性
   - 完全性評価

### 信頼度算出
- 各手法のスコア分散に基づく信頼度計算
- 異常値検出と再採点機能
- 人間レビューが必要な閾値設定

## 📊 API仕様

### 主要エンドポイント

#### 解答提出
```http
POST /api/scoring/submit
Content-Type: application/json

{
  "exam_id": 1,
  "question_id": 1,
  "candidate_id": "TEST001",
  "answer_text": "解答文"
}
```

#### AI採点実行
```http
POST /api/scoring/evaluate
Content-Type: application/json

{
  "answer_id": 1
}
```

#### 採点結果取得
```http
GET /api/scoring/results/1?candidate_id=TEST001
```

詳細は [API Documentation](http://localhost:8000/docs) を参照

## 🔧 運用・管理

### システム管理コマンド

```bash
# システム起動
./start.sh      # Linux/Mac
start.bat       # Windows

# システム停止
./stop.sh       # Linux/Mac
stop.bat        # Windows

# ログ確認
./logs.sh       # 全サービス
./logs.sh api   # 特定サービス

# ビルド（更新時）
./build.sh      # Linux/Mac
build.bat       # Windows
```

### モニタリング

- **Flower**: http://localhost:5555 - Celeryタスク監視
- **pgAdmin**: http://localhost:5050 - データベース管理（開発時）
- **Jupyter**: http://localhost:8888 - データ分析（開発時）

### ログ
```bash
# リアルタイムログ
./logs.sh

# 特定サービス
./logs.sh api
./logs.sh ai_engine
./logs.sh celery_worker
```

## 🔒 セキュリティ

### 本番環境での注意点

1. **環境変数の設定**
   ```env
   ENVIRONMENT=production
   SECRET_KEY=your-production-secret-key
   DB_PASSWORD=strong-database-password
   ```

2. **ネットワーク設定**
   - 適切なファイアウォール設定
   - SSL/TLS証明書の配置
   - 不要なポートの無効化

3. **データ保護**
   - 受験者情報の匿名化
   - 採点データの暗号化
   - 定期的なバックアップ

## 📈 パフォーマンス

### スケーリング
- **水平スケーリング**: Celery Workerの増設
- **垂直スケーリング**: CPUとメモリの増強
- **データベース最適化**: インデックス・クエリ最適化

### 目標性能
- **処理能力**: 1000件/2時間
- **AI採点精度**: 人間採点との相関係数 0.85以上
- **システム稼働率**: 99.5%以上

## 🧪 テスト

### テストデータ
初期セットアップ時に以下のテストデータが投入されます：

- **試験**: 2024年秋期PM試験
- **問題**: 2問（リスク管理関連）
- **解答**: 3件のサンプル解答

### テスト実行
```bash
# 単体テスト
docker-compose exec api pytest tests/unit/

# 統合テスト
docker-compose exec api pytest tests/integration/

# E2Eテスト
docker-compose -f docker-compose.test.yml up --abort-on-container-exit
```

## 🛠️ 開発・カスタマイズ

### 開発環境
```bash
# 開発プロファイルで起動
docker-compose --profile development up

# ホットリロード有効
# API: src/api/ の変更が自動反映
# Web: src/web/ の変更が自動反映
```

### AI採点アルゴリズムのカスタマイズ
- `src/ai_engine/scoring/` のモジュールを編集
- 重み付けは `scoring/integrator.py` で調整
- 新しい採点手法は同ディレクトリに追加

### フロントエンドのカスタマイズ
- `src/web/src/` でReactコンポーネントを編集
- Material-UIテーマは `App.tsx` で設定
- API接続は `services/apiService.ts` で管理

## 📚 追加情報

### 設計書
- [システム設計書](docs/system_design.md)
- [Docker設計書](docs/docker_additional_design.md)

### 今後の拡張計画
- **Phase 2**: LLM統合（GPT-4等）
- **Phase 3**: 論述式（午後Ⅱ）対応
- **Phase 4**: 他資格試験への展開

## ❓ トラブルシューティング

### よくある問題

| 問題 | 解決策 |
|------|--------|
| ポート競合エラー | `.env`でポート番号を変更 |
| メモリ不足 | Docker Desktopでメモリ割り当てを増やす |
| ビルドエラー | `docker system prune -a` 後に再ビルド |
| DB接続エラー | `./logs.sh postgres` でログ確認 |

### サポート
問題や要望がある場合は、以下を確認してください：
1. ログの確認（`./logs.sh`）
2. システム状態の確認（http://localhost:8000/health）
3. Docker環境の確認（`docker-compose ps`）

## 📄 ライセンス

このプロジェクトは教育・研究目的で開発されています。
商用利用の際は適切なライセンス確認を行ってください。

---

**PM試験AI採点システム v1.0.0**
© 2024 - AI-Powered Project Manager Exam Scoring System