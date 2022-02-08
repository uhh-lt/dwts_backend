import os

from loguru import logger
from omegaconf import OmegaConf

# global config
__conf_file__ = os.getenv("DWISE_BACKEND_CONFIG", "./configs/default_localhost_dev.yaml")
conf = OmegaConf.load(__conf_file__)

# setup loguru logging
logger.add(conf.logging.path + '/{time}.log',
           rotation=f"{conf.logging.max_file_size} MB",
           level=conf.logging.level.upper())

logger.info(f"Loaded config '{__conf_file__}'")
