"""Slack Bolt app for handling Slack events and commands in Socket Mode."""

import logging
import asyncio
from typing import Any, Dict

from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler
from slack_bolt.context.ack import Ack
from slack_bolt.context.say import Say
from slack_sdk.web.async_client import AsyncWebClient

from .config import settings
from .app import CanvasCreatorApp


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Slack app for Socket Mode
app = AsyncApp(
    token=settings.slack_bot_token,
    signing_secret=settings.slack_signing_secret
)

# Initialize canvas creator app
canvas_creator: CanvasCreatorApp = CanvasCreatorApp()


@app.event("app_mention")
async def handle_app_mention(event: Dict[str, Any], say: Say, client: AsyncWebClient) -> None:
    """Handle mentions of the bot for canvas creation."""
    try:
        text: str = event.get("text", "").lower()
        user_id: str = event["user"]
        channel: str = event["channel"]

        # Check if this is in a thread
        if "thread_ts" in event:
            thread_ts: str = event["thread_ts"]

            # Keywords that trigger immediate canvas creation
            immediate_trigger_words = [
                "まとめて", "canvas作成", "キャンバス作成", "作成して", "整理して",
                "要約して", "summary", "create", "make"
            ]

            # Check if message contains immediate trigger words
            if any(word in text for word in immediate_trigger_words):
                # Send ephemeral processing message to user only
                await client.chat_postEphemeral(
                    channel=channel,
                    user=user_id,
                    text="🔄 Canvasを作成中です。少々お待ちください...",
                    thread_ts=thread_ts
                )

                # Create canvas immediately from the current thread
                canvas_id: str = await canvas_creator.create_canvas_from_thread(
                    channel=channel,
                    thread_ts=thread_ts,
                    user_id=user_id
                )

                logger.info(f"Canvas {canvas_id} created from app mention")
            else:
                # Show confirmation dialog with Yes/No buttons (ephemeral)
                blocks = [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "📝 このスレッドの内容をCanvasにまとめますか？\n\n" +
                                    "⚠️ この操作はOpenAI APIを使用してトークンを消費します。"
                        }
                    },
                    {
                        "type": "actions",
                        "elements": [
                            {
                                "type": "button",
                                "text": {
                                    "type": "plain_text",
                                    "text": "Yes - Canvasを作成",
                                    "emoji": True
                                },
                                "style": "primary",
                                "action_id": "create_canvas_from_mention_yes",
                                "value": f"{channel}|{thread_ts}|{user_id}"
                            },
                            {
                                "type": "button",
                                "text": {
                                    "type": "plain_text",
                                    "text": "No - キャンセル",
                                    "emoji": True
                                },
                                "action_id": "create_canvas_from_mention_no",
                                "value": f"{channel}|{thread_ts}|{user_id}"
                            }
                        ]
                    }
                ]

                await client.chat_postEphemeral(
                    channel=channel,
                    user=user_id,
                    text="Canvasを作成しますか？",
                    blocks=blocks,
                    thread_ts=thread_ts
                )
        else:
            # Not in a thread, provide general help
            await say(
                text=f"<@{user_id}> 👋 slack-canvas-creator-from-threads です！\n\n"
                     "**使用方法:**\n"
                     "• スレッド内で `@slack-canvas-creator-from-threads` とメンション（確認ダイアログ付き）\n"
                     "• スレッド内で `@slack-canvas-creator-from-threads まとめて` （即座実行）\n"
                     "• `/create-canvas <スレッドURL>` でスレッドを指定\n"
                     "• `/create-canvas-from-thread` （チャンネルの最新スレッド）"
            )

    except Exception as e:
        logger.error(f"Error handling app mention: {e}")


@app.event("message")
async def handle_message_events(body: Dict[str, Any], logger) -> None:
    """Handle general message events to avoid unhandled request warnings."""
    # This is a catch-all for message events that aren't handled by specific patterns
    # We don't need to do anything here, just acknowledge the event
    pass


@app.action("create_canvas_from_mention_yes")
async def handle_mention_yes_button(ack: Ack, body: Dict[str, Any], client: AsyncWebClient) -> None:
    """Handle 'Yes' button click from thread mention."""
    await ack()

    try:
        # Parse the button value
        button_value: str = body["actions"][0]["value"]
        channel, thread_ts, user_id = button_value.split("|")

        # Send ephemeral processing message to user only
        await client.chat_postEphemeral(
            channel=channel,
            user=user_id,
            text="🔄 Canvasを作成中です。少々お待ちください...",
            thread_ts=thread_ts
        )

        # Create canvas from thread
        canvas_id: str = await canvas_creator.create_canvas_from_thread(
            channel=channel,
            thread_ts=thread_ts,
            user_id=user_id
        )

        logger.info(f"Canvas {canvas_id} created from mention Yes button click")

    except Exception as e:
        logger.error(f"Error handling mention Yes button: {e}")
        # Send error message to user only
        try:
            await client.chat_postEphemeral(
                channel=channel,
                user=user_id,
                text=f"❌ エラーが発生しました: {str(e)}",
                thread_ts=thread_ts
            )
        except Exception:
            pass


@app.action("create_canvas_from_mention_no")
async def handle_mention_no_button(ack: Ack, body: Dict[str, Any], client: AsyncWebClient) -> None:
    """Handle 'No' button click from thread mention."""
    await ack()

    try:
        # Parse the button value
        button_value: str = body["actions"][0]["value"]
        channel, thread_ts, user_id = button_value.split("|")

        # Send ephemeral cancellation message to user only
        await client.chat_postEphemeral(
            channel=channel,
            user=user_id,
            text="👍 Canvas作成をキャンセルしました。",
            thread_ts=thread_ts
        )

        logger.info(f"Canvas creation cancelled by user {user_id} from mention")

    except Exception as e:
        logger.error(f"Error handling mention No button: {e}")


async def main() -> None:
    """Main function to start the Slack app in Socket Mode."""
    try:
        # Socket mode only
        handler: AsyncSocketModeHandler = AsyncSocketModeHandler(app, settings.slack_app_token)
        await handler.start_async()
    except Exception as e:
        logger.error(f"Error starting app: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
