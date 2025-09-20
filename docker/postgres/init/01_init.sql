-- PM試験AI採点システム データベース初期化SQL

-- データベース設定
SET timezone = 'Asia/Tokyo';

-- 拡張機能の有効化
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 注意: 初期データは SQLAlchemy でテーブル作成後に挿入
-- このファイルは基本的な設定のみを行います

-- 初期データは別途 FastAPI 起動時に投入されます
-- テーブル、インデックス、コメントはFastAPIから作成されます