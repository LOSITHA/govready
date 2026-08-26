import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from kg.query import GovReadyKG
from kg.profile import ApplicantProfile


def print_separator(char="─", width=55):
    print(char * width)


def display_prediction(result: dict):
    if "error" in result:
        print(f"❌ Error: {result['error']}")
        return

    meta = result["service_meta"]
    print_separator("═")
    print(f"  SERVICE  : {meta['service_name']}")
    print(f"  CONFIDENCE: {result['confidence_score']}%")
    print(f"  TOTAL DOCS NEEDED: {result['total_docs_required']}")
    print_separator("═")

    print("\n📋 MANDATORY DOCUMENTS:")
    for doc in result["mandatory"]:
        print(f"  ✓ {doc['name']}  ({doc['rule_ref']})")

    if result["applicable_conditional"]:
        print("\n⚠️  CONDITIONAL DOCUMENTS (apply to this profile):")
        for doc in result["applicable_conditional"]:
            print(f"  ✓ {doc['name']}  ({doc['rule_ref']})")
            print(f"    Triggered by: {doc['triggered_by']}")


if __name__ == "__main__":
    # This exact profile came from your teammate's NLP pipeline
    # (query was: "I want a passport" -> conversation loop -> this profile)
    profile_data = {
        "service_id": "S001",
        "state": "TN",
        "gender": "female",
        "marital_status": "widow",
        "employment": "private",
    }

    profile = ApplicantProfile(**profile_data)

    kg = GovReadyKG()
    result = kg.predict_documents(profile)
    display_prediction(result)
    kg.close()

    print("\n\n✅ If you see a document list above with no errors, "
          "the NLP → KG handoff works end to end.")