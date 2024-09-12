from pgvector.utils import to_db
from sqlalchemy import Float, Integer, String, select, text
from sqlalchemy.ext.asyncio import async_sessionmaker

from .postgres_models import Doc
from neo4j import GraphDatabase
import os 

class PostgresFirst:
    def __init__(self, postgres_engine):
        neo4j_uri = os.getenv("NEO4J_URL")
        neo4j_user = os.getenv("NEO4J_USERNAME")
        neo4j_password = os.getenv("NEO4J_PASSWORD")
        # Initialize PostgreSQL session maker
        self.async_session_maker = async_sessionmaker(postgres_engine, expire_on_commit=False)
        
        # Initialize Neo4j driver
        self.neo4j_driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))

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
    ):
        # Build the filter clauses for SQL queries
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

        # Use Neo4j to enhance the results
        enhanced_results = []
        with self.neo4j_driver.session() as neo4j_session:
            for result in docs:
                doc_id = result.doc_id

                # First query for entities with the same doc_id
                first_neo4j_query = f"""
                MATCH (n {{doc_id: '{doc_id}'}})
                RETURN n
                """
                # Find out which communities the entities are in 
                communities = [json['community'] for json in neo4j_session.run(first_neo4j_query)]

                #Return all nodes that are in that community
                for community in communities:
                    final_neo4j_query = f"""
                    MATCH (n {{community: '{community}'}})
                    RETURN n 
                    """
                related_nodes = neo4j_session.run(final_neo4j_query).values()

                formatted_related_nodes = []

                for n, related, related_related, rel_type_1, rel_type_2 in related_nodes:
                    # Convert nodes to dictionaries with all their properties
                    n_properties = dict(n.items()) if n else {}
                    related_properties = dict(related.items()) if related else {}
                    related_related_properties = dict(related_related.items()) if related_related else {}

                    if related and related_related:
                        # Chain of relations
                        formatted_related_nodes.append({
                            "start_node": n_properties,
                            "relationship_1": rel_type_1,
                            "middle_node": related_properties,
                            "relationship_2": rel_type_2,
                            "end_node": related_related_properties
                        })
                    elif related:
                        # Single relation
                        formatted_related_nodes.append({
                            "start_node": n_properties,
                            "relationship_1": rel_type_1,
                            "end_node": related_properties
                        })

                enhanced_results.append((doc_id, formatted_related_nodes, result))

        return enhanced_results

    def close(self):
        """Close the Neo4j driver connection when done."""
        self.neo4j_driver.close()





class PostgresSecond:
    def __init__(self, engine, neo4j_driver=None):
        # Initialize PostgreSQL session maker
        self.async_session_maker = async_sessionmaker(engine, expire_on_commit=False)
        # Initialize Neo4j driver
        self.neo4j_driver = neo4j_driver


    def enrich_query_with_graph(self, original_query: str, query_embedding):
        enriched_terms = []
        relevant_doc_ids = []
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
                    enriched_terms.append(record[0])  
                    relevant_doc_ids.append(record[1])
            

                #enriched_terms.add(record[0:3]) if record[i] is not None
                #enriched_terms.update(record[1] if record[1] else [])
        return enriched_terms, relevant_doc_ids
    

    def build_filter_clause(self, filters) -> tuple[str, str]:
        if filters is None:
            return "", ""
        filter_clauses = []
        for filter in filters:
            if isinstance(filter["value"], str):
                filter["value"] = f"'{filter['value']}'"
            filter_clauses.append(f"{filter['column']} {filter['comparison_operator']} {filter['value']}")
        filter_clause = " OR ".join(filter_clauses)
        if len(filter_clause) > 0:
            return f"WHERE {filter_clause}", f"AND {filter_clause}"
        return "", ""


    async def search(
        self,
        query_text: str | None,
        query_vector: list[float] | list,
        query_top: int = 5,
        query_embedding: str | None = None,
        orignal_query: str | None = None 
    ):
        filters = []
        # Only use graph database when llm_generated_query is passed 
        if query_vector: 
            # Enrich the query with graph-based terms
            enriched_terms= self.enrich_query_with_graph(orignal_query, query_vector) if query_vector else []
            relevant_doc_ids = list(set(enriched_terms[1]))
            enriched_terms = list(set(enriched_terms[0]))


            print(f"RELEVANT DOC IDS: {relevant_doc_ids}")
            print(f"ENRICHED TERMS: {enriched_terms}")
            if enriched_terms:
                print(f"ENRICHED TERMS: {enriched_terms}")
                enriched_query_text = " OR ".join(x for x in enriched_terms)
                query_text = f"({query_text}) OR ({enriched_query_text})" if query_text else enriched_query_text
                for doc_id in relevant_doc_ids:
                    print(f"DOC ID: {doc_id}")
                    filters.append({"column": "doc_id", "comparison_operator": "=", "value": doc_id})
            else:
                enriched_query_text = query_text

            print(f"ENRICHED QUERY TEXT: {enriched_query_text}")
            print(f"FILTERS: {filters}")
        
        filter_clause_where, filter_clause_and = self.build_filter_clause(filters)

        # Add filtering by relevant doc_ids if available
        if relevant_doc_ids:
            relevant_doc_ids_list = ', '.join(f"'{doc_id}'" for doc_id in relevant_doc_ids)
            doc_id_filter = f"AND id IN ({relevant_doc_ids_list})"
        else:
            doc_id_filter = ""


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
        
        print(f"SQL: {sql}")

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