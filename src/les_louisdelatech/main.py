import logging
from argparse import ArgumentParser
import tomllib

import sentry_sdk

from les_louisdelatech.bot import LouisDeLaTech

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s:%(message)s")
logger = logging.getLogger()

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

logger.info("Bot started")

with open(args.config, "rb") as f:
    config = tomllib.load(f)
logger.info("Config loaded")

log_level = logging.getLevelName(config["log_level"])
logger.setLevel(log_level)
logger.info(f"Started bot with log level {logging.getLevelName(logger.level)}")

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
