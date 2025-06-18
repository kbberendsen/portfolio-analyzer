from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, time

class Transaction(BaseModel):
    """
    Defines the data structure for a single transaction record.
    This model is used to validate the API response.
    """
    Date: Optional[date] = None
    Time: Optional[time] = None
    Product_Name_DeGiro: Optional[str] = None
    ISIN: str
    Exchange: Optional[str] = None
    Quantity: float
    Price: float
    Currency: str
    Cost: float
    Transaction_Costs: float
    Stock: str
    Product: str
    Action: str