from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, time

class Transaction(BaseModel):
    """
    Defines the data structure for a single transaction record.
    This model is used to validate the API response.
    """
    Date: date
    Time: time
    product_name_degiro: Optional[str] = Field(None, alias='Product Name DeGiro') # Use Field(alias=...) to handle column names with spaces
    ISIN: str
    Exchange: Optional[str] = None
    Quantity: int
    Price: float
    Currency: str
    Cost: float
    Transaction_costs: float
    Stock: str
    Product: str
    Action: str