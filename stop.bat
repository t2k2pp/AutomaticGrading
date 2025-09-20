@echo off
echo ================================================
echo PM試験AI採点システム - システム停止
echo ================================================

echo システムを停止中...

REM Docker Composeで停止
docker-compose down

echo [OK] システムを停止しました

REM オプション: ボリュームも削除する場合
set /p choice="データベースのデータも削除しますか？ (y/N): "
if /i "%choice%"=="y" (
    echo データを削除中...
    docker-compose down -v
    echo [OK] データも削除しました
)

pause