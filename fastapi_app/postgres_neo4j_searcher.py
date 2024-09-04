from pgvector.utils import to_db
from sqlalchemy import Float, Integer, String, select, text
from sqlalchemy.ext.asyncio import async_sessionmaker
from neo4j import GraphDatabase
from .postgres_models import Doc


class PostgresSearcher:
    def __init__(self, engine, neo4j_driver=None):
        # Initialize PostgreSQL session maker
        self.async_session_maker = async_sessionmaker(engine, expire_on_commit=False)
        # Initialize Neo4j driver
        self.neo4j_driver = neo4j_driver


    def enrich_query_with_graph(self, original_query: str, query_embedding):
        enriched_terms = set()
        with self.neo4j_driver.session() as neo4j_session:
            neo4j_query = f"""
            WITH {query_embedding} AS queryEmbedding
            MATCH (n)
            WHERE n.embedding IS NOT NULL
            WITH n, vector.similarity.cosine(n.embedding, queryEmbedding) AS similarity
            ORDER BY similarity DESC
            LIMIT 3
            
            WITH {query_embedding} AS queryEmbedding, n, similarity
            MATCH (n)-[r]->(relatedNode)
            WHERE relatedNode.embedding IS NOT NULL
            WITH n,
                n.name AS node_name, 
                n.doc_id AS doc_id, 
                similarity,
                relatedNode, 
                queryEmbedding,
                vector.similarity.cosine(relatedNode.embedding, queryEmbedding) AS related_similarity
            ORDER BY n, related_similarity DESC
            WITH n, node_name, doc_id, similarity, 
                collect(relatedNode.name)[0..3] AS top_related_names, 
                collect(relatedNode.doc_id)[0..3] AS top_related_doc_ids, 
                collect(related_similarity)[0..3] AS top_related_similarities

            UNWIND ([node_name] + top_related_names) AS name
            WITH name, 
                ([doc_id] + top_related_doc_ids) AS all_doc_ids, 
                ([similarity] + top_related_similarities) AS all_similarities

            UNWIND all_doc_ids AS doc_ids
            UNWIND all_similarities AS similarities

            RETURN DISTINCT name, doc_ids, similarities;
 """ 

            result = neo4j_session.run(neo4j_query, parameters={"query": original_query}).values()
            print(f"NEO4J RESULT: {result}")

            for record in result:
                if record[1] is not None:
                    enriched_terms.add(tuple(record[0:3]))  # Convert first three terms to a tuple and add to the set


                #enriched_terms.add(record[0:3]) if record[i] is not None
                #enriched_terms.update(record[1] if record[1] else [])
        return list(enriched_terms)
    

    def build_filter_clause(self, filters) -> tuple[str, str]:
        if filters is None:
            return "", ""
        filter_clauses = []
        for filter in filters:
            if isinstance(filter["value"], str):
                filter["value"] = f"'{filter['value']}'"
            filter_clauses.append(f"{filter['column']} {filter['comparison_operator']} {filter['value']}")
        filter_clause = " AND ".join(filter_clauses)
        if len(filter_clause) > 0:
            return f"WHERE {filter_clause}", f"AND {filter_clause}"
        return "", ""


    async def search(
        self,
        query_text: str | None,
        query_vector: list[float] | list,
        query_top: int = 5,
        filters: list[dict] | None = None,
        query_embedding: str | None = None,
        orignal_query: str | None = None 
    ):
        # Only use graph database when llm_generated_query is passed 
        if query_embedding: 
            # Enrich the query with graph-based terms
            enriched_terms = self.enrich_query_with_graph(orignal_query, query_embedding) if query_embedding else []
            #if enriched_terms:
            enriched_query_text = " OR ".join(enriched_terms)
            query_text = f"({query_text}) OR ({enriched_query_text})" if query_text else enriched_query_text
            #else:
                #enriched_query_text = query_text
        
            print(f"ENRICHED QUERY TEXT: {enriched_query_text}")

        filter_clause_where, filter_clause_and = self.build_filter_clause(filters)

        # SQL queries for vector, full-text, and hybrid search
        vector_query = f"""
            SELECT id, RANK () OVER (ORDER BY embedding <=> :embedding) AS rank
                FROM lse_doc
                {filter_clause_where}
                ORDER BY embedding <=> :embedding
                LIMIT 20
            """

        fulltext_query = f"""
            SELECT id, RANK () OVER (ORDER BY ts_rank_cd(to_tsvector('english', content), query) DESC)
                FROM lse_doc, plainto_tsquery('english', :query) query
                WHERE to_tsvector('english', content) @@ query {filter_clause_and}
                ORDER BY ts_rank_cd(to_tsvector('english', content), query) DESC
                LIMIT 20
            """

        hybrid_query = f"""
        WITH vector_search AS (
            {vector_query}
        ),
        fulltext_search AS (
            {fulltext_query}
        )
        SELECT
            COALESCE(vector_search.id, fulltext_search.id) AS id,
            COALESCE(1.0 / (:k + vector_search.rank), 0.0) +
            COALESCE(1.0 / (:k + fulltext_search.rank), 0.0) AS score
        FROM vector_search
        FULL OUTER JOIN fulltext_search ON vector_search.id = fulltext_search.id
        ORDER BY score DESC
        LIMIT 20
        """

        # Determine which query to run based on the inputs
        if query_text is not None and len(query_vector) > 0:
            sql = text(hybrid_query).columns(id=String, score=Float)
        elif len(query_vector) > 0:
            sql = text(vector_query).columns(id=String, rank=Integer)
        elif query_text is not None:
            sql = text(fulltext_query).columns(id=String, rank=Integer)
        else:
            raise ValueError("Both query text and query vector are empty")

        # Execute the SQL query using PostgreSQL
        async with self.async_session_maker() as session:
            results = (
                await session.execute(
                    sql,
                    {"embedding": to_db(query_vector), "query": query_text, "k": 60},
                )
            ).fetchall()

            # Convert results to Doc models
            docs = []
            for id, _ in results[:query_top]:
                doc = await session.execute(select(Doc).where(Doc.id == id))
                docs.append(doc.scalar())
            return docs
