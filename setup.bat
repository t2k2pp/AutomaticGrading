@echo off
setlocal EnableDelayedExpansion

echo ================================================
echo PM試験AI採点システム - 初回セットアップ
echo ================================================

REM Docker Desktopの確認
echo.
echo 1. Docker Desktopの確認...
docker version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Dockerがインストールされていません。
    echo Docker Desktopをインストールしてください。
    pause
    exit /b 1
)

docker info >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker Desktopが起動していません。
    echo 起動してから再実行してください。
    pause
    exit /b 1
)

echo [OK] Docker Desktopが正常に動作しています
docker version

REM .envファイルの作成
echo.
echo 2. 環境設定ファイルの作成...
if not exist ".env" (
    copy ".env.example" ".env"
    echo [OK] .envファイルを作成しました
    echo [注意] .envファイルでデータベースパスワードやAPIキーを設定してください
) else (
    echo [OK] .envファイルは既に存在します
)

REM 必要なディレクトリの作成
echo.
echo 3. ディレクトリ構造の確認...

for %%D in (
    "data\input"
    "data\output"
    "logs\api"
    "logs\ai"
    "logs\celery"
    "models"
    "notebooks"
) do (
    if not exist "%%D" (
        mkdir "%%D"
        echo Created: %%D
    )
)

echo [OK] ディレクトリ構造を確認しました

REM Dockerネットワークの作成
echo.
echo 4. Dockerネットワークの作成...
docker network ls | findstr "scoring_network" >nul
if errorlevel 1 (
    docker network create scoring_network
    echo [OK] Dockerネットワークを作成しました
) else (
    echo [OK] Dockerネットワークは既に存在します
)

REM セットアップ完了
echo.
echo ================================================
echo セットアップが完了しました！
echo ================================================

echo.
echo 次のステップ:
echo 1. .envファイルでAPIキーなどの設定を行ってください
echo 2. build.bat でDockerイメージをビルドしてください
echo 3. start.bat でシステムを起動してください

echo.
echo アクセス先:
echo - API: http://localhost:8000
echo - Web: http://localhost:3000
echo - 統合: http://localhost:8080
echo - API ドキュメント: http://localhost:8000/docs
echo - Flower (Celery監視): http://localhost:5555
echo - pgAdmin (開発時): http://localhost:5050
echo - Jupyter (開発時): http://localhost:8888

echo.
echo セットアップが正常に完了しました。
pause