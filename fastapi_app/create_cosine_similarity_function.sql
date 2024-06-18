CREATE OR REPLACE FUNCTION cosine_similarity(json_vectors JSONB, target_vector FLOAT[])
RETURNS TABLE(vector_index INT, similarity FLOAT) AS $$
DECLARE
    element JSONB;
    index INT := 1;
BEGIN
    FOR element IN SELECT * FROM jsonb_array_elements(json_vectors)
    LOOP
        -- Assuming cosine_sim_calc is a function you've defined to calculate cosine similarity
        -- between two FLOAT arrays.
        RETURN QUERY SELECT index, cosine_sim_calc(ARRAY(SELECT jsonb_array_elements_text(element)::float), target_vector);
        index := index + 1;
    END LOOP;
END;
$$ LANGUAGE plpgsql IMMUTABLE;
