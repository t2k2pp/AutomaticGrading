#!/bin/bash

# ========================================
# PM試験AI採点システム - ログ表示スクリプト
# ========================================

echo "================================================"
echo "PM試験AI採点システム - ログ表示"
echo "================================================"

if [ "$1" ]; then
    echo "サービス $1 のログを表示します (Ctrl+C で終了):"
    docker-compose logs -f "$1"
else
    echo "全サービスのログを表示します (Ctrl+C で終了):"
    echo "特定のサービスのみ表示する場合: ./logs.sh [service-name]"
    echo "利用可能なサービス: api, ai_engine, web, postgres, redis, celery_worker, flower"
    echo ""
    docker-compose logs -f
fi