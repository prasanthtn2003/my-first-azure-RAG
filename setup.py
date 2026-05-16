# setup.py — run once
import os
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    AzureBlobKnowledgeSource, AzureBlobKnowledgeSourceParameters,
    AzureOpenAIVectorizerParameters, KnowledgeBase,
    KnowledgeBaseAzureOpenAIModel, KnowledgeSourceReference,
)
from azure.search.documents.knowledgebases.models import (
    KnowledgeSourceIngestionParameters, KnowledgeSourceAzureOpenAIVectorizer,
)

load_dotenv()
credential = DefaultAzureCredential()
client = SearchIndexClient(endpoint=os.environ["AZURE_SEARCH_ENDPOINT"], credential=credential)

resource_id = (
    f"/subscriptions/{os.environ['AZURE_SUBSCRIPTION_ID']}"
    f"/resourceGroups/{os.environ['AZURE_RESOURCE_GROUP']}"
    f"/providers/Microsoft.Storage/storageAccounts/{os.environ['AZURE_STORAGE_ACCOUNT_NAME']}"
)

client.create_or_update_knowledge_source(
    AzureBlobKnowledgeSource(
        name="my-blob-source",
        description="User-uploaded documents.",
        azure_blob_parameters=AzureBlobKnowledgeSourceParameters(
            connection_string=f"ResourceId={resource_id};",
            container_name=os.environ["AZURE_STORAGE_CONTAINER"],
            ingestion_parameters=KnowledgeSourceIngestionParameters(
                embedding_model=KnowledgeSourceAzureOpenAIVectorizer(
                    azure_open_ai_parameters=AzureOpenAIVectorizerParameters(
                        resource_url=os.environ["AZURE_OPENAI_ENDPOINT"],
                        deployment_name="text-embedding-3-large",
                        model_name="text-embedding-3-large",
                    ),
                ),
            ),
        ),
    )
)
print("Knowledge source ready.")

client.create_or_update_knowledge_base(
    KnowledgeBase(
        name="my-knowledge-base",
        knowledge_sources=[KnowledgeSourceReference(name="my-blob-source")],
        models=[KnowledgeBaseAzureOpenAIModel(
            azure_open_ai_parameters=AzureOpenAIVectorizerParameters(
                resource_url=os.environ["AZURE_OPENAI_ENDPOINT"],
                deployment_name="gpt-4.1",
                model_name="gpt-4.1",
            ),
        )],
    )
)
print("Knowledge base ready.")