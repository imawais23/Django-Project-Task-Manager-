from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter

from .models import Project, Task
from .serializers import ProjectSerializer, TaskSerializer
from .querysets import (
    get_annotated_projects,
    get_tasks_due_in_3_days,
    get_high_priority_incomplete_tasks,
    get_latest_5_tasks,
)


class ProjectViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Project CRUD operations.

    ModelViewSet automatically provides:
      list()    → GET  /api/projects/
      retrieve()→ GET  /api/projects/<id>/
      create()  → POST /api/projects/
      update()  → PUT  /api/projects/<id>/
      destroy() → DELETE /api/projects/<id>/

    We override get_queryset() to always return annotated projects
    (with total_tasks, completed_tasks, pending_tasks).
    """
    serializer_class = ProjectSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering_fields = ['created_at', 'name']
    ordering = ['-created_at']  # Default ordering: latest projects first

    def get_queryset(self):
        """
        Always return annotated projects so the serializer has access to
        total_tasks, completed_tasks, and pending_tasks.
        prefetch_related('tasks') is included inside get_annotated_projects().
        """
        return get_annotated_projects()

    @action(detail=True, methods=['get'], url_path='tasks')
    def tasks(self, request, pk=None):
        """
        Custom action: GET /api/projects/<id>/tasks/
        Returns all tasks belonging to a specific project.

        HOW @action WORKS:
        - detail=True means this operates on a single project (needs <id>).
        - url_path='tasks' defines the extra URL segment.
        - select_related('project') is already handled in the queryset.
        - Supports filtering by status/priority and ordering.
        """
        project = self.get_object()
        tasks = project.tasks.select_related('project').all()

        # Optional filtering by status or priority via query params
        # Example: /api/projects/1/tasks/?status=pending&priority=5
        task_status = request.query_params.get('status')
        priority = request.query_params.get('priority')

        if task_status:
            tasks = tasks.filter(status=task_status)
        if priority:
            tasks = tasks.filter(priority=priority)

        # Ordering support: ?ordering=-created_at or ?ordering=due_date
        ordering = request.query_params.get('ordering', '-created_at')
        tasks = tasks.order_by(ordering)

        serializer = TaskSerializer(tasks, many=True)
        return Response(serializer.data)


class TaskViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Task CRUD operations.

    Provides standard CRUD + two custom actions:
      - complete → PATCH /api/tasks/<id>/complete/
      - due_soon → GET   /api/tasks/due_soon/
      - high_priority → GET /api/tasks/high_priority/
      - latest → GET /api/tasks/latest/
    """
    serializer_class = TaskSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['status', 'priority', 'project']  # ?status=pending, ?priority=5
    ordering_fields = ['created_at', 'due_date', 'priority']
    ordering = ['-created_at']  # Default: latest tasks first

    def get_queryset(self):
        """
        Use select_related('project') to fetch linked project data in ONE
        database query instead of one query per task (avoids N+1 problem).
        """
        return Task.objects.select_related('project').all()

    @action(detail=True, methods=['patch'], url_path='complete')
    def complete(self, request, pk=None):
        """
        Custom action: PATCH /api/tasks/<id>/complete/
        Marks a specific task as 'completed' without needing to send the full task body.

        HOW IT WORKS:
        - get_object() fetches the task by its primary key (<id>).
        - We directly update the status field and call save().
        - Return the updated task data as the response.
        """
        task = self.get_object()
        task.status = Task.Status.COMPLETED
        task.save()
        serializer = self.get_serializer(task)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='due_soon')
    def due_soon(self, request):
        """
        Custom action: GET /api/tasks/due_soon/
        Returns tasks due in the next 3 days using our queryset function.
        detail=False means no <id> needed — operates on the whole task list.
        """
        tasks = get_tasks_due_in_3_days()
        serializer = self.get_serializer(tasks, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='high_priority')
    def high_priority(self, request):
        """
        Custom action: GET /api/tasks/high_priority/
        Returns high priority (>=4) non-completed tasks.
        """
        tasks = get_high_priority_incomplete_tasks()
        serializer = self.get_serializer(tasks, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='latest')
    def latest(self, request):
        """
        Custom action: GET /api/tasks/latest/
        Returns the 5 most recently created tasks.
        """
        tasks = get_latest_5_tasks()
        serializer = self.get_serializer(tasks, many=True)
        return Response(serializer.data)
