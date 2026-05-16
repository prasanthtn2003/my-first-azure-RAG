import os
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.search.documents.indexes import SearchIndexClient

load_dotenv()
credential = DefaultAzureCredential()
client = SearchIndexClient(endpoint=os.environ["AZURE_SEARCH_ENDPOINT"], credential=credential)

# Order matters: delete the base first (it references the source)
try:
    client.delete_knowledge_base("my-knowledge-base")
    print("Knowledge base deleted.")
except Exception as e:
    print(f"Knowledge base delete: {e}")

try:
    client.delete_knowledge_source("my-blob-source")
    print("Knowledge source deleted.")
except Exception as e:
    print(f"Knowledge source delete: {e}")

print("Cleanup complete.")