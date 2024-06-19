# Querying phi3/llama3 using openai API 

"""from openai import OpenAI

client = OpenAI(
    base_url = 'http://localhost:11434/v1',
    api_key='ollama', # required, but unused
)

response = client.chat.completions.create(
  model="phi3",
  messages=[
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Who won the world series in 2020?"},
    {"role": "assistant", "content": "The LA Dodgers won in 2020."},
    {"role": "user", "content": "Where was it played?"}
  ]
)
print(response.choices[0].message.content)"""

###############################################################

# Embedding with ollama using llama3

"""import ollama 

embeddings = ollama.embeddings(
    model="llama3:instruct", 
    prompt="test test 123"
)

print(len(embeddings["embedding"]))"""

###############################################################

# Embedding with llama_index using llama3

"""from llama_index.embeddings.ollama import OllamaEmbedding

ollama_embedding = OllamaEmbedding(model_name="llama3:instruct", base_url="http://localhost:11434", ollama_additional_kwargs={"mirostat": 0}) 

query_embedding = ollama_embedding.get_query_embedding("test")

print(query_embedding)"""

###############################################################

# Embedding with llama-index using hugging face sentence transformers (gte-large)

"""from llama_index.embeddings.huggingface import HuggingFaceEmbedding 

embed_model = HuggingFaceEmbedding(model_name="thenlper/gte-large") 

embeddings = embed_model.get_text_embedding("Hello World!") 
print(len(embeddings))
print(embeddings)"""

