from .auth import auth_route
from .user import users_route

routes = [
    auth_route.auth_router,
    users_route.user_router
]