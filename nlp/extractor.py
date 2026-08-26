import re

class EntityExtractor:
    """
    Extracts applicant attributes from free-text queries using
    keyword/pattern matching.
    """

    STATE_KEYWORDS = {
        "UP": ["uttar pradesh", "up"],
        "MH": ["maharashtra", "mh"],
        "KA": ["karnataka", "ka"],
        "WB": ["west bengal", "wb"],
        "TN": ["tamil nadu", "tn"],
        "GJ": ["gujarat", "gj"],
        "DL": ["delhi", "dl"],
    }

    GENDER_KEYWORDS = {
        "female": ["woman", "female", "she", "her", "widow", "wife"],
        "male": ["man", "male", "he", "his", "husband"],
    }

    MARITAL_KEYWORDS = {
        "widow": ["widow", "widower"],
        "married": ["married", "wife", "husband", "spouse"],
        "single": ["single", "unmarried"],
        "divorced": ["divorced"],
    }

    EMPLOYMENT_KEYWORDS = {
        "government": ["government employee", "govt employee", "government job", "government", "govt"],
        "private": ["private employee", "private job", "private company", "private"],
        "self": ["self employed", "self-employed", "business owner", "self"],
        "unemployed": ["unemployed", "no job", "not working"],
    }

    CATEGORY_KEYWORDS = {
        "SC": ["sc category", "scheduled caste"],
        "ST": ["st category", "scheduled tribe"],
        "OBC": ["obc category", "other backward class"],
        "general": ["general category"],
    }

    def extract(self, query: str) -> dict:
        text = query.lower()
        result = {
            "state": self._match_keywords(text, self.STATE_KEYWORDS),
            "gender": self._match_keywords(text, self.GENDER_KEYWORDS),
            "marital_status": self._match_keywords(text, self.MARITAL_KEYWORDS),
            "employment": self._match_keywords(text, self.EMPLOYMENT_KEYWORDS),
            "category": self._match_keywords(text, self.CATEGORY_KEYWORDS),
            "income": self._extract_income(text),
        }
        return result

    def _match_keywords(self, text: str, keyword_map: dict):
        for value, keywords in keyword_map.items():
            for kw in keywords:
                if kw in text:
                    return value
        return None

    def _extract_income(self, text: str):
        text = text.replace(",", "")

        below_lakh_match = re.search(r"below\s+(\d+(?:\.\d+)?)\s*lakh", text)
        if below_lakh_match:
            return float(below_lakh_match.group(1)) * 100000 - 1

        lakh_match = re.search(r"(\d+(?:\.\d+)?)\s*lakh", text)
        if lakh_match:
            return float(lakh_match.group(1)) * 100000

        number_match = re.search(r"\b(\d{4,7})\b", text)
        if number_match:
            return float(number_match.group(1))

        return None


if __name__ == "__main__":
    ext = EntityExtractor()
    test_queries = [
        "I'm a widow in UP applying for a ration card, my income is below 1 lakh",
        "I'm a married woman working a government job in Maharashtra",
        "SC category applicant in Karnataka, unemployed",
    ]
    for q in test_queries:
        print(f"Query: {q}")
        print(f"  → {ext.extract(q)}\n")