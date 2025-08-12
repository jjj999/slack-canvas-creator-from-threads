# Slack Canvas Creator from Threads

SlackのスレッドからOpenAI APIを使ってトピックを整理し、Canvasを作成するSlackアプリです。

## 使い方（Slack ユーザー）

1. チャット内容を要約した Canvas を作成したいスレッドに移動
2. スレッド内でボットをメンション（何も文字を入力しないと警告ポップアップが出るので、適当に `.` などを入力）してメッセージを送信
    - 例: `@slack-canvas-creator-from-threads .`
3. Canvas を作成するかどうかの確認メッセージが表示されるので、**Yes** をクリック
4. 作成された Canvas がスレッドに投稿されます

![usage-slack-canvas-creator-from-threads](./res/usage-slack-canvas-creator-from-threads.gif)

### 作成される Canvas の文章構成

生成されるCanvasには以下の項目が含まれます：

1. **議論の概要**
2. **主要なポイント**
3. **決定事項**（該当する場合）
4. **アクションアイテム**（該当する場合）
5. **今後の対策**（AI生成）
6. **参考情報やリンク**（該当する場合）
7. **元のスレッドへのリンク**（自動挿入）

### 確認メッセージのスキップ

- 確認メッセージをスキップするには、ボットをメンションする際に特定のキーワードを含める必要があります。
- 例えば、`@slack-canvas-creator-from-threads 要約して` と入力することで、確認メッセージをスキップできます。
- スキップするためのキーワード
  - `まとめて`
  - `canvas作成`
  - `キャンバス作成`
  - `作成して`
  - `整理して`
  - `要約して`
  - `summary`
  - `create`
  - `make`

## アプリの使用方法

### 実行環境要件

- Python 3.12 以上
- 依存関係: [pyproject.toml](./pyproject.toml) を参照

### 注意事項

- Canvas機能を使用するには、SlackワークスペースでCanvas機能が有効になっている必要があります
- Canvas APIが利用できない場合、自動的にMarkdownファイルとしてアップロードされます
- OpenAI APIの使用料金は使用者の負担です
- スレッドリンクはSlackアプリで開くように設定されています

### 1. Slackアプリの作成

> [!NOTE]
> 現時点でこのアプリは Slack Marketplace に公開していません。
> 使用するためには、Slackワークスペースでアプリを手動で作成する必要があります。

1. App-Level Token の作成（Socket Mode を使用するため）
   - 必要なスコープ
     - `connections:write`  # 接続の作成・管理
2. Bot User OAuth Token の作成
    - 必要なスコープ
      - `app_mentions:read` # アプリメンションの受信
      - `canvases:write`    # Canvas作成・編集
      - `channels:history`  # チャンネルメッセージ履歴の読み取り
      - `channels:read`     # チャンネル情報の読み取り
      - `chat:write`        # メッセージ送信
      - `chat:write.public` # パブリックチャンネルへのメッセージ送信
      - `commands`          # スラッシュコマンド
      - `files:write`       # ファイルアップロード（フォールバック用）
      - `groups:history`    # プライベートチャンネル履歴の読み取り
    - Bot User OAuth Token 作成後にワークスペースにインストール
3. Event Subscriptions の設定
   - 必要なイベント
     - `app_mention`        # ボットへのメンション
     - `message.channels`   # チャンネルメッセージ
     - `message.groups`     # プライベートチャンネルメッセージ
4. 以下の情報をメモしておく
   1. Bot User OAuth Token
   2. App-Level Token
   3. Signing Secret

### 2. OpenAI API の設定

1. [OpenAI API](https://platform.openai.com/) の API キーを作成（詳細は OpenAI のドキュメントを参照）
2. API キーをメモしておく

### 3. 環境変数の設定

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
```

### 4. ローカルでの実行テスト

1. ソースコードのダウンロード
    ```bash
    git clone https://github.com/jjj999/slack-canvas-creator-from-threads.git
    cd slack-canvas-creator-from-threads/
    ```
2. 依存関係のインストール

   このプロジェクトは [Poetry](https://python-poetry.org/) を使用して依存関係を管理しています。以下のコマンドで依存関係をインストールします：

   ```bash
   poetry install
   ```

   (非推奨) pip を用いてもインストール可能です：

   ```bash
   pip install -r requirements.txt
   ```
3. アプリの起動

    poetry でインストールした場合
    ```bash
    poetry run python run.py
    ```

    pip でインストールした場合
    ```bash
    python run.py
    ```
5. Slack で動作確認

### 5. デプロイ

#### ホスティングサービスを使用する場合

- ローカルでの実行テストと同じようにして、ホスティングサービス（Heroku, AWS, GCPなど）にデプロイできます。

#### Ubuntu での systemd デーモン化

- このアプリは Socket Mode を前提としているので、ローカルマシンで起動して使用できます
- 本リポジトリでは Ubuntu での systemd を使用する方法を提供しています（詳細は[こちら](./docs/systemd.md)）

# 開発環境セットアップ

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
