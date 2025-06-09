#!/usr/bin/env python3
"""
Startup script for Telegram Bot on Render
This script handles the bot startup and provides better logging for deployment
"""

import os
import sys
import logging
from bot import main

# Configure logging for deployment
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    try:
        logger.info("Starting Telegram Bot...")
        logger.info(f"Bot Token: {'*' * 10}{os.getenv('BOT_TOKEN', '')[-10:] if os.getenv('BOT_TOKEN') else 'NOT SET'}")
        logger.info(f"Admin ID: {os.getenv('ADMIN_ID', 'NOT SET')}")
        
        # Run the bot
        main()
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        sys.exit(1) 