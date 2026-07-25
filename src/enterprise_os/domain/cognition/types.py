from typing import Literal


Confidence = Literal["Low", "Medium", "High"]
StrategyRecommendation = Literal["Recommended", "Rejected"]


CONFIDENCE_LEVELS: tuple[Confidence, ...] = ("Low", "Medium", "High")
