from fastapi import FastAPI, HTTPException
# from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware
from app.config import Settings
from app.routers import assistant_router, crud_router
from app.exceptions import *
# Import other exceptions and handlers as needed
import uvicorn


# Initiate app
app = FastAPI(title=Settings().app_name)

# Including Routers
app.include_router(assistant_router, prefix="/assistant")
app.include_router(crud_router, prefix="/crud") 

# # Session Management
# app.add_middleware(SessionMiddleware, secret_key="your_secret_key")

# Register custom exception handlers
app.add_exception_handler(ItemNotFoundException, item_not_found_exception_handler)
app.add_exception_handler(NothingToRespondException, nothing_to_respond_exception_handler)
app.add_exception_handler(ValidationErrorException, validation_error_exception_handler)

app.add_exception_handler(HTTPException, http_exception_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 출처 허용
    allow_credentials=True,
    allow_methods=["*"],  # 모든 HTTP 메서드 허용
    allow_headers=["*"],  # 모든 헤더 허용
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8005)