# PM試験AI採点システム - Jupyter用Dockerfile
FROM jupyter/scipy-notebook:latest

# rootユーザーに切り替え
USER root

# 追加パッケージのインストール
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# jovyanユーザーに戻る
USER jovyan

# 追加のPythonパッケージをインストール
COPY requirements_jupyter.txt /tmp/
RUN pip install --no-cache-dir -r /tmp/requirements_jupyter.txt

# 作業ディレクトリ設定
WORKDIR /home/jovyan/work

# デフォルトコマンド
CMD ["start-notebook.sh"]