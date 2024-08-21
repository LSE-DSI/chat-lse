import spacy 

nlp = spacy.load("en_core_web_sm")

user_input = "How do I switch from BSc in Economics to BSc in Mathematics and Economics?"

doc = nlp(user_input)
entities = [(ent.text, ent.label_) for ent in doc.ents]

# Print extracted entities
print(entities)