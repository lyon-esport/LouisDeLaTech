import logging
from argparse import ArgumentParser

import toml

from bot import LouisDeLaTech

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s:%(message)s")
logger = logging.getLogger(__name__)

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

logger.info(f"Bot started")
config = toml.load(args.config)
logger.info(f"Config loaded")

if len(config["sentry_dsn"]) > 0:
    import sentry_sdk

    sentry_sdk.init(
        config["sentry_dsn"],
        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for performance monitoring.
        # We recommend adjusting this value in production.
        traces_sample_rate=0.5,
    )

bot = LouisDeLaTech(config, args.google)

for extension in config["discord"]["initial_cogs"]:
    bot.load_extension(extension)

bot.run(config["discord"]["token"], bot=True, reconnect=True)
