import json

from nlp.intent import IntentClassifier
from nlp.extractor import EntityExtractor
from nlp.profile_builder import ProfileBuilder


class ConversationManager:
    """
    Runs a multi-turn conversation with a citizen:
      1. Takes their first message, detects intent + extracts what it can
      2. If fields are missing, asks one question at a time
      3. Merges each reply into the growing profile
      4. Stops once the profile is complete for that service

    This is the piece that makes the system feel conversational
    instead of a form.
    """

    def __init__(self):
        self.intent_clf = IntentClassifier()
        self.extractor = EntityExtractor()
        self.builder = ProfileBuilder()

    def start(self, first_message: str) -> dict:
        """
        Runs one full conversation from the first message to a
        complete profile, using terminal input() for follow-ups.
        Returns the final structured result.
        """
        intent = self.intent_clf.classify(first_message)
        service_id = intent["service_id"]

        print(f"\n(matched service: {intent['service_name']}, "
              f"confidence {intent['confidence']})\n")

        # Extracted entities accumulate across turns in this dict
        collected = self.extractor.extract(first_message)

        result = self.builder.build(service_id, collected)

        # Keep asking until nothing relevant is missing
        while not result["is_complete"]:
            question = result["next_question"]
            print(f"Assistant: {question}")
            reply = input("You: ")

            # Extract whatever this reply gives us, merge into what we have
            new_entities = self.extractor.extract(reply)
            for field, value in new_entities.items():
                if value is not None:
                    collected[field] = value

            result = self.builder.build(service_id, collected)

        print("\n✅ Profile complete. Ready to send for document prediction.\n")
        return {
            "service_id": service_id,
            "service_name": intent["service_name"],
            "profile": result["profile"].to_dict(),
        }


if __name__ == "__main__":
    manager = ConversationManager()

    print("=" * 55)
    print("  GovReady — describe what you need in your own words")
    print("=" * 55)
    first_message = input("You: ")

    final = manager.start(first_message)

    print("Final profile (this is what gets sent to the KG engine):")
    print(json.dumps(final, indent=2))