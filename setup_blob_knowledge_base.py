import os
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    AzureBlobKnowledgeSource,
    AzureBlobKnowledgeSourceParameters,
    KnowledgeBase,
    KnowledgeBaseAzureOpenAIModel,
    AzureOpenAIVectorizerParameters,
    KnowledgeSourceReference,
    
)
from azure.search.documents.knowledgebases.models import (
    KnowledgeSourceIngestionParameters,
    KnowledgeSourceAzureOpenAIVectorizer,
)

load_dotenv()
search_endpoint = os.environ["AZURE_SEARCH_ENDPOINT"]
aoai_endpoint = os.environ["AZURE_OPENAI_ENDPOINT"]
storage_url = os.environ["AZURE_STORAGE_ACCOUNT_URL"]
container = os.environ["AZURE_STORAGE_CONTAINER"]

credential = DefaultAzureCredential()
client = SearchIndexClient(endpoint=search_endpoint, credential=credential)

# 1. Blob knowledge source — Azure AUTO-CREATES the index, chunker, embedder, and indexer
ks = AzureBlobKnowledgeSource(
    name="my-blob-source",
    description="User-uploaded documents.",
    blob_parameters=AzureBlobKnowledgeSourceParameters(
        connection_string=f"ResourceId=/subscriptions/6479bfe7-7d60-427b-8d6c-656f0c664fcd/resourceGroups/learn-ai-search/providers/Microsoft.Storage/storageAccounts/strgaisearch;",
        container_name=container,
        # Tell it which embedding model to use for auto-embedding
        embedding_model={
            "resource_url": aoai_endpoint,
            "deployment_name": "text-embedding-3-large",
            "model_name": "text-embedding-3-large",
        },
    ),
)
client.create_or_update_knowledge_source(knowledge_source=ks)
print("Blob knowledge source created!")

# 2. Knowledge base on top of it
# Embedding model config (for vectorizing text chunks)
embedding_params = AzureOpenAIVectorizerParameters(
    resource_url=aoai_endpoint,
    deployment_name="text-embedding-3-large",   # ← your embedding deployment name
    model_name="text-embedding-3-large",         # ← the underlying model
)

# Chat/LLM model config (for image verbalization, etc.)
chat_params = AzureOpenAIVectorizerParameters(
    resource_url=aoai_endpoint,
    deployment_name="gpt-4.1-mini",
    model_name="gpt-4.1-mini",
)

# Wrap them into ingestion parameters
ingestion_params = KnowledgeSourceIngestionParameters(
    identity=None,   # None = use the search service's system-assigned managed identity
    disable_image_verbalization=False,
    chat_completion_model=KnowledgeBaseAzureOpenAIModel(
        azure_open_ai_parameters=chat_params,
    ),
    embedding_model=KnowledgeSourceAzureOpenAIVectorizer(
        azure_open_ai_parameters=embedding_params,
    ),
)

# 1. Blob knowledge source
ks = AzureBlobKnowledgeSource(
    name="my-blob-source",
    description="User-uploaded documents.",
    azure_blob_parameters=AzureBlobKnowledgeSourceParameters(
        connection_string=f"ResourceId=/subscriptions/6479bfe7-7d60-427b-8d6c-656f0c664fcd/resourceGroups/learn-ai-search/providers/Microsoft.Storage/storageAccounts/strgaisearch;",
        container_name=container,
        folder_path=None,
        is_adls_gen2=False,
        ingestion_parameters=ingestion_params,   # ← models go through here
    ),
)