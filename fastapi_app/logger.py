import logging
import sys 
import os
from dotenv import load_dotenv
from logtail import LogtailHandler
from .globals import global_storage

#load environment variables
load_dotenv()

token = os.getenv('LOGTAIL_TOKEN')

# get logger
logger = logging.getLogger()

# create formatter 

class CustomFormatter(logging.Formatter):
    def format(self, record):
        record.model = getattr(global_storage, 'chat_model', 'No Model Selected')
        record.summariser = getattr(global_storage, 'to_summarise', False)
        return super().format(record)
    


formatter = CustomFormatter("%(asctime)s - %(levelname)s - Model: %(model)s - Summariser: %(summariser)s - %(message)s")

# create ExcludeWarningsFilter class to remove unneccessary logs (e.g. "defaulting to Cl100k")
class ExcludeWarningsFilter(logging.Filter):
    def filter(self, record):
        # Allow INFO, ERROR, and CRITICAL, but not WARNING
        if record.levelno == logging.WARNING:
            return False
        return True

# create handlers 

stream_handler = logging.StreamHandler(sys.stdout)
file_handler = logging.FileHandler('app.log')
better_stack_handler = LogtailHandler(source_token = token)

# set formatters
stream_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

# add handlers to the logger
logger.handlers = [stream_handler, file_handler, better_stack_handler]

# set log-level

logger.setLevel(logging.INFO)
exclude_warnings_filter = ExcludeWarningsFilter()
logger.addFilter(exclude_warnings_filter)

# ensuring that exclude_warnings_filter runs on all three handlers
stream_handler.addFilter(exclude_warnings_filter)
file_handler.addFilter(exclude_warnings_filter)
better_stack_handler.addFilter(exclude_warnings_filter)
