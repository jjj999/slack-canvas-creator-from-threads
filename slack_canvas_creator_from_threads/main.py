"""Slack Bolt app for handling Slack events and commands."""

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

# Initialize Slack app
app = AsyncApp(
    token=settings.slack_bot_token,
    signing_secret=settings.slack_signing_secret
)

# Initialize canvas creator app
canvas_creator: CanvasCreatorApp = CanvasCreatorApp()


@app.command("/create-canvas")
async def handle_create_canvas_command(ack: Ack, command: Dict[str, Any], client: AsyncWebClient) -> None:
    """Handle the /create-canvas slash command."""
    await ack()

    try:
        channel_id: str = command["channel_id"]
        user_id: str = command["user_id"]
        text: str = command.get("text", "").strip()

        # If no argument provided, show usage (slash commands can't be run in threads)
        if not text:
            await client.chat_postEphemeral(
                channel=channel_id,
                user=user_id,
                text="📝 **Canvas作成方法**\n\n"
                     "**方法1: スレッドURLから作成**\n"
                     "`/create-canvas <スレッドのURL>`\n"
                     "例: `/create-canvas https://workspace.slack.com/archives/C123/p1234567890123456`\n\n"
                     "**方法2: メッセージリンクから作成**\n"
                     "`/create-canvas <メッセージのパーマリンク>`\n\n"
                     "**方法3: スレッド内で自然言語**\n"
                     "スレッド内で「canvasを作成して」「まとめてcanvas」などと送信\n\n"
                     "**方法4: スレッド内でボットにメンション**\n"
                     "スレッド内で `@slack-canvas-crator-from-threads まとめて` と送信"
            )
            return

        # Parse different input formats
        thread_ts = None

        # Case 1: Slack URL format
        if "slack.com" in text and "/p" in text:
            # Extract timestamp from URL like: https://workspace.slack.com/archives/C123/p1234567890123456
            url_parts = text.split("/p")
            if len(url_parts) > 1:
                timestamp_part = url_parts[1].split("?")[0]  # Remove query parameters
                thread_ts = timestamp_part[:10] + "." + timestamp_part[10:]

        # Case 2: Direct timestamp format (p1234567890123456)
        elif text.startswith("p") and len(text) >= 16:
            timestamp_part = text[1:]  # Remove 'p' prefix
            thread_ts = timestamp_part[:10] + "." + timestamp_part[10:]

        # Case 3: Already formatted timestamp (1234567890.123456)
        elif "." in text and len(text.replace(".", "")) >= 16:
            thread_ts = text

        if not thread_ts:
            await client.chat_postEphemeral(
                channel=channel_id,
                user=user_id,
                text="❌ スレッドの識別に失敗しました。\n\n"
                     "以下の形式で指定してください：\n"
                     "• SlackのスレッドURL\n"
                     "• メッセージのパーマリンク\n"
                     "• またはスレッド内で「canvasを作成」と送信"
            )
            return

        # Create canvas from thread
        canvas_id: str = await canvas_creator.create_canvas_from_thread(
            channel=channel_id,
            thread_ts=thread_ts,
            user_id=user_id
        )

        logger.info(f"Canvas {canvas_id} created successfully for user {user_id}")

    except Exception as e:
        logger.error(f"Error handling create-canvas command: {e}")
        await client.chat_postEphemeral(
            channel=command["channel_id"],
            user=command["user_id"],
            text=f"❌ エラーが発生しました: {str(e)}"
        )


@app.event("app_mention")
async def handle_app_mention(event: Dict[str, Any], say: Say) -> None:
    """Handle mentions of the bot for canvas creation."""
    try:
        text: str = event.get("text", "").lower()
        user_id: str = event["user"]
        channel: str = event["channel"]

        # Check if this is in a thread
        if "thread_ts" in event:
            thread_ts: str = event["thread_ts"]

            # Keywords that trigger canvas creation
            trigger_words = [
                "まとめ", "canvas", "キャンバス", "作成", "整理",
                "要約", "summary", "create", "make"
            ]

            # Check if message contains trigger words
            if any(word in text for word in trigger_words):
                # Create canvas from the current thread
                canvas_id: str = await canvas_creator.create_canvas_from_thread(
                    channel=channel,
                    thread_ts=thread_ts,
                    user_id=user_id
                )

                logger.info(f"Canvas {canvas_id} created from app mention")
            else:
                # Provide help message
                await say(
                    text=f"<@{user_id}> 👋 こんにちは！\n\n"
                         "このスレッドをCanvasにまとめるには、以下のように話しかけてください：\n"
                         "• `@slack-canvas-crator-from-threads まとめて`\n"
                         "• `@slack-canvas-crator-from-threads canvasを作成`\n"
                         "• `@slack-canvas-crator-from-threads この内容を整理して`",
                    thread_ts=thread_ts
                )
        else:
            # Not in a thread, provide general help
            await say(
                text=f"<@{user_id}> 👋 slack-canvas-crator-from-threads です！\n\n"
                     "**使用方法:**\n"
                     "• スレッド内で `@slack-canvas-crator-from-threads まとめて` とメンション\n"
                     "• `/create-canvas <スレッドURL>` でスレッドを指定\n"
                     "• スレッド内で「canvasを作成」などの自然言語"
            )

    except Exception as e:
        logger.error(f"Error handling app mention: {e}")


@app.message("canvas")
async def handle_canvas_mention(message: Dict[str, Any], say: Say) -> None:
    """Handle messages mentioning 'canvas' for quick canvas creation."""
    try:
        # Only respond if this is a threaded message
        if "thread_ts" in message:
            thread_ts: str = message["thread_ts"]
            channel: str = message["channel"]
            user_id: str = message["user"]

            # Check if the message contains specific keywords for canvas creation
            text: str = message.get("text", "").lower()

            # Keywords that trigger canvas creation
            trigger_phrases = [
                "canvasを作成",
                "canvas作成",
                "canvasにまとめ",
                "まとめてcanvas",
                "canvas化",
                "キャンバス作成",
                "キャンバスにまとめ"
            ]

            # Check if any trigger phrase is in the message
            should_create_canvas = any(phrase in text for phrase in trigger_phrases)

            if should_create_canvas:
                # Create canvas from the current thread
                canvas_id: str = await canvas_creator.create_canvas_from_thread(
                    channel=channel,
                    thread_ts=thread_ts,
                    user_id=user_id
                )

                logger.info(f"Canvas {canvas_id} created from message mention")
            else:
                # Provide helpful suggestion with button
                await say(
                    text=f"<@{user_id}> 💡 このスレッドをCanvasにまとめますか？",
                    thread_ts=thread_ts,
                    blocks=[
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": f"<@{user_id}> 💡 このスレッドをCanvasにまとめますか？"
                            }
                        },
                        {
                            "type": "actions",
                            "elements": [
                                {
                                    "type": "button",
                                    "text": {
                                        "type": "plain_text",
                                        "text": "📝 Canvasを作成"
                                    },
                                    "action_id": "create_canvas_button",
                                    "value": f"{channel}|{thread_ts}|{user_id}"
                                }
                            ]
                        },
                        {
                            "type": "context",
                            "elements": [
                                {
                                    "type": "mrkdwn",
                                    "text": "または「canvasを作成」「まとめて」などと送信してください"
                                }
                            ]
                        }
                    ]
                )

    except Exception as e:
        logger.error(f"Error handling canvas mention: {e}")


@app.event("message")
async def handle_message_events(body: Dict[str, Any], logger) -> None:
    """Handle general message events to avoid unhandled request warnings."""
    # This is a catch-all for message events that aren't handled by specific patterns
    # We don't need to do anything here, just acknowledge the event
    pass


@app.action("create_canvas_button")
async def handle_create_canvas_button(ack: Ack, body: Dict[str, Any], client: AsyncWebClient) -> None:
    """Handle canvas creation button click."""
    await ack()

    try:
        # Parse the button value
        button_value: str = body["actions"][0]["value"]
        channel, thread_ts, user_id = button_value.split("|")

        # Update the message to show processing
        await client.chat_update(
            channel=channel,
            ts=body["message"]["ts"],
            text="🔄 Canvasを作成中...",
            blocks=[
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "🔄 Canvasを作成中です。少々お待ちください..."
                    }
                }
            ]
        )

        # Create canvas from thread
        canvas_id: str = await canvas_creator.create_canvas_from_thread(
            channel=channel,
            thread_ts=thread_ts,
            user_id=user_id
        )

        # Update message with success
        await client.chat_update(
            channel=channel,
            ts=body["message"]["ts"],
            text="✅ Canvasが作成されました！",
            blocks=[
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"✅ <@{user_id}> Canvasが作成されました！\nCanvas IDでリンクが送信されます。"
                    }
                }
            ]
        )

        logger.info(f"Canvas {canvas_id} created from button click")

    except Exception as e:
        logger.error(f"Error handling canvas button: {e}")
        # Update message with error
        try:
            await client.chat_update(
                channel=body["channel"]["id"],
                ts=body["message"]["ts"],
                text="❌ エラーが発生しました",
                blocks=[
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"❌ エラーが発生しました: {str(e)}"
                        }
                    }
                ]
            )
        except:
            pass


async def main() -> None:
    """Main function to start the Slack app."""
    try:
        if settings.slack_app_token:
            # Socket mode (for development)
            handler: AsyncSocketModeHandler = AsyncSocketModeHandler(app, settings.slack_app_token)
            await handler.start_async()
        else:
            # HTTP mode (for production)
            await app.start_async(port=settings.port, host=settings.host)
    except Exception as e:
        logger.error(f"Error starting app: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
