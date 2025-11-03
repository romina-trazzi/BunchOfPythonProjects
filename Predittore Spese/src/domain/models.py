from dataclasses import dataclass
from typing import Optional, List, Dict
from datetime import date

@dataclass
class Transaction:
    date: date
    description: str
    amount: float
    type: str  # 'debito' | 'credito'
    category: Optional[str] = None

@dataclass
class MonthlyAggregate:
    year_month: str  # YYYY-MM
    income: float
    expense: float
    balance: float

@dataclass
class AlertItem:
    category: str
    month: str  # YYYY-MM
    expense: float
    average: float
    threshold: float