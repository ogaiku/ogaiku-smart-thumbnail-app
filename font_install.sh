#!/bin/bash

# 日本語フォントインストールスクリプト
# Ubuntu/Debian系での実行を想定

echo "日本語フォントをインストールしています..."

# システムの更新
sudo apt update

# 基本的な日本語フォントパッケージをインストール
sudo apt install -y fonts-noto-cjk fonts-noto-cjk-extra

# 追加の日本語フォント
sudo apt install -y fonts-takao-gothic fonts-takao-mincho

# IPAフォント（多くの環境で推奨）
sudo apt install -y fonts-ipafont fonts-ipaexfont

# Google Noto フォント（推奨）
sudo apt install -y fonts-noto

# フォントキャッシュの更新
sudo fc-cache -fv

echo "日本語フォントのインストールが完了しました。"
echo "インストールされたフォント一覧:"
fc-list :lang=ja | head -10