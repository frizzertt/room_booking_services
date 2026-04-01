from fastapi import FastAPI

from app.api.routes_auth import router as auth_router
from app.api.routes_bookings import router as bookings_router
from app.api.routes_rooms import router as rooms_router
from app.api.routes_schedules import router as schedules_router
from app.api.routes_slots import router as slots_router
from app.core.errors import register_exception_handlers


def create_app() -> FastAPI:
    app = FastAPI(title="Room Booking Service", version="1.0.0")
    register_exception_handlers(app)

    @app.get("/_info", tags=["System"])
    def info() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(auth_router)
    app.include_router(rooms_router)
    app.include_router(schedules_router)
    app.include_router(slots_router)
    app.include_router(bookings_router)
    return app


app = create_app()
