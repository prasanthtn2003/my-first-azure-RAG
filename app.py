import os
import json
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from azure.storage.blob import BlobServiceClient
from azure.search.documents.knowledgebases import KnowledgeBaseRetrievalClient
from azure.search.documents.knowledgebases.models import (
    KnowledgeBaseRetrievalRequest,
    KnowledgeRetrievalSemanticIntent,
)
from openai import AzureOpenAI

load_dotenv()
app = Flask(__name__)
credential = DefaultAzureCredential()

container_client = BlobServiceClient(
    account_url=os.environ["AZURE_STORAGE_ACCOUNT_URL"],
    credential=credential,
).get_container_client(os.environ["AZURE_STORAGE_CONTAINER"])

kb_client = KnowledgeBaseRetrievalClient(
    endpoint=os.environ["AZURE_SEARCH_ENDPOINT"],
    knowledge_base_name="my-knowledge-base",
    credential=credential,
)

token_provider = get_bearer_token_provider(credential, "https://cognitiveservices.azure.com/.default")
aoai = AzureOpenAI(
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    azure_ad_token_provider=token_provider,
    api_version="2024-10-21",
)


@app.route("/")
def home():
    try:
        files = [b.name for b in container_client.list_blobs()]
    except Exception as e:
        print(f"Error listing blobs: {e}")
        files = []
    return render_template("index.html", files=files)


@app.route("/upload", methods=["POST"])
def upload():
    file = request.files.get("file")
    if not file or not file.filename:
        return jsonify({"error": "No file selected"}), 400

    try:
        container_client.get_blob_client(file.filename).upload_blob(
            file.stream, overwrite=True
        )
    except Exception as e:
        return jsonify({"error": f"Upload failed: {str(e)}"}), 500

    return jsonify({
        "message": f"Uploaded {file.filename}. Azure will index it within a few minutes."
    })


@app.route("/ask", methods=["POST"])
def ask():
    question = (request.get_json() or {}).get("question", "").strip()
    if not question:
        return jsonify({"error": "No question"}), 400

    # Step 1: Get relevant content from the knowledge base
    try:
        response = kb_client.retrieve(
            KnowledgeBaseRetrievalRequest(
                intents=[KnowledgeRetrievalSemanticIntent(search=question)],
                include_activity=True,
            )
        )
    except Exception as e:
        print(f"Azure retrieve error: {e}")
        return jsonify({"error": f"Azure error: {str(e)}"}), 500

    # Step 2: Extract text chunks from the response
    chunks = []
    for item in (response.response or []):
        content = getattr(item, "content", None)
        if not content:
            continue
        if isinstance(content, list):
            for c in content:
                text = getattr(c, "text", None) if not isinstance(c, str) else c
                if not text:
                    continue
                try:
                    parsed = json.loads(text)
                    if isinstance(parsed, list):
                        for chunk in parsed:
                            if isinstance(chunk, dict) and "content" in chunk:
                                chunks.append(chunk["content"])
                    else:
                        chunks.append(text)
                except (json.JSONDecodeError, TypeError):
                    chunks.append(text)

    if not chunks:
        return jsonify({"answer": "No relevant content found."})

    # Step 3: Send the chunks + question to gpt-4.1 for a clean answer
    context = "\n\n---\n\n".join(chunks[:5])
    try:
        completion = aoai.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant. Answer the user's question using only the provided context. If the context does not contain the answer, say so."
                },
                {
                    "role": "user",
                    "content": f"Context:\n{context}\n\nQuestion: {question}"
                },
            ],
        )
        answer = completion.choices[0].message.content
    except Exception as e:
        print(f"OpenAI error: {e}")
        return jsonify({"error": f"OpenAI error: {str(e)}"}), 500

    return jsonify({"answer": answer})


if __name__ == "__main__":
    app.run(debug=True, port=5000)