# Ubuntuでのsystemdデーモン化

本番環境でSlackアプリをUbuntuのsystemdサービスとして起動することができます。

## システム要件

- **OS**: Ubuntu 24.04 LTS以降
- **Python**: 3.12以降（Ubuntu 24.04にデフォルトで含まれます）
- **pip**: Python標準のパッケージマネージャー

> [:Warning]
> システムの pip がインストールされていない場合は自動インストールされます。

## 自動デプロイ

付属のデプロイスクリプトを使用して簡単にインストールできます：

```bash
# サービスをインストール
sudo ./deploy.sh install

# .envファイルを設定（必須）
sudo -u slackapp nano /opt/slack-canvas-creator-from-threads/.env

# サービスを起動
sudo systemctl start slack-canvas-creator

# サービスの状態確認
./deploy.sh status

# ログの確認
./deploy.sh logs
```

## 手動セットアップ

### 1. 専用ユーザーの作成
```bash
sudo useradd --system --create-home --home-dir /home/slackapp --shell /bin/false slackapp
```

### 2. プロジェクトファイルのコピー
```bash
sudo mkdir -p /opt/slack-canvas-creator-from-threads
sudo cp -r . /opt/slack-canvas-creator-from-threads/
sudo chown -R slackapp:slackapp /opt/slack-canvas-creator-from-threads
```

### 3. Python依存関係のインストール
```bash
cd /opt/slack-canvas-creator-from-threads

# Python 3.12以上が必要（Ubuntu 24.04以降）
python3 --version

# 依存関係をユーザーレベルでインストール
sudo -u slackapp python3 -m pip install --user -r requirements.txt
```

### 4. 環境変数ファイルの作成
```bash
sudo -u slackapp nano /opt/slack-canvas-creator-from-threads/.env
```

以下の内容を設定：
```env
SLACK_BOT_TOKEN=xoxb-...
SLACK_SIGNING_SECRET=...
OPENAI_API_KEY=sk-...
PORT=3000
HOST=0.0.0.0
```

### 5. systemdユニットファイルのインストール
```bash
sudo cp slack-canvas-creator.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable slack-canvas-creator
```

### 6. サービスの起動と確認
```bash
# サービス起動
sudo systemctl start slack-canvas-creator

# 状態確認
sudo systemctl status slack-canvas-creator

# ログ確認
sudo journalctl -u slack-canvas-creator -f
```

## セキュリティ設定

systemdユニットファイルには以下のセキュリティ設定が含まれています：

- 専用ユーザー(`slackapp`)での実行
- 最小権限でのファイルシステムアクセス
- プライベート`/tmp`ディレクトリ
- カーネル機能への制限付きアクセス
