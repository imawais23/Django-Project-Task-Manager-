from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProjectViewSet, TaskViewSet

# DefaultRouter automatically creates these URL patterns:
# GET    /api/projects/              → list all projects
# POST   /api/projects/              → create a project
# GET    /api/projects/<id>/         → retrieve one project
# PUT    /api/projects/<id>/         → update a project
# DELETE /api/projects/<id>/         → delete a project
# GET    /api/projects/<id>/tasks/   → list tasks in a project (custom @action)
#
# GET    /api/tasks/                 → list all tasks
# POST   /api/tasks/                 → create a task
# GET    /api/tasks/<id>/            → retrieve one task
# PATCH  /api/tasks/<id>/complete/   → mark task as completed (custom @action)
# GET    /api/tasks/due_soon/        → tasks due in next 3 days
# GET    /api/tasks/high_priority/   → high priority incomplete tasks
# GET    /api/tasks/latest/          → latest 5 tasks

router = DefaultRouter()
router.register(r'projects', ProjectViewSet, basename='project')
router.register(r'tasks', TaskViewSet, basename='task')

urlpatterns = [
    path('', include(router.urls)),
]
