from dataclasses import dataclass, field
from typing import Optional

@dataclass
class ApplicantProfile:
    """
    Represents a citizen's profile used to predict
    which documents they need for a government service.
    """
    # Service they are applying for (matches service_id in KG)
    service_id: str

    # State they are applying in
    state: str = "ALL"

    # Personal attributes used for conditional document resolution
    gender: Optional[str] = None           # 'male', 'female', 'other'
    marital_status: Optional[str] = None   # 'single', 'married', 'widow', 'divorced'
    employment: Optional[str] = None       # 'government', 'private', 'self', 'unemployed'
    category: Optional[str] = None         # 'general', 'OBC', 'SC', 'ST'
    income: Optional[float] = None         # annual income in INR

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if v is not None}

    def evaluate_condition(self, condition: str) -> bool:
        """
        Evaluates a condition string from the KG against this profile.
        Example condition: "applicant_marital_status == 'married' AND applicant_gender == 'female'"
        """
        if not condition:
            return False

        # Map condition variable names to profile attributes
        context = {
            "applicant_gender":         self.gender,
            "applicant_marital_status": self.marital_status,
            "applicant_employment":     self.employment,
            "applicant_category":       self.category,
            "applicant_income":         self.income,
        }

        try:
            return bool(eval(condition, {"__builtins__": {}}, context))
        except Exception:
            # If condition can't be evaluated (missing profile field), skip it
            return False