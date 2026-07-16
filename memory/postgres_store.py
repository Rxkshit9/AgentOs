import datetime
import json
from typing import List, Optional, Tuple, Dict, Any, Union, Literal, Iterable
from sqlalchemy import (
    create_engine, Column, Integer, String, Text, DateTime, JSON,
    select, delete, insert, update
)
from sqlalchemy.orm import declarative_base, sessionmaker
from pgvector.sqlalchemy import Vector
from langgraph.store.base import BaseStore, Item, Op, GetOp, PutOp, SearchOp, ListNamespacesOp

from config.memory import DATABASE_URL, EMBEDDING_DIM, get_embeddings

Base = declarative_base()

class DocumentModel(Base):
    """Database model for semantic knowledge base documents."""
    __tablename__ = "knowledge_documents"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    embedding = Column(Vector(EMBEDDING_DIM), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class MemoryStoreItemModel(Base):
    """Database model for LangGraph long-term memories."""
    __tablename__ = "long_term_memories"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    namespace_path = Column(String(512), nullable=False, index=True)
    key = Column(String(255), nullable=False, index=True)
    value = Column(JSON, nullable=False)
    embedding = Column(Vector(EMBEDDING_DIM), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

# Engine and Session initialization
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Initializes tables in the PostgreSQL database, enabling the vector extension."""
    with engine.begin() as conn:
        # Create pgvector extension if not exists
        conn.execute(select(1))  # Just connection check
        from sqlalchemy import text
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
    Base.metadata.create_all(bind=engine)

class PostgresStore(BaseStore):
    """PostgreSQL-backed implementation of LangGraph BaseStore using pgvector."""
    
    def __init__(self):
        super().__init__()
        self.embeddings = get_embeddings()
        init_db()

    def _namespace_to_path(self, namespace: Tuple[str, ...]) -> str:
        return "/".join(namespace)

    def _path_to_namespace(self, path: str) -> Tuple[str, ...]:
        return tuple(path.split("/"))

    def get(self, namespace: Tuple[str, ...], key: str) -> Optional[Item]:
        """Retrieves a single memory item by namespace and key."""
        ns_path = self._namespace_to_path(namespace)
        with SessionLocal() as session:
            stmt = select(MemoryStoreItemModel).where(
                MemoryStoreItemModel.namespace_path == ns_path,
                MemoryStoreItemModel.key == key
            )
            res = session.execute(stmt).scalar_one_or_none()
            if not res:
                return None
            return Item(
                namespace=self._path_to_namespace(res.namespace_path),
                key=res.key,
                value=res.value,
                created_at=res.created_at,
                updated_at=res.updated_at
            )

    def put(
        self,
        namespace: Tuple[str, ...],
        key: str,
        value: Dict[str, Any],
        index: Optional[Union[Literal[False], List[str]]] = None
    ) -> None:
        """Stores or updates a memory item by namespace and key, generating vectors."""
        ns_path = self._namespace_to_path(namespace)
        # Embed the value content (convert dict to string representation for embedding)
        content_to_embed = json.dumps(value)
        embedding_vector = self.embeddings.embed_query(content_to_embed)
        
        with SessionLocal() as session:
            # Check if exists
            stmt = select(MemoryStoreItemModel).where(
                MemoryStoreItemModel.namespace_path == ns_path,
                MemoryStoreItemModel.key == key
            )
            existing = session.execute(stmt).scalar_one_or_none()
            
            if existing:
                existing.value = value
                existing.embedding = embedding_vector
                existing.updated_at = datetime.datetime.utcnow()
            else:
                new_item = MemoryStoreItemModel(
                    namespace_path=ns_path,
                    key=key,
                    value=value,
                    embedding=embedding_vector
                )
                session.add(new_item)
            session.commit()

    def delete(self, namespace: Tuple[str, ...], key: str) -> None:
        """Deletes a memory item."""
        ns_path = self._namespace_to_path(namespace)
        with SessionLocal() as session:
            stmt = delete(MemoryStoreItemModel).where(
                MemoryStoreItemModel.namespace_path == ns_path,
                MemoryStoreItemModel.key == key
            )
            session.execute(stmt)
            session.commit()

    def search(
        self,
        namespace_prefix: Tuple[str, ...],
        *,
        query: Optional[str] = None,
        limit: int = 10,
        offset: int = 0
    ) -> List[Item]:
        """Searches memory items under a namespace prefix, ordering by similarity if queried."""
        prefix_path = self._namespace_to_path(namespace_prefix)
        with SessionLocal() as session:
            stmt = select(MemoryStoreItemModel)
            
            # Namespace prefix filter
            if prefix_path:
                stmt = stmt.where(MemoryStoreItemModel.namespace_path.like(f"{prefix_path}%"))
            
            # Vector search query filter
            if query:
                query_vector = self.embeddings.embed_query(query)
                stmt = stmt.order_by(MemoryStoreItemModel.embedding.cosine_distance(query_vector))
            else:
                stmt = stmt.order_by(MemoryStoreItemModel.updated_at.desc())
                
            stmt = stmt.limit(limit).offset(offset)
            results = session.execute(stmt).scalars().all()
            
            return [
                Item(
                    namespace=self._path_to_namespace(res.namespace_path),
                    key=res.key,
                    value=res.value,
                    created_at=res.created_at,
                    updated_at=res.updated_at
                )
                for res in results
            ]

    # Async implementations wrapping the sync calls (compliant with BaseStore API)
    async def aget(self, namespace: Tuple[str, ...], key: str) -> Optional[Item]:
        return self.get(namespace, key)

    async def aput(
        self,
        namespace: Tuple[str, ...],
        key: str,
        value: Dict[str, Any],
        index: Optional[Union[Literal[False], List[str]]] = None
    ) -> None:
        self.put(namespace, key, value, index)

    async def adelete(self, namespace: Tuple[str, ...], key: str) -> None:
        self.delete(namespace, key)

    async def asearch(
        self,
        namespace_prefix: Tuple[str, ...],
        *,
        query: Optional[str] = None,
        limit: int = 10,
        offset: int = 0
    ) -> List[Item]:
        return self.search(namespace_prefix, query=query, limit=limit, offset=offset)

    def batch(self, ops: Iterable[Op]) -> list[Any]:
        """Executes a batch of operations in order and returns their results."""
        results = []
        for op in ops:
            if isinstance(op, GetOp):
                results.append(self.get(op.namespace, op.key))
            elif isinstance(op, PutOp):
                if op.value is None:
                    self.delete(op.namespace, op.key)
                else:
                    self.put(op.namespace, op.key, op.value, index=op.index)
                results.append(None)
            elif isinstance(op, SearchOp):
                results.append(self.search(
                    op.namespace_prefix,
                    query=op.query,
                    limit=op.limit,
                    offset=op.offset
                ))
            elif isinstance(op, ListNamespacesOp):
                results.append([])
            else:
                results.append(None)
        return results

    async def abatch(self, ops: Iterable[Op]) -> list[Any]:
        """Asynchronously executes a batch of operations."""
        return self.batch(ops)
