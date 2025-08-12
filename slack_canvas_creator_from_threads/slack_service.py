"""Slack service for handling thread operations and Canvas creation."""

import logging
from typing import List, Dict, Any, Optional

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from slack_sdk.web import SlackResponse

from .config import settings


logger = logging.getLogger(__name__)


class SlackService:
    """Service for Slack API operations."""

    def __init__(self) -> None:
        self.client: WebClient = WebClient(token=settings.slack_bot_token)

    async def get_thread_messages(self, channel: str, thread_ts: str) -> List[Dict[str, Any]]:
        """
        Get all messages from a thread.

        Args:
            channel: Channel ID
            thread_ts: Thread timestamp

        Returns:
            List of message dictionaries
        """
        try:
            response: SlackResponse = self.client.conversations_replies(
                channel=channel,
                ts=thread_ts,
                inclusive=True
            )

            messages: List[Dict[str, Any]] = []
            for message in response["messages"]:
                # Skip bot messages and only include text messages
                if not message.get("bot_id") and message.get("text"):
                    messages.append({
                        "user": message.get("user", "Unknown"),
                        "text": message.get("text", ""),
                        "ts": message.get("ts", "")
                    })

            logger.info(f"Retrieved {len(messages)} messages from thread {thread_ts}")
            return messages

        except SlackApiError as e:
            logger.error(f"Error getting thread messages: {e.response['error']}")
            raise

    async def get_thread_link(self, channel: str, thread_ts: str) -> str:
        """
        Generate a link to the specific thread that opens in Slack app.

        Args:
            channel: Channel ID
            thread_ts: Thread timestamp

        Returns:
            URL to the thread that opens in Slack app
        """
        try:
            # Get workspace info
            auth_response: SlackResponse = self.client.auth_test()
            team_url: str = auth_response.get("url", "")

            # Extract workspace domain from team URL (e.g., https://yusa-group.slack.com/)
            if team_url:
                workspace_domain = team_url.rstrip('/')
            else:
                # Fallback: try to get team domain from team info
                team_info_response: SlackResponse = self.client.team_info()
                team_domain = team_info_response.get("team", {}).get("domain", "")
                workspace_domain = f"https://{team_domain}.slack.com" if team_domain else "https://slack.com"

            # Convert timestamp to p-format for URL (remove dot and pad with zeros)
            ts_parts = thread_ts.split('.')
            p_timestamp = f"p{ts_parts[0]}{ts_parts[1].ljust(6, '0')}"

            # Generate link in format: https://workspace.slack.com/archives/CHANNEL/pTIMESTAMP
            thread_link = f"{workspace_domain}/archives/{channel}/{p_timestamp}"

            logger.info(f"Generated thread link: {thread_link}")
            return thread_link

        except SlackApiError as e:
            logger.error(f"Error generating thread link: {e.response['error']}")
            # Return a fallback link
            return f"https://slack.com/archives/{channel}/{thread_ts.replace('.', '')}"
        except Exception as e:
            logger.error(f"Unexpected error generating thread link: {e}")
            return f"https://slack.com/archives/{channel}/{thread_ts.replace('.', '')}"

    async def send_processing_message(self, channel: str, user_id: str, thread_ts: str) -> str:
        """
        Send a "Canvas生成中" message to indicate processing has started.
        Note: This method is disabled to avoid duplicate processing messages.

        Args:
            channel: Channel ID
            user_id: User ID who requested the canvas
            thread_ts: Thread timestamp

        Returns:
            Message timestamp of the processing message (empty string since disabled)
        """
        # Disabled to avoid duplicate processing messages
        # Ephemeral messages are used instead in the button handlers
        logger.info("Processing message sending is disabled - using ephemeral messages instead")
        return ""

    async def create_canvas(self, title: str, content: str) -> str:
        """
        Create a new Canvas with the given content.

        Args:
            title: Canvas title
            content: Canvas content in Markdown format

        Returns:
            Canvas ID
        """
        try:
            response: SlackResponse = self.client.canvases_create(
                title=title,
                document_content={
                    "type": "markdown",
                    "markdown": content
                }
            )

            logger.info(f"Canvas API response: {response}")

            # Check if response contains canvas data
            if not response.get("ok"):
                raise SlackApiError(f"Canvas creation failed: {response.get('error', 'Unknown error')}", response)

            # Handle different response formats
            canvas_id = None
            if "canvas_id" in response:
                canvas_id = response["canvas_id"]
            elif "canvas" in response and response["canvas"] and "id" in response["canvas"]:
                canvas_id = response["canvas"]["id"]

            if not canvas_id:
                raise SlackApiError("Canvas creation response missing canvas ID", response)

            logger.info(f"Created canvas with ID: {canvas_id}")
            return canvas_id

        except SlackApiError as e:
            logger.error(f"Error creating canvas: {e.response['error']}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating canvas: {e}")
            raise

    async def create_canvas_fallback(self, title: str, content: str, channel: str, user_id: str) -> str:
        """
        Create a text file as fallback when Canvas API is not available.

        Args:
            title: Document title
            content: Document content in Markdown format
            channel: Channel to upload file to
            user_id: User ID for notification

        Returns:
            File ID
        """
        try:
            # Create markdown file content
            file_content = f"# {title}\n\n{content}"

            # Upload as file using the newer API
            response = self.client.files_upload_v2(
                channel=channel,
                content=file_content,
                filename=f"{title}.md",
                title=title,
                initial_comment=f"<@{user_id}> Canvas APIが利用できないため、Markdownファイルとして作成しました。"
            )

            if response["ok"]:
                file_id = response["file"]["id"]
                logger.info(f"Created markdown file with ID: {file_id}")
                return file_id
            else:
                raise SlackApiError(f"File upload failed: {response.get('error')}", response)

        except SlackApiError as e:
            logger.error(f"Error uploading file: {e.response['error']}")
            raise

    async def share_canvas_with_user(self, canvas_id: str, user_id: str) -> None:
        """
        Give write access to a user for the canvas.

        Args:
            canvas_id: Canvas ID
            user_id: User ID to give access to
        """
        try:
            self.client.canvases_access_set(
                canvas_id=canvas_id,
                access_level="write",
                user_ids=[user_id]
            )

            logger.info(f"Granted write access to user {user_id} for canvas {canvas_id}")

        except SlackApiError as e:
            logger.error(f"Error sharing canvas: {e.response['error']}")
            raise

    async def send_canvas_link(self, channel: str, user_id: str, canvas_id: str, thread_ts: Optional[str] = None) -> None:
        """
        Send a message with the canvas link to the user.

        Args:
            channel: Channel to send message to
            user_id: User ID to mention
            canvas_id: Canvas ID
            thread_ts: Thread timestamp (optional, for replying in thread)
        """
        try:
            # Canvas URLの正しい形式: https://workspace.slack.com/docs/TEAM_ID/CANVAS_ID
            # チーム情報を取得して正確なURLを生成

            workspace_url = None
            team_id = None

            try:
                # チーム情報を取得（team:read権限は不要、auth.testで代用）
                auth_response = self.client.auth_test()
                if auth_response.get("ok"):
                    team_id = auth_response.get("team_id")
                    team_url = auth_response.get("url")  # https://workspace.slack.com/
                    if team_url:
                        # URLから正しいワークスペースドメインを抽出
                        workspace_url = team_url.rstrip('/')
                        logger.info(f"Workspace URL: {workspace_url}, Team ID: {team_id}")
            except Exception as e:
                logger.warning(f"Could not get workspace info: {e}")

            # 正しいCanvas URL形式を生成
            canvas_url = None
            if workspace_url and team_id:
                canvas_url = f"{workspace_url}/docs/{team_id}/{canvas_id}"
                logger.info(f"Generated Canvas URL: {canvas_url}")

            # Create simple message with Canvas link
            if canvas_url:
                message: str = f"<@{user_id}> ✅ スレッドの内容をまとめたCanvasを作成しました！\n\n{canvas_url}"
            else:
                # フォールバック: ワークスペース情報が取得できない場合
                message: str = f"<@{user_id}> ✅ スレッドの内容をまとめたCanvasを作成しました！\n\nCanvas ID: `{canvas_id}`\nSlack内で検索してアクセスしてください。"

            self.client.chat_postMessage(
                channel=channel,
                text=message,
                thread_ts=thread_ts
            )

            logger.info(f"Sent canvas link to user {user_id}")

        except SlackApiError as e:
            logger.error(f"Error sending canvas link: {e.response['error']}")
            raise

    async def send_ephemeral_message(self, channel: str, user_id: str, text: str, blocks: Optional[List[Dict[str, Any]]] = None, thread_ts: Optional[str] = None) -> None:
        """
        Send an ephemeral message that only the specified user can see.

        Args:
            channel: Channel to send message to
            user_id: User ID who will see the message
            text: Message text
            blocks: Optional blocks for rich formatting
            thread_ts: Optional thread timestamp to send message in thread
        """
        try:
            kwargs = {
                "channel": channel,
                "user": user_id,
                "text": text
            }

            if blocks:
                kwargs["blocks"] = blocks

            if thread_ts:
                kwargs["thread_ts"] = thread_ts

            self.client.chat_postEphemeral(**kwargs)

            logger.info(f"Sent ephemeral message to user {user_id}")

        except SlackApiError as e:
            logger.error(f"Error sending ephemeral message: {e.response['error']}")
            raise
