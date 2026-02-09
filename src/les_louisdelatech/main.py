"""
Application entrypoint.

Responsibilities:
- Parse CLI args (-c config path, -g Google service account JSON path)
- Load TOML config (see `config.example`)
- Configure structured-ish logging for operational debugging
- Initialize Sentry (optional) and start the Discord bot

This module intentionally does not contain bot logic. All bot behavior lives in:
- `les_louisdelatech/bot.py` (core bot wiring)
- `les_louisdelatech/extensions/*` (commands and listeners)
"""

import logging
import tomllib
from argparse import ArgumentParser

import sentry_sdk

from les_louisdelatech.bot import LouisDeLaTech

logger = logging.getLogger()


def _parse_log_level(value):
    """Parse a log level value from config.

    Accepts:
    - int (e.g. 10)
    - str (e.g. "INFO", "debug")
    """
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        return logging._nameToLevel.get(value.upper())
    return None


def _configure_logging(level):
    """Configure global logging.

    `force=True` ensures we override any logging config done by dependencies.
    """
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        force=True,
    )


parser = ArgumentParser()
parser.add_argument(
    "-c",
    "--config",
    action="store",
    dest="config",
    default="/etc/LouisDeLaTech/config.toml",
    help="Path to config file",
)
parser.add_argument(
    "-g",
    "--google",
    action="store",
    dest="google",
    default="/etc/LouisDeLaTech/google.json",
    help="Path to google secrets json",
)
args = parser.parse_args()

_configure_logging(logging.INFO)
logger.info("Bot started")

with open(args.config, "rb") as f:
    config = tomllib.load(f)
logger.info("Config loaded")

log_level = _parse_log_level(config.get("log_level", "INFO"))
if log_level is None:
    logger.warning(
        "Invalid log_level in config, falling back to INFO: %s",
        config.get("log_level"),
    )
    log_level = logging.INFO
_configure_logging(log_level)
logger.info("Started bot with log level %s", logging.getLevelName(log_level))

if len(config["sentry_dsn"]) > 0:
    sentry_sdk.init(
        config["sentry_dsn"],
        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for performance monitoring.
        # We recommend adjusting this value in production.
        traces_sample_rate=0.5,
    )

bot = LouisDeLaTech(config, args.google)

bot.run(config["discord"]["token"], reconnect=True)
