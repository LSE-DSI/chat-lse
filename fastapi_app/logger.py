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
        record.user_context = getattr(global_storage, 'user_context', {})
        record.message_history = " | ".join(global_storage.message_history)  # Join messages into a single string
        format_string = "%(asctime)s - %(levelname)s - Model: %(model)s - Summariser: %(summariser)s - Messages: %(message_history)s - User context: %(user_context)s"
        formatter = logging.Formatter(format_string)
        return formatter.format(record)

def handle_new_message(message):
    # Process the message
    # Add the message to the history
    global_storage.message_history.append(message)


formatter = CustomFormatter("%(asctime)s - %(levelname)s - Model: %(model)s - Summariser: %(summariser)s - %(message)s - User context: %(user_context)s")

# create ExcludeWarningsFilter class to remove unneccessary logs (e.g. "defaulting to Cl100k")
class ExcludeWarningsAndHTTPFilter(logging.Filter):
    def filter(self, record):
        # Allow INFO, ERROR, and CRITICAL, but not WARNING
        if record.levelno == logging.WARNING:
            return False
        if record.getMessage().startswith("HTTP Request"):
            return False
    
        sensitive_keywords = [
            "Authenticating to PostgreSQL",
            "Creating Ollama Chat Client",
            "Initialising Embedding model",
            "Load pretrained SentenceTransformer",
            "prompts are loaded"
        ]
        sensitive_paths = [
            "/sentence_transformers/SentenceTransformer.py",
            "/chatlse/clients.py",
            "/chatlse/postgres_engine.py"
        ]

        if any(keyword in record.getMessage() for keyword in sensitive_keywords):
            return False

        if any(sensitive_path in record.pathname for sensitive_path in sensitive_paths):
            return False

        # If none of the above conditions are met, allow the log
        return True    
# create handlers 

# stream_handler = logging.StreamHandler(sys.stdout)
file_handler = logging.FileHandler('app.log')
better_stack_handler = LogtailHandler(source_token = token)

# set formatters
# stream_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

# add handlers to the logger
logger.handlers = [file_handler, better_stack_handler]

# set log-level

logger.setLevel(logging.INFO)
exclude_warnings_filter = ExcludeWarningsAndHTTPFilter()
logger.addFilter(exclude_warnings_filter)

# ensuring that exclude_warnings_filter runs on all three handlers
# stream_handler.addFilter(exclude_warnings_filter)
file_handler.addFilter(exclude_warnings_filter)
better_stack_handler.addFilter(exclude_warnings_filter)