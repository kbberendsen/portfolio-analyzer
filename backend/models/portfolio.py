from pydantic import BaseModel

class PortfolioCalculationRequest(BaseModel):
    """
    Defines the expected input for triggering a portfolio calculation.
    The frontend must send a JSON with a "start_date" key.
    """
    start_date: str