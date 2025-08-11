# Slack Canvas Creator from Threads

SlackのスレッドからOpenAI APIを使ってトピックを整理し、Canvasを作成するSlackアプリです。

## 機能

- **スレッドのチャット内容を自動読み込み**
- **OpenAI GPT-4o-miniを使用したスレッド内容の要約**
- **AI生成による適切なCanvasタイトル作成**
- **スレッドリンクの自動挿入**（Slackアプリで開く）
- **今後の対策項目の自動生成**
- **Canvas作成中の進捗通知**
- **複数の実行方法をサポート**

## Canvas構成

生成されるCanvasには以下の項目が含まれます：

1. **議論の概要**
2. **主要なポイント**
3. **決定事項**（該当する場合）
4. **アクションアイテム**（該当する場合）
5. **今後の対策**（AI生成）
6. **参考情報やリンク**（該当する場合）
7. **元のスレッドへのリンク**（自動挿入）

## セットアップ

### 1. 依存関係のインストール

```bash
poetry install
```

### 2. 環境変数の設定

`.env.example`を`.env`にコピーして必要な値を設定：

```bash
cp .env.example .env
```

以下の環境変数を設定してください：

```env
# Slack設定
SLACK_BOT_TOKEN=xoxb-...           # SlackボットのOAuthトークン
SLACK_SIGNING_SECRET=...           # Slackアプリの署名シークレット
SLACK_APP_TOKEN=xapp-...           # Socket Mode用のアプリトークン（開発環境）

# OpenAI設定
OPENAI_API_KEY=sk-...              # OpenAI APIキー
OPENAI_MODEL=gpt-4o-mini           # 使用するOpenAIモデル（デフォルト）

# サーバー設定（本番環境）
PORT=3000                          # サーバーポート（デフォルト）
```

### 3. Slackアプリの設定

#### 必要なBot Token Scopes
```
channels:history     # チャンネルメッセージ履歴の読み取り
groups:history       # プライベートチャンネル履歴の読み取り
chat:write          # メッセージ送信
chat:write.public   # パブリックチャンネルへのメッセージ送信
canvases:write      # Canvas作成・編集
commands            # スラッシュコマンド
app_mentions:read   # アプリメンションの受信
channels:read       # チャンネル情報の読み取り
files:write         # ファイルアップロード（フォールバック用）
```

#### Event Subscriptions
```
app_mention         # ボットへのメンション
message.channels    # チャンネルメッセージ
message.groups      # プライベートチャンネルメッセージ
```

#### スラッシュコマンド
- コマンド: `/create-canvas`
- 説明: Create a Canvas from thread URL

## 使用方法

### アプリの起動

#### 開発環境（Socket Mode）
```bash
python -m slack_canvas_creator_from_threads.main
```

#### 本番環境（HTTP Mode）
```bash
# サーバー起動
python run.py

# ngrokを使用してHTTPSエンドポイントを作成
ngrok http 3000
```

## Ubuntuでのsystemdデーモン化

本番環境でSlackアプリをUbuntuのsystemdサービスとして起動することができます。

### 自動デプロイ

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

### 手動セットアップ

#### 1. 専用ユーザーの作成
```bash
sudo useradd --system --home-dir /opt/slack-canvas-creator-from-threads --shell /bin/false slackapp
```

#### 2. プロジェクトファイルのコピー
```bash
sudo mkdir -p /opt/slack-canvas-creator-from-threads
sudo cp -r . /opt/slack-canvas-creator-from-threads/
sudo chown -R slackapp:slackapp /opt/slack-canvas-creator-from-threads
```

#### 3. Poetry環境のセットアップ
```bash
cd /opt/slack-canvas-creator-from-threads
sudo -u slackapp poetry install --only=main
```

#### 4. 環境変数ファイルの作成
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

#### 5. systemdユニットファイルのインストール
```bash
sudo cp slack-canvas-creator.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable slack-canvas-creator
```

#### 6. サービスの起動と確認
```bash
# サービス起動
sudo systemctl start slack-canvas-creator

# 状態確認
sudo systemctl status slack-canvas-creator

# ログ確認
sudo journalctl -u slack-canvas-creator -f
```

### サービス管理コマンド

```bash
# サービス起動
sudo systemctl start slack-canvas-creator

# サービス停止
sudo systemctl stop slack-canvas-creator

# サービス再起動
sudo systemctl restart slack-canvas-creator

# サービスの自動起動有効化
sudo systemctl enable slack-canvas-creator

# サービスの自動起動無効化
sudo systemctl disable slack-canvas-creator

# ログ確認
sudo journalctl -u slack-canvas-creator -f
```

### デプロイスクリプトのコマンド

```bash
# インストール（要sudo）
sudo ./deploy.sh install

# アンインストール（要sudo）
sudo ./deploy.sh uninstall

# 再起動
./deploy.sh restart

# 状態確認
./deploy.sh status

# ログ表示
./deploy.sh logs
```

### セキュリティ設定

systemdユニットファイルには以下のセキュリティ設定が含まれています：

- 専用ユーザー(`slackapp`)での実行
- 最小権限でのファイルシステムアクセス
- プライベート`/tmp`ディレクトリ
- カーネル機能への制限付きアクセス

### Canvas作成の4つの方法

#### 1. スレッドURLを指定（どこからでも実行可能）
任意のチャンネルで以下のようにスレッドのURLを指定：
```
/create-canvas https://yourworkspace.slack.com/archives/C1234567890/p1234567890123456
```

**スレッドURLの取得方法：**
1. スレッドの最初のメッセージにマウスオーバー
2. 「︙」（その他のアクション）をクリック
3. 「リンクをコピー」を選択
4. コピーしたURLを `/create-canvas` の後に貼り付け

#### 2. スレッド内でボットにメンション（最も簡単）
スレッド内で以下のようにボットにメンション：
```
@slack-canvas-creator-from-threads まとめて
@slack-canvas-creator-from-threads canvasを作成
@slack-canvas-creator-from-threads この内容を整理して
```

#### 3. スレッド内で自然言語（簡単）
スレッド内で以下のようなメッセージを送信：
- 「canvasを作成して」
- 「この内容をcanvasにまとめて」
- 「まとめてcanvas」
- 「canvas化して」

#### 4. スレッド内でボタンクリック（最も直感的）
スレッド内で「canvas」というキーワードを含むメッセージを送信すると、Canvas作成ボタンが表示されます。

### 実行フロー

1. **即座に処理開始通知**
   ```
   Canvas生成中です...しばらくお待ちください
   ```

2. **AI処理とCanvas作成**
   - スレッドメッセージの取得
   - スレッドリンクの生成
   - OpenAI APIによる要約とタイトル生成
   - Canvas作成

3. **完了通知**
   ```
   スレッドの内容をまとめたCanvasを作成しました！

   Canvas: [AI生成タイトル]
   https://yourworkspace.slack.com/docs/T123456789/F099CANVAS1
   ```

## プロジェクト構造

```
slack_canvas_creator_from_threads/
├── __init__.py          # パッケージの初期化
├── config.py           # 設定管理（Pydantic）
├── main.py             # Slackアプリのメインエントリーポイント
├── app.py              # アプリケーションのメインロジック
├── slack_service.py    # Slack API操作
└── openai_service.py   # OpenAI API操作
```

## 技術仕様

- **Python**: 3.12+
- **Slack Framework**: Slack Bolt for Python
- **AI Model**: OpenAI GPT-4o-mini
- **Configuration**: Pydantic Settings
- **Connection Mode**: Socket Mode（開発）/ HTTP Mode（本番）

## 注意事項

- **スラッシュコマンドはスレッド内では実行できません**（Slackの制限）
- Canvas APIが利用できない場合、自動的にMarkdownファイルとしてアップロードされます
- OpenAI APIの使用には料金が発生します
- Canvas機能を使用するには、SlackワークスペースでCanvas機能が有効になっている必要があります
- スレッドリンクはSlackアプリで開くように設定されています

## トラブルシューティング

### Canvas作成に失敗する場合
1. Canvas APIの権限を確認
2. ワークスペースでCanvas機能が有効か確認
3. 自動的にMarkdownファイルのフォールバックが実行されるか確認

### OpenAI APIエラーの場合
1. APIキーが正しく設定されているか確認
2. OpenAIアカウントの残高を確認
3. レート制限に達していないか確認

### Socket Mode接続エラーの場合
1. `SLACK_APP_TOKEN`が正しく設定されているか確認
2. Slack AppでSocket Modeが有効になっているか確認

## ライセンス

MIT License
