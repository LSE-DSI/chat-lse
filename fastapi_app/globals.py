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
        self.rag_results = []


global_storage = Global()
