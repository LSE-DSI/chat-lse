class Global:
    def __init__(self):
        self.engine = None
        self.chat_client = None
        self.embed_client = None
        self.chat_model = None
        self.embed_model = None
        self.embed_dimensions = None
        self.chat_deployment = None
        self.embed_deployment = None
        self.context_window_override = None 
        self.to_summarise = None
        self.rag_results = []
        self.user_context = None
        self.requires_clarification = None
        self.chat_class = None 
        self.message_history = []


global_storage = Global()
