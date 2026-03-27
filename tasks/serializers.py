from rest_framework import serializers
from .models import Project, Task


class TaskSerializer(serializers.ModelSerializer):
    """
    Converts Task model instances ↔ JSON.

    - 'project_name' is a read-only field that shows the project's name
      instead of just the project's ID number. Makes the API response much
      more readable.
      
    project_name = serializers.CharField(source='project.name', read_only=True)

    class Meta:
        model = Task
        fields = [
            'id',
            'project',
            'project_name',
            'title',
            'status',
            'priority',
            'due_date',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class ProjectSerializer(serializers.ModelSerializer):
    """
    Converts Project model instances ↔ JSON.

    Includes 4 annotated fields (added by our QuerySets):
    - total_tasks, completed_tasks, in_progress_tasks, pending_tasks

    These fields don't exist on the model itself — they are computed
    by the database via annotate() and attached to each project object.
    We declare them here so DRF knows to include them in the response.
    Check: completed + in_progress + pending = total.
    """
    total_tasks = serializers.IntegerField(read_only=True, default=0)
    completed_tasks = serializers.IntegerField(read_only=True, default=0)
    in_progress_tasks = serializers.IntegerField(read_only=True, default=0)
    pending_tasks = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Project
        fields = [
            'id',
            'name',
            'description',
            'created_at',
            'total_tasks',
            'completed_tasks',
            'in_progress_tasks',
            'pending_tasks',
        ]
        read_only_fields = ['id', 'created_at']
