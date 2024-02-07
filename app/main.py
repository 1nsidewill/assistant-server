from fastapi import FastAPI, HTTPException
# from starlette.middleware.sessions import SessionMiddleware
from app.config import Settings
from app.routers import agent_router, crud_router
from app.exceptions import (
    ItemNotFoundException,
    ValidationErrorException,
    item_not_found_exception_handler,
    validation_error_exception_handler,
    http_exception_handler,
    # Import other exceptions and handlers as needed
)
import uvicorn


# Initiate app
app = FastAPI(title=Settings().app_name)

# # Session Management
# app.add_middleware(SessionMiddleware, secret_key="your_secret_key")

# Register custom exception handlers
app.add_exception_handler(ItemNotFoundException, item_not_found_exception_handler)
app.add_exception_handler(ValidationErrorException, validation_error_exception_handler)

# Register handler for built-in HTTPException
app.add_exception_handler(HTTPException, http_exception_handler)

# Including Routers
app.include_router(agent_router, prefix="/agent")
app.include_router(crud_router, prefix="/crud") 