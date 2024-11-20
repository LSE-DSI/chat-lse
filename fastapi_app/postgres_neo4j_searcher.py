from pgvector.utils import to_db
from sqlalchemy import Float, Integer, String, select, text
from sqlalchemy.ext.asyncio import async_sessionmaker
from neo4j import GraphDatabase
from .postgres_models import Doc


class Postgres_neo4j_Searcher:
    def __init__(self, engine, neo4j_driver=None):
        # Initialize PostgreSQL session maker
        self.async_session_maker = async_sessionmaker(engine, expire_on_commit=False)
        # Initialize Neo4j driver
        self.neo4j_driver = neo4j_driver

    def enrich_query_with_graph(self, original_query: str, name_embedding):
        enriched_terms = []
        relevant_doc_ids = []

        if name_embedding is None:
            print("Name embedding is None. Skipping Neo4j enrichment.")
            return enriched_terms, relevant_doc_ids

        with self.neo4j_driver.session() as neo4j_session:
            neo4j_query = """
            WITH $name_embedding AS nameEmbedding
            MATCH (n)
            WHERE n.embedding IS NOT NULL
            WITH n, vector.similarity.cosine(n.embedding, nameEmbedding) AS similarity
            ORDER BY similarity DESC
            LIMIT 3
            """
            try:
                print("Running Neo4j query:", neo4j_query)
                result = neo4j_session.run(neo4j_query, name_embedding=name_embedding).values()
                for record in result:
                    enriched_terms.extend(record[0])
                    relevant_doc_ids.extend(record[1])
            except Exception as e:
                print(f"Error querying Neo4j: {e}")
                raise

        return enriched_terms, relevant_doc_ids

    def build_filter_clause(self, filters) -> tuple[str, str]:
        if not filters:
            return "", ""
        filter_clauses = [
            f"{filter['column']} {filter['comparison_operator']} {filter['value']!r}"
            for filter in filters
        ]
        filter_clause = " OR ".join(filter_clauses)
        return f"WHERE {filter_clause}", f"AND {filter_clause}" if filter_clause else ""

    async def search(
        self,
        query_text: str | None,
        query_vector: list[float] | list,
        query_top: int = 5,
        name_embedding: str | None = None,
        original_query: str | None = None,
        enhanced_results: list | None = None,  # Enhanced results as a list
    ):
        filters = []

        # Add existing enhanced results to filters
        if enhanced_results:
            print(f"Using enhanced_results: {enhanced_results}")
            filters.extend({"column": "doc_id", "comparison_operator": "=", "value": doc_id} for doc_id in enhanced_results)

        if query_vector:
            enriched_terms, relevant_doc_ids = self.enrich_query_with_graph(original_query, name_embedding)
            enriched_terms = list(set(enriched_terms))
            relevant_doc_ids = list(set(relevant_doc_ids))
            enriched_query_text = " OR ".join(str(x) for x in enriched_terms)
            query_text = f"({query_text}) OR ({enriched_query_text})" if query_text else enriched_query_text
            filters.extend({"column": "doc_id", "comparison_operator": "=", "value": doc_id} for doc_id in relevant_doc_ids)

        filter_clause_where, filter_clause_and = self.build_filter_clause(filters)

        # SQL Queries (unchanged)
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

        sql = (
            text(hybrid_query).columns(id=String, score=Float)
            if query_text and query_vector
            else text(vector_query).columns(id=String, rank=Integer)
            if query_vector
            else text(fulltext_query).columns(id=String, rank=Integer)
        )

        docs = []
        async with self.async_session_maker() as session:
            results = await session.execute(
                sql,
                {"embedding": to_db(query_vector), "query": query_text, "k": 60}
            )
            for row in results.fetchall()[:query_top]:
                doc = await session.execute(select(Doc).where(Doc.id == row.id))
                docs.append(doc.scalar())

        # Use Neo4j to enrich results
        if enhanced_results is None:
            enhanced_results = []  # Initialize enhanced_results if not provided

        with self.neo4j_driver.session() as neo4j_session:
            for result in docs:
                doc_id = result.doc_id
                neo4j_query = f"""
                MATCH (n)-[r1]->(related)-[r2]->(related_related)
                WHERE n.doc_id = '{doc_id}'
                RETURN n, related, type(r1), related_related, type(r2)
                """
                related_nodes = neo4j_session.run(neo4j_query).values()
                if not related_nodes:
                    print(f"No related nodes found for doc_id: {doc_id}")
                    continue

                formatted_related_nodes = [
                    f"{n.get('name', 'Unnamed Node')} [{rel_type_1}] {related.get('name', 'Unnamed Node')} [{rel_type_2}] {related_related.get('name', 'Unnamed Node')}"
                    for n, related, rel_type_1, related_related, rel_type_2 in related_nodes
                ]
                enhanced_results.append((doc_id, formatted_related_nodes, result))

        return enhanced_results


    def close(self):
        """Close the Neo4j driver connection."""
        if self.neo4j_driver:
            self.neo4j_driver.close()
