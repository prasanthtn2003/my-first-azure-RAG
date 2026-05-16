# Document Q&A with Azure AI Search

A web application that lets users upload documents and ask natural-language questions about them. Built with Flask, Azure AI Search (agentic retrieval), Azure Blob Storage, and Azure OpenAI.

## How it works

User uploads a document → Flask stores it in Azure Blob Storage → Azure AI Search automatically indexes it → User asks a question → The knowledge base retrieves relevant chunks → Azure OpenAI synthesizes a clean answer.

## Tech stack

- Python 3.12
- Flask (web framework)
- Azure AI Search (preview SDK with agentic retrieval)
- Azure Blob Storage
- Azure OpenAI (text-embedding-3-large for embeddings, gpt-4.1 for synthesis)
- DefaultAzureCredential for keyless authentication

## Project structure

- app.py — Flask web server with upload and ask endpoints
- setup.py — One-time setup that creates the knowledge source and knowledge base in Azure
- cleanup.py — Deletes the knowledge source and base, useful for resets
- requirements.txt — Python dependencies
- templates/index.html — Web UI for upload and Q&A
- .env.example — Template for required environment variables

## Prerequisites

1. An Azure subscription
2. An Azure AI Search service (Basic tier or higher)
3. An Azure Storage account with a container for uploaded documents
4. A Microsoft Foundry project with two model deployments: text-embedding-3-large and gpt-4.1
5. Python 3.10 or newer
6. Azure CLI installed, signed in with `az login`

## Role assignments

For the app to work with keyless authentication, the following Azure RBAC roles must be assigned.

On the AI Search service — assign to your user account:
- Search Service Contributor
- Search Index Data Contributor
- Search Index Data Reader

On the Storage account — assign to your user account:
- Storage Blob Data Contributor

On the Storage account — assign to the AI Search service's managed identity:
- Storage Blob Data Reader

On the Azure OpenAI resource — assign to the AI Search service's managed identity:
- Cognitive Services OpenAI User

## Setup

1. Clone the repo:

       git clone https://github.com/prasanthtn2003/my-first-azure-RAG.git
       cd my-first-azure-RAG

2. Create a virtual environment and install dependencies:

       python -m venv .venv
       .venv\Scripts\activate
       pip install -r requirements.txt

3. Copy .env.example to .env and fill in your values.

4. Run the one-time setup to create the knowledge source and knowledge base in Azure:

       python setup.py

5. Start the app:

       python app.py

6. Open http://127.0.0.1:5000 in your browser.

## Usage

1. Click Choose File, pick a PDF or text document, click Upload.
2. Wait a couple of minutes for Azure to index the document. You can watch progress in the Azure portal under your AI Search service → Indexers.
3. Type a question in the Ask section and click Ask.
4. The synthesized answer appears below.

## Key concepts

This project demonstrates several Azure AI Search concepts.

Knowledge source — a labeled, reusable pointer to where content lives. It does not hold content itself; it tells AI Search where to find it and how to index it.

Knowledge base — the orchestrator that combines one or more knowledge sources with an LLM. When a user asks a question, the knowledge base uses the LLM to plan the search, runs retrieval against the knowledge sources, and returns relevant chunks.

Agentic retrieval — instead of running the question as a single search query, the LLM decomposes the question into multiple focused subqueries, runs them in parallel, semantically re-ranks the results, and merges them into a unified response.

Managed identity authentication — the app uses DefaultAzureCredential, which picks up the current az login session. The AI Search service uses its own system-assigned managed identity to call Blob Storage and Azure OpenAI. No API keys appear anywhere in the code.

## What I learned building this

- How Azure AI Search's agentic retrieval decomposes complex questions into parallel subqueries and re-ranks results.
- Why knowledge sources and knowledge bases are separate concepts: knowledge sources are reusable pointers, knowledge bases are active orchestrators.
- How to set up keyless authentication using managed identities and DefaultAzureCredential, avoiding API keys in code.
- The difference between Azure OpenAI deployment names (the label you choose) and model names (the model family). Both are required in the knowledge base configuration.
- That a knowledge source's embedding model is immutable after creation — changing it requires deleting and recreating the source.
- How to debug Azure permission errors: Forbidden errors trace back to missing RBAC role assignments, not code bugs.

## Roadmap

- Show citations (which document and page each answer came from)
- Multi-turn chat with conversation memory
- Delete uploaded files from the UI
- Deploy to Azure App Service
- Add authentication with Microsoft Entra ID

## License

MIT
