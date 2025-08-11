"""OpenAI service for summarizing thread content."""

import logging
from typing import List, Dict, Any, Tuple

from openai import OpenAI
from openai.types.chat import ChatCompletion

from .config import settings

logger = logging.getLogger(__name__)


class OpenAIService:
    """Service for interacting with OpenAI API."""

    def __init__(self) -> None:
        self.client = OpenAI(api_key=settings.openai_api_key)

    async def summarize_thread_content(self, messages: List[Dict[str, Any]], thread_link: str = "") -> Tuple[str, str]:
        """
        Summarize thread content using OpenAI API.

        Args:
            messages: List of message dictionaries containing text and user info
            thread_link: Link to the original Slack thread

        Returns:
            Tuple of (title, content) suitable for Canvas
        """
        try:
            # Format messages for the prompt
            formatted_messages: List[str] = []
            for msg in messages:
                user: str = msg.get('user', 'Unknown')
                text: str = msg.get('text', '')
                formatted_messages.append(f"[{user}]: {text}")

            thread_content: str = "\n".join(formatted_messages)

            prompt: str = f"""
以下はSlackスレッドでの会話内容です。この内容を読んで、主要なトピックやポイントを整理し、Canvas形式でまとめてください。

会話内容:
{thread_content}

以下の形式で出力してください：

まず、この会話内容に適切なタイトルを1行で出力してください。タイトルは「TITLE:」で始めてください。

次に、以下の形式でまとめてください：
1. 議論の概要
2. 主要なポイント
3. 決定事項（もしあれば）
4. アクションアイテム（もしあれば）
5. 今後の対策（会話の内容から推測される今後必要な対策や改善点）
6. 参考情報やリンク（もしあれば）

最後に、元のスレッドへのリンクを含めてください。

出力例：
TITLE: プロジェクトAの進捗確認と次のステップ

# 議論の概要
[ここに概要を記載]

# 主要なポイント
- ポイント1
- ポイント2

# 決定事項
- 決定1
- 決定2

# アクションアイテム
- [ ] タスク1
- [ ] タスク2

# 今後の対策
- 対策1
- 対策2

# 参考情報
- リンク1
- リンク2

---
**元のスレッド**: [こちらをクリック]({thread_link})

Markdown形式で出力してください。コードブロック（```）で囲まずに、直接Markdownテキストを出力してください。
"""

            response: ChatCompletion = self.client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": "あなたはSlackスレッドの内容を整理してCanvas用のMarkdownドキュメントを作成するアシスタントです。会話の内容を適切に要約し、分かりやすいタイトルも生成してください。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000,
                temperature=0.3
            )

            full_response: str = response.choices[0].message.content or ""

            # コードブロックで囲まれている場合は除去
            full_response = self._clean_markdown_response(full_response)

            # タイトルとコンテンツを分離
            title, content = self._extract_title_and_content(full_response)

            logger.info("Successfully generated thread summary with title")
            return title, content

        except Exception as e:
            logger.error(f"Error summarizing thread content: {e}")
            raise

    def _clean_markdown_response(self, content: str) -> str:
        """
        OpenAIの応答からMarkdownコードブロックを除去する

        Args:
            content: OpenAIからの応答

        Returns:
            クリーンなMarkdownテキスト
        """
        content = content.strip()

        # ```markdown ... ``` パターンを除去
        if content.startswith('```markdown') and content.endswith('```'):
            content = content[11:-3].strip()

        # ``` ... ``` パターンを除去
        elif content.startswith('```') and content.endswith('```'):
            content = content[3:-3].strip()

        return content

    def _extract_title_and_content(self, response: str) -> Tuple[str, str]:
        """
        OpenAIの応答からタイトルとコンテンツを分離する

        Args:
            response: OpenAIからの応答

        Returns:
            (title, content) のタプル
        """
        lines = response.split('\n')
        title = "スレッドまとめ"  # デフォルトタイトル
        content_lines = []

        for i, line in enumerate(lines):
            if line.startswith('TITLE:'):
                title = line[6:].strip()
            elif i > 0 or not line.startswith('TITLE:'):
                content_lines.append(line)

        content = '\n'.join(content_lines).strip()
        return title, content
