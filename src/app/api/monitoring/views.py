from fastapi import APIRouter
import warnings

router = APIRouter()

warnings.filterwarnings("ignore")
@router.get("/health")
def health_check() -> None:
    """
    Checks the health of a project.

    It returns 200 if the project is healthy.
    """
    return {"status": "ok"}
