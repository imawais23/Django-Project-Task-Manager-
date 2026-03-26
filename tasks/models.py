from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class Project(models.Model):
    """
    Represents a project that contains multiple tasks.
    """
    name = models.CharField(max_length=200)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']  # Latest projects first by default

    def __str__(self):
        return self.name


class Task(models.Model):
    """
    Represents a task belonging to a specific project.
    """
    # Status choices — stored as short strings in DB, displayed as human-readable labels
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        IN_PROGRESS = 'in_progress', 'In Progress'
        COMPLETED = 'completed', 'Completed'

    # ForeignKey links each task to a project.
    # on_delete=CASCADE means: if the project is deleted, its tasks are deleted too.
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='tasks'  # lets us do project.tasks.all() from a Project instance
    )
    title = models.CharField(max_length=200)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    # priority 1 (lowest) to 5 (highest), validated server-side
    priority = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    due_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']  # Latest tasks first by default

    def __str__(self):
        return f"{self.title} [{self.project.name}]"
