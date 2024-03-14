from typing import TYPE_CHECKING, Any, Dict, List, Optional

from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.retrievers import BaseRetriever
from langchain_core.documents import Document
from langchain_core.callbacks.manager import Callbacks

from langchain.tools import Tool

from langchain_community.vectorstores.milvus import Milvus

class RetrieverInput(BaseModel):
    """Input to the retriever."""
    query: str = Field(description="query to look up in retriever")

class retriever_tool:
    retriever: BaseRetriever = None
    milvus: Milvus = None

    def get_extend_documents(
            self,
            query: str,
            *,
            callbacks: Callbacks = None,
            tags: Optional[List[str]] = None,
            metadata: Optional[Dict[str, Any]] = None,
            run_name: Optional[str] = None,
            **kwargs: Any,
        ) -> List[Document]:
        docs: List[Document] = self.retriever.get_relevant_documents(query=query, callbacks=callbacks, tags=tags, metadata=metadata, run_name=run_name, kwargs=kwargs)
        if len(docs) > 0 and 'file_id' in docs[0].metadata:
            (domain_id, file_id, min_chunk_id, max_chunk_id) = self.get_opt_chunk(docs)
            texts = self.milvus.col.query(f"domain_id == {domain_id} && file_id == {file_id} && chunk_index >= {min_chunk_id} && chunk_index <= {max_chunk_id}", ['text'])
            page_content = ""
            for text in texts:
                page_content += text['text']
            docs[0].page_content = page_content
            print("page_content:" + page_content)
        return docs

    def get_opt_chunk(self, docs: List[Document]) -> tuple[int, int, int]:
        meta1st = docs[0].metadata
        metadatas = [doc.metadata for doc in docs]
        len_meta = len(metadatas)
        score = 0
        opt_i = 0
        for wi in range(5):
            calc_socre = 0
            min_chunk_id = meta1st['chunk_index'] - 5 + wi
            max_chunk_id = meta1st['chunk_index'] + wi
            for i in range(len_meta):
                meta = metadatas[i]
                if meta['file_id'] == meta1st['file_id'] and meta['chunk_index'] >= min_chunk_id and meta['chunk_index'] <= max_chunk_id:
                    calc_socre += pow(2, len_meta-(i+1))
            if calc_socre == score:
                if wi <= 3 or min_chunk_id < 0:
                    score = calc_socre
                    opt_i = wi
            elif calc_socre > score:
                score = calc_socre
                opt_i = wi
        return (meta1st['domain_id'], meta1st['file_id'], meta1st['chunk_index'] - 5 + opt_i, meta1st['chunk_index'] + opt_i)

    async def aget_extend_documents(
            self,
            query: str,
            *,
            callbacks: Callbacks = None,
            tags: Optional[List[str]] = None,
            metadata: Optional[Dict[str, Any]] = None,
            run_name: Optional[str] = None,
            **kwargs: Any,
        ) -> List[Document]:
        docs: List[Document] = await self.retriever.aget_relevant_documents(query=query, callbacks=callbacks, tags=tags, metadata=metadata, run_name=run_name, kwargs=kwargs)
        if len(docs) > 0 and 'file_id' in docs[0].metadata:
            (domain_id, file_id, min_chunk_id, max_chunk_id) = self.get_opt_chunk(docs)
            texts = self.milvus.col.query(f"domain_id == {domain_id} && file_id == {file_id} && chunk_index >= {min_chunk_id} && chunk_index <= {max_chunk_id}", ['text'])
            page_content = ""
            for text in texts:
                page_content += text['text']
            docs[0].page_content = page_content
            print("page_content:" + page_content)
        return docs

    def create_retriever_tool(
        self, milvus: Milvus, retriever: BaseRetriever, name: str, description: str
    ) -> Tool:
        self.retriever = retriever
        self.milvus = milvus

        return Tool(
            name=name,
            description=description,
            func=self.get_extend_documents,
            coroutine=self.aget_extend_documents,
            args_schema=RetrieverInput,
        )
