import fastapi

from .api_models import ChatRequest
from .globals import global_storage
from .postgres_searcher import PostgresSearcher
from .logger import logger # Ensure logger is imported here
from .clients import create_chat_model
from dotenv import load_dotenv
import random


from .rag_advanced import AdvancedRAGChatLlama, AdvancedRAGChatMistral, AdvancedRAGChatLlamaSummariser, AdvancedRAGChatMistralSummariser



BACKENDS = {
    "llama31_without_summariser": AdvancedRAGChatLlama,
    "mistral_without_summariser": AdvancedRAGChatMistral,
    "llama31_summariser": AdvancedRAGChatLlamaSummariser,
    "mistral_summariser": AdvancedRAGChatMistralSummariser
}

CHATMODELS = {
    "llama31": "llama3.1:8b-instruct-q8_0",
    "mistral": "mistral-nemo:12b-instruct-2407-q6_K"
}

model_list = ["llama31", "mistral"]

choices = [
    ("llama31_summariser", "llama31"),
    ("llama31_without_summariser", "llama31"),
    ("mistral_summariser", "mistral"),
    ("mistral_without_summariser", "mistral")
]


# Global variables to store the selected backend and chat model
selected_backend = None
selected_chatmodel = None

def randomize_selection():
    global selected_backend, selected_chatmodel
    selected_choice = random.choice(choices)
    selected_backend, selected_chatmodel = selected_choice
    print(f"Selected Backend: {selected_backend}")
    print(f"Selected Chat Model: {selected_chatmodel}")

# Perform the random selection when the application starts
randomize_selection()

router = fastapi.APIRouter()

@router.post("/chat")
async def chat_handler(chat_request: ChatRequest, backend = BACKENDS[selected_backend], chatmodel = CHATMODELS[selected_chatmodel]):
    load_dotenv(override=True)

    logger.info(f"Selected Backend: {backend}")
    logger.info(f"Selected Chat Model: {chatmodel}")

    ChatClass = backend
    if not ChatClass:
        raise ValueError(f"Invalid backend: {backend}")
    
    ragchat = ChatClass(
        searcher=PostgresSearcher(global_storage.engine),
        chat_client=global_storage.chat_client,
        chat_model= await create_chat_model(chatmodel),
        #chat_model=global_storage.chat_model,
        chat_deployment=global_storage.chat_deployment,
        embed_client=global_storage.embed_client,
        embed_deployment=global_storage.embed_deployment,
        embed_model=global_storage.embed_model,
        embed_dimensions=global_storage.embed_dimensions,
        context_window_override=global_storage.context_window_override
    )

    messages = [message.model_dump() for message in chat_request.messages]
    logger.info(f"Received messages: {messages[0]['content']}")
    
    overrides = chat_request.context.get("overrides", {})
    logger.info(f"Overrides: {overrides}")

    response = await ragchat.run(messages, overrides=overrides)
    logger.info(f"Response: {response['choices'][0]['message']['content']}")

    return response
