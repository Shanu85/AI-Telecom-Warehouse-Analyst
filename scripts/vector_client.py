import os
import chromadb
import uuid
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sentence_transformers import SentenceTransformer
import logging

logger = logging.getLogger(__name__)

class VectorStore:
    def __init__(self,collection_name:str="sql_queries",persist_dir:str="data/vector_store"):
        '''Initialise Vector store
        arg:
            collection_name : name of ChromaDB collection
            persist_dir : directory to persist vector store
        '''
        self.collection_name=collection_name
        self.persist_dir=persist_dir
        self.vector_client=None
        self.collection=None
        self.embedding_model=None
        self._initialise_store()

    def _initialise_store(self):
        """Initialse Chroma client and collections"""
        try:
            # create persistent chromaDB client
            os.makedirs(self.persist_dir,exist_ok=True)
            self.vector_client=chromadb.PersistentClient(path=self.persist_dir)

            # get or create collection
            self.collection=self.vector_client.get_or_create_collection(name=self.collection_name,metadata={'description': 'NL2SQL RAG memory store'})

            print("⏳ Loading embedding model...")
            self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

            print(f'Vector store initialised : Collection - {self.collection_name}')

            print(f"Model loaded successfully. Model dimensions are {self.embedding_model.get_sentence_embedding_dimension()}")
            print(f'Existing document in collection : {self.collection.count()}')

        except Exception as e:
            print(f"Error initialising chromaDB store {e}")
            raise
    
    def _generate_embeddings(self,texts: list[str]) -> list:
        """
        Embed a list of strings. Returns list of vectors.
        """
        try:
            embeddings = self.embedding_model.encode(texts, show_progress_bar=False)
            return embeddings.tolist()  # ✅ numpy → list, not .to_list()
        except Exception as e:
            print(f"❌ Embedding error: {e}")
            raise


    def add_documents(self,documents):
        """
        Store a successful (question → SQL → answer) triple.
        Embeds the USER QUESTION (not SQL) for similarity search at retrieval time.

        Args:
            documents: {
                'user_question': str,
                'sql_generated': str,
                'table_used': list[str],
                'answer': str
            }
        """

        sql=documents['sql_generated']
        user_question=documents['user_question']
        answer = documents['answer'] # llm generated response
        tables=documents['table_used']

        # FIX: Deduplication — don't store if an exact match already exists
        # if user asked the same question don't store that question again in vector store
        existing = self.get_similar_examples(user_question, top_k=1)
        if existing and existing[0]['question'].strip().lower() == user_question.strip().lower():
            logger.info(f"⏭️ Duplicate question skipped: '{user_question}'")
            return

        # Embed the QUESTION (at query time we search by question similarity)
        embeddings = self._generate_embeddings([user_question])

        # ChromaDB metadata must be flat dict with str/int/float values only
        metadata = [{
            'user_question': user_question,
            'sql_generated': sql,
            'tables_used': ", ".join(tables) if isinstance(tables, list) else tables
        }]

        try:
            self.collection.add(
                ids=[str(uuid.uuid4())],   # unique ID required
                embeddings=embeddings,      # vector of the question
                documents=[answer],         # natural language answer stored as document
                metadatas=metadata          # list of dicts, not plain dict
            )
            print(f"✅ Saved to vector store | Total docs: {self.collection.count()}")

        except Exception as e:
            print(f"❌ Error adding to vector store: {e}")
            raise
    

    def get_similar_examples(self,user_question:str,top_k:int=3)->list[dict]:
        """
        Find the most similar past questions and return their SQL.
        This is what gets injected into the LLM prompt as few-shot examples.

        Returns: [{'question': ..., 'sql': ..., 'tables': ...}, ...]
        """

        total = self.collection.count()
        if total == 0:
            return []  # nothing stored yet
        
        query_embedding = self._generate_embeddings([user_question])

        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=min(top_k, total),      # ✅ can't request more than exists
            include=["metadatas", "documents", "distances"]
        )

        examples = []
        for meta, doc, dist in zip(
            results["metadatas"][0],
            results["documents"][0],
            results["distances"][0]
        ):
            # ✅ filter out low-quality matches (cosine distance > 0.5 = too dissimilar)
            if dist < 0.5:
                examples.append({
                    "question": meta["user_question"],
                    "sql":      meta["sql_generated"],
                    "tables":   meta["tables_used"],
                    "answer":   doc
                })

        return examples


        
