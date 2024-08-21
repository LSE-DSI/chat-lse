import spacy
from spacy.training import Example

# Create a blank model or load a pre-existing one
nlp = spacy.blank("en")

# Add a Named Entity Recognizer to the pipeline
ner = nlp.add_pipe("ner")

# Add your custom labels
ner.add_label("MOVIE")
ner.add_label("ACTOR")

# Example training data
TRAIN_DATA = [
    ("Who directed Inception?", {"entities": [(14, 23, "MOVIE")]}),
    ("Which actors starred in The Matrix?", {"entities": [(22, 32, "MOVIE")]}),
]

# Disable other pipeline components for efficiency during training
unaffected_pipes = [pipe for pipe in nlp.pipe_names if pipe != 'ner']

# Begin training
with nlp.disable_pipes(*unaffected_pipes):
    optimizer = nlp.begin_training()
    
    # Train the model
    for iteration in range(10):  # Adjust the number of iterations as needed
        # Loop through the training data
        for text, annotations in TRAIN_DATA:
            # Convert the data into a format spaCy understands (Example objects)
            doc = nlp.make_doc(text)
            example = Example.from_dict(doc, annotations)
            
            # Update the model
            nlp.update([example], sgd=optimizer)

# Save the model to disk
nlp.to_disk("my_ner_model")
