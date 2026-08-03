from app.core.vector_store import vector_store

data = vector_store.collection.get()

found = False

for doc, meta in zip(data["documents"], data["metadatas"]):
    if "HQRNORM REVIW00002443AM25".lower() in doc.lower():
        found = True
        print("=" * 100)
        print("Metadata:", meta)
        print("-" * 100)
        print(doc)
        print("=" * 100)

if not found:
    print("No matching chunk found.")