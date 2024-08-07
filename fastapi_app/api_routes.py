import random
import fastapi

from .api_models import ChatRequest
from .globals import global_storage
from .postgres_searcher import PostgresSearcher
from .logger import logger # Ensure logger is imported here
from dotenv import load_dotenv

from .rag_advanced import AdvancedRAGChat


model_list = ["llama3.1:8b-instruct-q8_0", "mistral-nemo:12b-instruct-2407-q6_K"]

#selected_chat_model = random.choice(model_list)
selected_chat_model = "mistral-nemo:12b-instruct-2407-q6_K"
selected_summariser = random.choice([True, False])

router = fastapi.APIRouter()

@router.post("/chat")
async def chat_handler(chat_request: ChatRequest, chat_model=selected_chat_model, to_summarise=selected_summariser):
    #logger.info(f"Selected Chat Model: {chat_model}")
    #logger.info(f"Summariser: {to_summarise}")
    
    ragchat = AdvancedRAGChat(
        searcher=PostgresSearcher(global_storage.engine),
        chat_client=global_storage.chat_client,
        chat_model=chat_model,
        #chat_model=global_storage.chat_model,
        embed_model=global_storage.embed_model,
        embed_dimensions=global_storage.embed_dimensions,
        context_window_override=global_storage.context_window_override, 
        to_summarise=to_summarise
    )

    messages = [message.model_dump() for message in chat_request.messages]
    logger.info(f"Received messages: {messages[0]['content']}")
    
    user_info = chat_request.context.get("userInfo", {})
    logger.info(f"User Information: {user_info}")

    overrides = chat_request.context.get("overrides", {})
    logger.info(f"Overrides: {overrides}")

    response = await ragchat.run(messages, user_info=user_info, overrides=overrides)
    logger.info(f"Response: {response['choices'][0]['message']['content']}")

    return response
