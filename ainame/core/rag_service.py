import os

try:
    from langchain_chroma import Chroma
    from langchain_community.document_loaders import PyPDFLoader, TextLoader
    from langchain_ollama import OllamaEmbeddings
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError as e:
    Chroma = None
    PyPDFLoader = None
    TextLoader = None
    OllamaEmbeddings = None
    RecursiveCharacterTextSplitter = None
    RAG_IMPORT_ERROR = e
else:
    RAG_IMPORT_ERROR = None


embedding_model = OllamaEmbeddings(model="nomic-embed-text") if OllamaEmbeddings else None
DB_PATH = "./chroma_rag_db"
RAG_EMPTY_KNOWLEDGE_MESSAGE = "用户尚未上传企业知识库，请根据用户当前输入和行业常识完成命名。"
RAG_NO_RESULT_MESSAGE = "用户已上传企业知识库，但本次未检索到相关内容，请根据用户当前输入和行业常识完成命名。"
RAG_UNAVAILABLE_MESSAGE = "知识库检索服务暂时不可用，请根据用户当前输入和行业常识完成命名。"
RAG_SKIPPED_MESSAGE = "用户未提供可用于检索知识库的需求，已跳过知识库检索。"
RAG_MAX_DOC_CHARS = 900
RAG_MAX_TOTAL_CHARS = 1800


def process_and_stor_file(file_path, user_id):
    """Parse an uploaded TXT/PDF file and store it in the user's vector DB."""
    if RAG_IMPORT_ERROR:
        raise RuntimeError(f"RAG dependencies are unavailable: {RAG_IMPORT_ERROR}")

    if file_path.endswith(".pdf"):
        doc = PyPDFLoader(file_path).load()
    elif file_path.endswith(".txt"):
        doc = TextLoader(file_path, encoding="utf-8").load()
    else:
        print("不支持的文件格式")
        return

    doc_spliter = RecursiveCharacterTextSplitter(
        chunk_size=300,
        chunk_overlap=50,
        add_start_index=True,
    )
    all_docs = doc_spliter.split_documents(doc)

    collection_name = f"user_{user_id}_docs"
    my_company_collection = Chroma(
        collection_name=collection_name,
        embedding_function=embedding_model,
        persist_directory=DB_PATH,
    )

    my_company_collection.add_documents(all_docs)


def _collection_exists(collection_name):
    if RAG_IMPORT_ERROR:
        print(f"[RAG 检索降级] RAG 依赖不可用: {RAG_IMPORT_ERROR}")
        return None

    if not os.path.exists(DB_PATH):
        return False

    try:
        import chromadb

        client = chromadb.PersistentClient(path=DB_PATH)
        collections = client.list_collections()
    except Exception as e:
        print(f"[RAG 检索降级] 无法读取 Chroma collection 列表: {e}")
        return None

    for collection in collections:
        name = collection if isinstance(collection, str) else getattr(collection, "name", None)
        if name == collection_name:
            return True
    return False


def retrive_user_from_knowledge(user_id, search_query):
    """Retrieve the current user's private knowledge with a safe fallback."""
    if not search_query:
        return RAG_SKIPPED_MESSAGE

    if RAG_IMPORT_ERROR:
        print(f"[RAG 检索降级] RAG 依赖不可用: {RAG_IMPORT_ERROR}")
        return RAG_UNAVAILABLE_MESSAGE

    collection_name = f"user_{user_id}_docs"
    collection_exists = _collection_exists(collection_name)
    if collection_exists is False:
        return RAG_EMPTY_KNOWLEDGE_MESSAGE
    if collection_exists is None:
        return RAG_UNAVAILABLE_MESSAGE

    try:
        my_company_collection = Chroma(
            collection_name=collection_name,
            embedding_function=embedding_model,
            persist_directory=DB_PATH,
        )
        result_docs = my_company_collection.similarity_search(search_query, k=2)
    except Exception as e:
        print(f"[RAG 检索降级] 用户 {user_id} 知识库检索失败: {e}")
        return RAG_UNAVAILABLE_MESSAGE

    if not result_docs:
        return RAG_NO_RESULT_MESSAGE

    return _format_retrieved_context(user_id, result_docs)


def _format_retrieved_context(user_id, docs):
    """Format only the current user's retrieved snippets with length guards."""
    snippets = []
    total_chars = 0
    for index, doc in enumerate(docs, start=1):
        content = _normalize_doc_text(getattr(doc, "page_content", ""))
        if not content:
            continue
        content = _truncate_text(content, RAG_MAX_DOC_CHARS)
        remaining = RAG_MAX_TOTAL_CHARS - total_chars
        if remaining <= 0:
            break
        if len(content) > remaining:
            content = _truncate_text(content, remaining)
        total_chars += len(content)
        snippets.append(f"【用户专属参考资料 {index}】\n{content}")

    if not snippets:
        return RAG_NO_RESULT_MESSAGE

    header = (
        "【RAG 检索状态】已检索当前登录用户自己的企业知识库；"
        "以下内容已按相关性截取，超过长度的资料已摘要式截断。"
    )
    return "\n".join([header, *snippets])


def _normalize_doc_text(text):
    return " ".join(str(text).split())


def _truncate_text(text, max_chars):
    if len(text) <= max_chars:
        return text
    return f"{text[:max(0, max_chars - 20)]}...【内容过长已截断】"
