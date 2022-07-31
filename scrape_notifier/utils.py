import logging
import toml

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(toml.load("pyproject.toml")["tool"]["poetry"]["name"])
