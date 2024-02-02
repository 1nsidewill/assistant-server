from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from typing import Union

# Custom Exception Classes
class ItemNotFoundException(HTTPException):
    def __init__(self, item_id: Union[int, str]):
        detail = f"Item with ID {item_id} not found"
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)

class ValidationErrorException(HTTPException):
    def __init__(self, detail: str):
        super().__init__(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail)

# Exception Handlers
async def item_not_found_exception_handler(request: Request, exc: ItemNotFoundException):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"message": exc.detail},
    )

async def validation_error_exception_handler(request: Request, exc: ValidationErrorException):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"message": exc.detail},
    )

async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.detail},
    )
