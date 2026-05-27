from .auth import auth_route
from .user import users_route
from .categories import categories_route
from .quizzes import quizzes_route
from .questions import questions_route
from .rooms import rooms_route
from .ws import ws_route

routes = [
    auth_route.auth_router,
    users_route.user_router,
    categories_route.category_router,
    quizzes_route.quiz_router,
    questions_route.question_router,
    rooms_route.room_router,
    ws_route.ws_router,
]