from kg.profile import ApplicantProfile

class ProfileBuilder:
    """
    Converts extracted entities (from EntityExtractor) into a real
    ApplicantProfile object, and figures out what's still missing
    so the system can ask the right follow-up question.
    """

    # Human-readable question for each field, asked only if it's missing.
    # Order matters — state is almost always needed, income/category
    # matter more for welfare-type services, so we ask state first.
    FIELD_QUESTIONS = {
        "state": "Which state are you applying in?",
        "gender": "Are you male, female, or other?",
        "marital_status": "What is your marital status? (single / married / widow / divorced)",
        "employment": "What is your employment status? (government / private / self-employed / unemployed)",
        "category": "What category do you belong to? (general / OBC / SC / ST)",
        "income": "What is your approximate annual income?",
    }

    # Not every field matters for every service. This keeps us from
    # asking irrelevant questions (e.g. no need to ask income for a
    # passport application).
    RELEVANT_FIELDS_BY_SERVICE = {
        "S001": ["state", "gender", "marital_status", "employment"],   # Passport
        "S002": ["state", "gender", "marital_status", "income"],       # Ration Card
        "S003": ["state", "category"],                                  # Driving Licence
    }

    def build(self, service_id: str, extracted: dict) -> dict:
        """
        Returns a dict with:
          - profile: an ApplicantProfile built from whatever was extracted
          - missing_fields: fields still needed for THIS service
          - next_question: the single best follow-up question to ask
          - is_complete: True if nothing relevant is missing
        """
        profile = ApplicantProfile(
            service_id=service_id,
            state=extracted.get("state") or "ALL",
            gender=extracted.get("gender"),
            marital_status=extracted.get("marital_status"),
            employment=extracted.get("employment"),
            category=extracted.get("category"),
            income=extracted.get("income"),
        )

        relevant_fields = self.RELEVANT_FIELDS_BY_SERVICE.get(
            service_id,
            list(self.FIELD_QUESTIONS.keys()),  # fallback: ask about everything
        )

        missing_fields = [
            field for field in relevant_fields
            if getattr(profile, field) is None or (field == "state" and profile.state == "ALL")
        ]

        next_question = (
            self.FIELD_QUESTIONS[missing_fields[0]] if missing_fields else None
        )

        return {
            "profile": profile,
            "missing_fields": missing_fields,
            "next_question": next_question,
            "is_complete": len(missing_fields) == 0,
        }


if __name__ == "__main__":
    from nlp.intent import IntentClassifier
    from nlp.extractor import EntityExtractor

    intent_clf = IntentClassifier()
    extractor = EntityExtractor()
    builder = ProfileBuilder()

    test_queries = [
        "I'm a widow in UP applying for a ration card, my income is below 1 lakh",
        "how do I renew my driving license",
        "I want a passport",
    ]

    for q in test_queries:
        print(f"Query: {q}")
        intent = intent_clf.classify(q)
        entities = extractor.extract(q)
        result = builder.build(intent["service_id"], entities)

        print(f"  Service: {intent['service_name']}")
        print(f"  Profile so far: {result['profile'].to_dict()}")
        print(f"  Missing fields: {result['missing_fields']}")
        print(f"  Is complete: {result['is_complete']}")
        if result["next_question"]:
            print(f"  → Next question to ask: \"{result['next_question']}\"")
        print()