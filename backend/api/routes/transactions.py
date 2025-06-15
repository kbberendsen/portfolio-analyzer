from fastapi import APIRouter
from typing import List
from backend.models.transactions import Transaction
from backend.services.transactions import get_transactions
from fastapi import APIRouter, HTTPException, status
import traceback

router = APIRouter()

@router.get(
    "/all",
    response_model=List[Transaction],
    tags=["Transactions"],
    summary="Get All Processed Transactions",
    description="Retrieves a list of all processed transactions from the source file (csv export)."
)
def get_all_transactions():
    """
    This endpoint returns the complete list of cleaned and processed transactions.
    """ 
    try:
        # Fetch all transactions from the service layer.
        transactions = get_transactions()
        if transactions.empty:
            return []  # Return an empty list if no transactions are found.
    except Exception as e:
        traceback.print_exc()
        # If an error occurs while fetching transactions, raise an HTTP exception.
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while fetching transactions: {e}"
        )
    return transactions.to_dict(orient="records")