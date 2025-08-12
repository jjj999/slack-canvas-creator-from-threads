"""Main application logic for the Slack Canvas Creator."""

import logging
from typing import Optional, List, Dict, Any

from .slack_service import SlackService
from .openai_service import OpenAIService


logger = logging.getLogger(__name__)


class CanvasCreatorApp:
    """Main application class for creating canvases from thread content."""

    def __init__(self) -> None:
        self.slack_service: SlackService = SlackService()
        self.openai_service: OpenAIService = OpenAIService()

    async def create_canvas_from_thread(
        self,
        channel: str,
        thread_ts: str,
        user_id: str,
        canvas_title: Optional[str] = None
    ) -> str:
        """
        Create a canvas from thread content and share it with the user.

        Args:
            channel: Channel ID
            thread_ts: Thread timestamp
            user_id: User ID who requested the canvas
            canvas_title: Optional custom title for the canvas

        Returns:
            Canvas ID
        """
        try:
            # Step 1: Get thread messages
            logger.info(f"Getting thread messages for {thread_ts}")
            messages: List[Dict[str, Any]] = await self.slack_service.get_thread_messages(channel, thread_ts)

            if not messages:
                raise ValueError("No messages found in the thread")

            # Step 2: Generate thread link
            logger.info("Generating thread link")
            thread_link: str = await self.slack_service.get_thread_link(channel, thread_ts)

            # Step 3: Summarize content using OpenAI
            logger.info("Summarizing thread content with OpenAI")
            ai_title, summary = await self.openai_service.summarize_thread_content(messages, thread_link)

            # Step 4: Create canvas
            title: str = canvas_title or ai_title
            logger.info(f"Creating canvas with title: {title}")

            try:
                canvas_id: str = await self.slack_service.create_canvas(title, summary)

                # Step 5: Try to share canvas with user (optional)
                try:
                    logger.info(f"Sharing canvas with user {user_id}")
                    await self.slack_service.share_canvas_with_user(canvas_id, user_id)
                except Exception as share_error:
                    logger.warning(f"Canvas sharing failed, but canvas was created: {share_error}")

                # Step 6: Send canvas link to user
                logger.info("Sending canvas link to user")
                await self.slack_service.send_canvas_link(channel, user_id, canvas_id, thread_ts)

                logger.info(f"Successfully created and shared canvas {canvas_id}")
                return canvas_id

            except Exception as canvas_error:
                logger.warning(f"Canvas creation failed, falling back to file upload: {canvas_error}")

                # Fallback: Create as markdown file
                file_id: str = await self.slack_service.create_canvas_fallback(
                    title, summary, channel, user_id
                )

                logger.info(f"Successfully created markdown file {file_id} as fallback")
                return file_id

        except Exception as e:
            logger.error(f"Error creating canvas from thread: {e}")
            # Send error message to user
            try:
                await self.slack_service.client.chat_postMessage(
                    channel=channel,
                    text=f"<@{user_id}> Canvasの作成中にエラーが発生しました: {str(e)}",
                    thread_ts=thread_ts
                )
            except Exception:
                pass  # Don't fail if we can't send error message
            raise
