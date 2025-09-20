@echo off
echo ================================================
echo PM試験AI採点システム - システム起動
echo ================================================

REM 環境確認
if not exist ".env" (
    echo エラー: .envファイルが見つかりません。setup.batを先に実行してください。
    pause
    exit /b 1
)

echo システムを起動中...

REM Docker Composeで起動
docker-compose up -d

echo.
echo 起動状況を確認中...
timeout /t 10 /nobreak >nul

echo.
echo ヘルスチェック実行中...
for /l %%i in (1,1,30) do (
    curl -f http://localhost:8000/health/live >nul 2>&1
    if not errorlevel 1 (
        echo [OK] APIサーバーが正常に起動しました
        goto :health_ok
    )
    echo API起動待機中... (%%i/30)
    timeout /t 2 /nobreak >nul
)

:health_ok
echo.
echo ================================================
echo システムが起動しました！
echo ================================================

echo.
echo アクセス先:
echo - API: http://localhost:8000
echo - Web: http://localhost:3000
echo - 統合: http://localhost:8080
echo - API ドキュメント: http://localhost:8000/docs
echo - Flower (Celery監視): http://localhost:5555
echo - pgAdmin (開発): http://localhost:5050
echo - Jupyter (開発): http://localhost:8888

echo.
echo ログ確認:
echo logs.bat でリアルタイムログを確認できます

echo.
echo 停止方法:
echo stop.bat でシステムを停止できます

pause