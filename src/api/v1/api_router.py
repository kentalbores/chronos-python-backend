from fastapi import APIRouter

from src.api.v1.routers import input, users, departments, attendance, roles, opensearch, leaves

api_v1_router = APIRouter()

api_v1_router.include_router(input.router)
api_v1_router.include_router(users.router)
api_v1_router.include_router(departments.router)
api_v1_router.include_router(attendance.router)
api_v1_router.include_router(roles.router)
api_v1_router.include_router(opensearch.router)
api_v1_router.include_router(leaves.router)