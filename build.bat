@echo off
echo ================================================
echo PM試験AI採点システム - Dockerイメージビルド
echo ================================================

echo Dockerイメージをビルド中...

echo.
echo 1. クリーンアップ...
docker-compose down --remove-orphans
docker system prune -f

echo.
echo 2. イメージビルド...
docker-compose build --no-cache

echo.
echo [OK] ビルドが完了しました
echo.
echo 次のコマンドでシステムを起動してください:
echo start.bat
pause