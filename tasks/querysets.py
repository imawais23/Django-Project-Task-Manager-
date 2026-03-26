"""
querysets.py — Centralized QuerySet operations for Projects and Tasks.

Each function is a self-contained database query using Django ORM.
These are imported into views.py to keep views clean.
"""

from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta

from .models import Project, Task


# ──────────────────────────────────────────────
#  PROJECT QUERYSETS
# ──────────────────────────────────────────────

def get_projects_with_total_tasks():
    """
    Returns all projects annotated with the total number of tasks each project has.

    HOW IT WORKS:
    - annotate() adds a computed column called 'total_tasks' to each project row.
    - Count('tasks') counts how many Task rows are linked to each project
      via the 'tasks' related_name (ForeignKey).
    """
    return Project.objects.annotate(
        total_tasks=Count('tasks')
    )


def get_projects_with_completed_tasks():
    """
    Returns all projects annotated with the count of COMPLETED tasks only.

    HOW IT WORKS:
    - Count('tasks', filter=Q(...)) counts only tasks where status is 'completed'.
    - Q() is Django's way of writing complex filter conditions inside annotations.
    """
    return Project.objects.annotate(
        completed_tasks=Count(
            'tasks',
            filter=Q(tasks__status='completed')
        )
    )


def get_projects_with_no_tasks():
    """
    Returns projects that have zero tasks assigned to them.

    HOW IT WORKS:
    - First annotate total_tasks, then filter those where total_tasks equals 0.
    """
    return Project.objects.annotate(
        total_tasks=Count('tasks')
    ).filter(total_tasks=0)


def get_annotated_projects():
    """
    Returns all projects with FOUR annotations at once:
      - total_tasks      → total tasks in project
      - completed_tasks  → tasks with status = 'completed'
      - in_progress_tasks→ tasks with status = 'in_progress'
      - pending_tasks    → tasks with status = 'pending'

    HOW IT WORKS:
    - Multiple annotate() calls can be chained, or all put inside one annotate().
    - Each uses Count with a Q filter to target a specific status value.
    - prefetch_related('tasks') reduces DB queries when accessing project.tasks later.
    - Check: completed + in_progress + pending should always equal total_tasks.
    """
    return Project.objects.prefetch_related('tasks').annotate(
        total_tasks=Count('tasks'),
        completed_tasks=Count(
            'tasks',
            filter=Q(tasks__status='completed')
        ),
        in_progress_tasks=Count(
            'tasks',
            filter=Q(tasks__status='in_progress')
        ),
        pending_tasks=Count(
            'tasks',
            filter=Q(tasks__status='pending')
        )
    )


# ──────────────────────────────────────────────
#  TASK QUERYSETS
# ──────────────────────────────────────────────

def get_tasks_due_in_3_days():
    """
    Returns all tasks whose due_date falls within the next 3 days (including today).

    HOW IT WORKS:
    - timezone.localdate() gets TODAY's date in the LOCAL timezone (Asia/Karachi).
      ⚠️  We do NOT use timezone.now().date() because that returns UTC date,
          which can differ from local date by hours — causing yesterday's tasks
          to show up as "due soon".
    - timedelta(days=3) adds 3 days to get the deadline boundary.
    - __range performs a SQL BETWEEN query: due_date >= today AND due_date <= today+3
    - select_related('project') fetches the linked project in ONE query instead of N queries.
    """
    today = timezone.localdate()          # ✅ Local date — respects TIME_ZONE setting
    deadline = today + timedelta(days=3)
    return Task.objects.select_related('project').filter(
        due_date__range=[today, deadline]
    )


def get_high_priority_incomplete_tasks():
    """
    Returns tasks that are high priority (priority >= 4) AND not yet completed.

    HOW IT WORKS:
    - priority__gte=4 means priority Greater Than or Equal to 4 (so 4 or 5).
    - ~Q(status='completed') is the NOT operator — excludes completed tasks.
    - select_related('project') avoids extra DB hits when accessing task.project.
    """
    return Task.objects.select_related('project').filter(
        priority__gte=4
    ).exclude(
        status='completed'
    )


def get_latest_5_tasks():
    """
    Returns the 5 most recently created tasks.

    HOW IT WORKS:
    - order_by('-created_at') sorts by created_at descending (newest first).
    - [:5] is Python slicing — Django translates this to SQL LIMIT 5.
    """
    return Task.objects.select_related('project').order_by('-created_at')[:5]
