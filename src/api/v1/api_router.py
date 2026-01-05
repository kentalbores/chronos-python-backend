from fastapi import APIRouter

from src.api.v1.routers import input, users, departments, attendance, roles

# Define the main API router for this version (v1)
api_v1_router = APIRouter()

# Include routers
api_v1_router.include_router(input.router)
api_v1_router.include_router(users.router)
api_v1_router.include_router(departments.router)
api_v1_router.include_router(attendance.router)
api_v1_router.include_router(roles.router)
