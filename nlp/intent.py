from sentence_transformers import SentenceTransformer, util

class IntentClassifier:
    """
    Identifies which government service a user is asking about,
    using semantic similarity (no training data required).
    """

    def __init__(self):
        self.model = SentenceTransformer("all-MiniLM-L6-v2")

        self.services = [
            {
                "service_id": "S001",
                "name": "Passport - Fresh Application",
                "examples": [
                    "I want to apply for a new passport",
                    "passport application",
                    "how do I get a passport",
                    "fresh passport",
                ],
            },
            {
                "service_id": "S002",
                "name": "Ration Card - New Application",
                "examples": [
                    "I need a ration card",
                    "apply for ration card",
                    "new ration card application",
                    "PDS card",
                ],
            },
            {
                "service_id": "S003",
                "name": "Driving Licence - Fresh (LMV)",
                "examples": [
                    "I want to get a driving licence",
                    "apply for driving license",
                    "new driving licence LMV",
                    "how do I get a license to drive",
                ],
            },
        ]

        self._corpus = []
        self._corpus_service_ids = []
        for service in self.services:
            for example in service["examples"]:
                self._corpus.append(example)
                self._corpus_service_ids.append(service["service_id"])

        self._corpus_embeddings = self.model.encode(
            self._corpus, convert_to_tensor=True
        )

    def classify(self, query: str, top_k: int = 1) -> dict:
        query_embedding = self.model.encode(query, convert_to_tensor=True)
        hits = util.semantic_search(
            query_embedding, self._corpus_embeddings, top_k=top_k
        )[0]

        if not hits:
            return {"service_id": None, "confidence": 0.0}

        best = hits[0]
        matched_service_id = self._corpus_service_ids[best["corpus_id"]]
        matched_service = next(
            s for s in self.services if s["service_id"] == matched_service_id
        )

        return {
            "service_id": matched_service_id,
            "service_name": matched_service["name"],
            "confidence": round(float(best["score"]), 3),
            "matched_phrase": self._corpus[best["corpus_id"]],
        }


if __name__ == "__main__":
    clf = IntentClassifier()
    test_queries = [
        "I'm a widow in UP applying for a ration card",
        "how do I renew my driving license",
        "need help getting my first passport",
    ]
    for q in test_queries:
        result = clf.classify(q)
        print(f"Query: {q}")
        print(f"  → {result}\n")