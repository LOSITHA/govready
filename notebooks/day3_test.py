import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from nlp.intent import IntentClassifier
from nlp.extractor import EntityExtractor


def print_separator(char="─", width=55):
    print(char * width)


def run_pipeline(query: str, intent_clf: IntentClassifier, extractor: EntityExtractor):
    print_separator("═")
    print(f"  QUERY: {query}")
    print_separator("═")

    intent_result = intent_clf.classify(query)
    print(f"  Matched service : {intent_result.get('service_name')}")
    print(f"  service_id      : {intent_result.get('service_id')}")
    print(f"  Confidence      : {intent_result.get('confidence')}")
    print()

    entities = extractor.extract(query)
    print("  Extracted attributes:")
    for key, value in entities.items():
        marker = "✓" if value is not None else "✗ (missing)"
        print(f"    {key:16s}: {value}  {marker}")
    print()


def run_tests():
    intent_clf = IntentClassifier()
    extractor = EntityExtractor()

    test_queries = [
        "I'm a widow in UP applying for a ration card, my income is below 1 lakh",
        "I'm a married woman working a government job in Maharashtra, need a passport",
        "SC category applicant in Karnataka wants a driving license",
        "how do I renew my driving license",
    ]

    for q in test_queries:
        run_pipeline(q, intent_clf, extractor)


if __name__ == "__main__":
    run_tests()