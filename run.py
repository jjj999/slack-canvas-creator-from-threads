#!/usr/bin/env python3
"""Entry point for running the Slack Canvas Creator app."""

import asyncio
from slack_canvas_creator_from_threads.main import main


if __name__ == "__main__":
    asyncio.run(main())
