import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from nlp.intent import IntentClassifier
from nlp.extractor import EntityExtractor


# ─────────────────────────────────────────────────────────────────
# LABELED TEST SET
# Mix of: easy cases, terse follow-ups, edge cases already fixed,
# and deliberately hard cases (misspellings, ambiguity, code-mixed
# language, unrelated input) meant to find NEW failures.
# expected_service_id = None means "don't check intent for this one"
# (used for terse follow-up-style inputs that wouldn't realistically
# be a first message).
# ─────────────────────────────────────────────────────────────────
TEST_SET = [
    # ── Easy, clear cases ──────────────────────────────────────
    {"query": "I want a passport", "expected_service_id": "S001", "expected_entities": {}},
    {"query": "apply for ration card", "expected_service_id": "S002", "expected_entities": {}},
    {"query": "how do I renew my driving license", "expected_service_id": "S003", "expected_entities": {}},
    {
        "query": "I'm a widow in UP applying for a ration card, my income is below 1 lakh",
        "expected_service_id": "S002",
        "expected_entities": {"state": "UP", "gender": "female", "marital_status": "widow"},
    },
    {
        "query": "SC category applicant in Karnataka wants a driving license",
        "expected_service_id": "S003",
        "expected_entities": {"state": "KA", "category": "SC"},
    },
    {
        "query": "I'm a married woman working a government job in Maharashtra, need a passport",
        "expected_service_id": "S001",
        "expected_entities": {"state": "MH", "gender": "female", "marital_status": "married", "employment": "government"},
    },
    {
        "query": "fresh passport application for a single male in Delhi",
        "expected_service_id": "S001",
        "expected_entities": {"state": "DL", "gender": "male", "marital_status": "single"},
    },
    {
        "query": "how do I get a license to drive in Gujarat",
        "expected_service_id": "S003",
        "expected_entities": {"state": "GJ"},
    },
    {
        "query": "OBC category, new ration card, West Bengal",
        "expected_service_id": "S002",
        "expected_entities": {"state": "WB", "category": "OBC"},
    },
    {
        "query": "I need a PDS card, I'm unemployed",
        "expected_service_id": "S002",
        "expected_entities": {"employment": "unemployed"},
    },

    # ── Terse follow-up-style answers (entity extraction only) ──
    {"query": "i am in tamil nadu", "expected_service_id": None, "expected_entities": {"state": "TN"}},
    {"query": "private", "expected_service_id": None, "expected_entities": {"employment": "private"}},
    {"query": "widow", "expected_service_id": None, "expected_entities": {"marital_status": "widow"}},
    {"query": "male", "expected_service_id": None, "expected_entities": {"gender": "male"}},
    {"query": "married", "expected_service_id": None, "expected_entities": {"marital_status": "married"}},
    {"query": "unemployed", "expected_service_id": None, "expected_entities": {"employment": "unemployed"}},
    {"query": "govt", "expected_service_id": None, "expected_entities": {"employment": "government"}},
    {"query": "self", "expected_service_id": None, "expected_entities": {"employment": "self"}},
    {"query": "my income is 2 lakhs", "expected_service_id": None, "expected_entities": {"income": 200000.0}},
    {"query": "20,000", "expected_service_id": None, "expected_entities": {"income": 20000.0}},
    {"query": "income below 3 lakh", "expected_service_id": None, "expected_entities": {"income": 299999.0}},

    # ── Ambiguous / overlapping phrasing (harder intent cases) ──
    {
        "query": "I need help with a government document for driving",
        "expected_service_id": "S003",
        "expected_entities": {},
    },
    {
        "query": "renewal of my license",
        "expected_service_id": "S003",
        "expected_entities": {},
    },
    {
        "query": "need to get my ration sorted out",
        "expected_service_id": "S002",
        "expected_entities": {},
    },
    {
        "query": "travel document application",
        "expected_service_id": "S001",
        "expected_entities": {},
    },

    # ── Misspellings / informal typing ───────────────────────────
    {
        "query": "i want a pasport",
        "expected_service_id": "S001",
        "expected_entities": {},
    },
    {
        "query": "ration crad application",
        "expected_service_id": "S002",
        "expected_entities": {},
    },
    {
        "query": "drivin licence pls",
        "expected_service_id": "S003",
        "expected_entities": {},
    },

    # ── Code-mixed Hindi-English (realistic for Indian users) ───
    {
        "query": "mera passport banwana hai",
        "expected_service_id": "S001",
        "expected_entities": {},
    },
    {
        "query": "ration card ke liye kya chahiye",
        "expected_service_id": "S002",
        "expected_entities": {},
    },

    # ── Multiple attributes packed into one sentence ────────────
    {
        "query": "ST category widow in Tamil Nadu, unemployed, applying for ration card, income around 50000",
        "expected_service_id": "S002",
        "expected_entities": {
            "state": "TN", "category": "ST", "marital_status": "widow",
            "employment": "unemployed", "income": 50000.0,
        },
    },
    {
        "query": "divorced female, private job, Karnataka, passport needed",
        "expected_service_id": "S001",
        "expected_entities": {
            "state": "KA", "gender": "female", "marital_status": "divorced", "employment": "private",
        },
    },

    # ── Deliberately unrelated / gibberish (tests confidence gate) ──
    {
        "query": "what's the weather today",
        "expected_service_id": None,
        "expected_entities": {},
    },
    {
        "query": "asdkj alskdj document xyz123",
        "expected_service_id": None,
        "expected_entities": {},
    },
    {
        "query": "tell me a joke",
        "expected_service_id": None,
        "expected_entities": {},
    },

    # ── Empty / minimal input ────────────────────────────────────
    {"query": "hi", "expected_service_id": None, "expected_entities": {}},
    {"query": "help", "expected_service_id": None, "expected_entities": {}},
]


LOW_CONFIDENCE_QUERIES = {
    "what's the weather today",
    "asdkj alskdj document xyz123",
    "tell me a joke",
    "hi",
    "help",
}
CONFIDENCE_THRESHOLD = 0.4


def evaluate():
    intent_clf = IntentClassifier()
    extractor = EntityExtractor()

    intent_total = 0
    intent_correct = 0
    intent_failures = []

    gate_total = 0
    gate_correct = 0
    gate_failures = []

    field_total = 0
    field_correct = 0
    field_failures = []

    for case in TEST_SET:
        query = case["query"]
        result = intent_clf.classify(query)

        # ── Confidence gate check (unrelated/gibberish inputs) ─────
        if query in LOW_CONFIDENCE_QUERIES:
            gate_total += 1
            should_be_rejected = result["confidence"] < CONFIDENCE_THRESHOLD
            if should_be_rejected:
                gate_correct += 1
            else:
                gate_failures.append({
                    "query": query,
                    "confidence": result["confidence"],
                    "wrongly_matched_to": result["service_name"],
                })

        # ── Intent accuracy (only for cases that test intent) ──────
        elif case["expected_service_id"] is not None:
            intent_total += 1
            predicted = result["service_id"]
            if predicted == case["expected_service_id"]:
                intent_correct += 1
            else:
                intent_failures.append({
                    "query": query,
                    "expected": case["expected_service_id"],
                    "predicted": predicted,
                    "confidence": result["confidence"],
                })

        # ── Entity extraction accuracy (field by field) ────────────
        extracted = extractor.extract(query)
        for field, expected_value in case["expected_entities"].items():
            field_total += 1
            actual_value = extracted.get(field)
            if actual_value == expected_value:
                field_correct += 1
            else:
                field_failures.append({
                    "query": query,
                    "field": field,
                    "expected": expected_value,
                    "actual": actual_value,
                })

    # ── Report ───────────────────────────────────────────────────
    print("=" * 60)
    print("  EVALUATION REPORT")
    print("=" * 60)

    intent_accuracy = (intent_correct / intent_total * 100) if intent_total else 0
    print(f"\nIntent Classification Accuracy: {intent_correct}/{intent_total} "
          f"({intent_accuracy:.1f}%)")
    if intent_failures:
        print("\n  Failures:")
        for f in intent_failures:
            print(f"    \"{f['query']}\" -> expected={f['expected']} "
                  f"predicted={f['predicted']} confidence={f['confidence']}")

    gate_accuracy = (gate_correct / gate_total * 100) if gate_total else 0
    print(f"\nConfidence Gate Accuracy (correctly rejecting unrelated input): "
          f"{gate_correct}/{gate_total} ({gate_accuracy:.1f}%)")
    if gate_failures:
        print("\n  Failures (wrongly matched instead of rejected):")
        for f in gate_failures:
            print(f"    \"{f['query']}\" -> confidence={f['confidence']} "
                  f"wrongly matched to \"{f['wrongly_matched_to']}\"")

    field_accuracy = (field_correct / field_total * 100) if field_total else 0
    print(f"\nEntity Extraction Accuracy: {field_correct}/{field_total} "
          f"({field_accuracy:.1f}%)")
    if field_failures:
        print("\n  Failures:")
        for f in field_failures:
            print(f"    \"{f['query']}\" -> field={f['field']} "
                  f"expected={f['expected']} actual={f['actual']}")

    print("\n" + "=" * 60)
    print(f"  SUMMARY: Intent {intent_accuracy:.1f}% | "
          f"Gate {gate_accuracy:.1f}% | Entities {field_accuracy:.1f}%")
    print("=" * 60)


if __name__ == "__main__":
    evaluate()