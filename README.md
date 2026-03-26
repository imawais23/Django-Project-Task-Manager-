# Django Project & Task Manager

A clean Django backend system to manage **Projects** and **Tasks**, built with Django REST Framework. This project demonstrates clean model design, efficient ORM QuerySets, and a fully functional REST API.

---

## Tech Stack

- **Python 3.x**
- **Django 4.2**
- **Django REST Framework 3.15**
- **django-filter 24.x**
- **SQLite** (default, no extra setup needed)

---

## Setup Instructions

### 1. Clone the repository
```bash
git clone <your-repo-url>
cd Django_task
```

### 2. Create and activate a virtual environment
```bash
python3 -m venv venv
source venv/bin/activate      # Linux / macOS
venv\Scripts\activate         # Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Run database migrations
```bash
python manage.py migrate
```

### 5. Create a superuser (for Admin panel)
```bash
python manage.py createsuperuser
```

### 6. Start the development server
```bash
python manage.py runserver
```

The API will be available at: **http://127.0.0.1:8000/api/**  
The Admin panel at: **http://127.0.0.1:8000/admin/**

---

## API Endpoints

| Method | URL | Description |
|--------|-----|-------------|
| GET | `/api/projects/` | List all projects (with task counts) |
| POST | `/api/projects/` | Create a new project |
| GET | `/api/projects/<id>/` | Retrieve a single project |
| GET | `/api/projects/<id>/tasks/` | List all tasks in a project |
| GET | `/api/tasks/` | List all tasks |
| POST | `/api/tasks/` | Create a new task |
| PATCH | `/api/tasks/<id>/complete/` | Mark a task as completed |
| GET | `/api/tasks/due_soon/` | Tasks due in the next 3 days |
| GET | `/api/tasks/high_priority/` | High priority (≥4) incomplete tasks |
| GET | `/api/tasks/latest/` | Latest 5 created tasks |

### Filtering & Ordering (Bonus)
```
GET /api/tasks/?status=pending
GET /api/tasks/?priority=5
GET /api/tasks/?status=in_progress&ordering=-due_date
GET /api/projects/<id>/tasks/?status=completed&ordering=priority
```

---

## QuerySet Explanations

All QuerySets live in `tasks/querysets.py`. Here is what each one does and how it works:

---

### 1. `get_projects_with_total_tasks()`
```python
Project.objects.annotate(total_tasks=Count('tasks'))
```
**What:** Adds a `total_tasks` count to every project.  
**How:** `annotate()` adds a computed field using SQL `COUNT`. `Count('tasks')` counts Task rows linked via the ForeignKey's `related_name='tasks'`.

---

### 2. `get_projects_with_completed_tasks()`
```python
Project.objects.annotate(
    completed_tasks=Count('tasks', filter=Q(tasks__status='completed'))
)
```
**What:** Counts only completed tasks per project.  
**How:** `Q()` allows filtering inside an annotation. `Count(..., filter=Q(...))` translates to SQL `COUNT(CASE WHEN status='completed' THEN 1 END)`.

---

### 3. `get_tasks_due_in_3_days()`
```python
Task.objects.select_related('project').filter(
    due_date__range=[today, today + timedelta(days=3)]
)
```
**What:** Returns tasks due between today and 3 days from now.  
**How:** `__range` performs a SQL `BETWEEN` query. `select_related('project')` fetches the project in the same JOIN query — no N+1 problem.

---

### 4. `get_high_priority_incomplete_tasks()`
```python
Task.objects.select_related('project').filter(priority__gte=4).exclude(status='completed')
```
**What:** Returns tasks with priority 4 or 5 that are not completed.  
**How:** `__gte` = "greater than or equal to". `exclude()` is the opposite of `filter()` — it removes matching rows.

---

### 5. `get_projects_with_no_tasks()`
```python
Project.objects.annotate(total_tasks=Count('tasks')).filter(total_tasks=0)
```
**What:** Projects that have zero tasks.  
**How:** Annotate first, then filter on the annotation. Django translates this into a `HAVING COUNT(...) = 0` SQL clause.

---

### 6. `get_latest_5_tasks()`
```python
Task.objects.select_related('project').order_by('-created_at')[:5]
```
**What:** The 5 most recently created tasks.  
**How:** `-created_at` sorts descending (newest first). Python slice `[:5]` maps to SQL `LIMIT 5`.

---

### 7. `get_annotated_projects()`
```python
Project.objects.prefetch_related('tasks').annotate(
    total_tasks=Count('tasks'),
    completed_tasks=Count('tasks', filter=Q(tasks__status='completed')),
    in_progress_tasks=Count('tasks', filter=Q(tasks__status='in_progress')),
    pending_tasks=Count('tasks', filter=Q(tasks__status='pending')),
)
```
**What:** All task status counts are computed in a single optimized query — used by the main project list API.  
**How:** Multiple `Count` annotations run as a single optimized SQL query. `prefetch_related('tasks')` pre-loads all tasks in a second query to avoid N+1 when iterating project tasks.

#### 🔹 Status Aggregation Note
**Why `in_progress_tasks` was included:**
The task model defines three statuses: `pending`, `in_progress`, and `completed`. While the original requirement specifically asked for `pending` and `completed` counts only, I included `in_progress_tasks` to ensure complete and consistent aggregation of all task states. Without this, the total task count would not match the sum of categorized tasks (e.g., if a project has 1 pending, 1 in progress, and 1 completed task, the total is 3, but the strictly requested categories would only sum to 2). This addition ensures mathematical consistency across the API response: `completed + in_progress + pending = total`.

---

## Project Structure

```
Django_task/
├── project_manager/
│   ├── settings.py       # Django config + DRF config
│   └── urls.py           # Root URL routing
├── tasks/
│   ├── models.py         # Project & Task models
│   ├── querysets.py      # All QuerySet operations
│   ├── serializers.py    # DRF serializers
│   ├── views.py          # ViewSets (API logic)
│   ├── urls.py           # App URL routing via DRF Router
│   └── admin.py          # Django Admin setup
├── requirements.txt
└── README.md
```

---

## Key Design Decisions

| Decision | Why |
|---|---|
| `querysets.py` separate file | Separation of concerns — DB logic stays out of views |
| ViewSets over APIViews | Less boilerplate, router auto-generates URLs |
| `select_related` on Tasks | Avoids N+1 DB queries when accessing `task.project` |
| `prefetch_related` on Projects | Efficiently pre-loads all related tasks |
| `TextChoices` for status | Type-safe, self-documenting status values |
| `MinValueValidator/MaxValueValidator` | Server-side enforcement of priority 1–5 range |

---

## Learnings & Technical Challenges Overcome

Throughout the development of this project, several interesting technical challenges were addressed to ensure a robust, production-ready implementation:

1. **Status Aggregation Consistency**
   * **Challenge:** The project required tracking `total_tasks` and breaking them down by status. However, annotating only `pending` and `completed` (as initially inferred) left a mathematical gap for `in_progress` tasks.
   * **Solution:** Proactively added the `in_progress_tasks` annotation. This guarantees data integrity and ensures that API consumers receive a mathematically sound representation of the project's task breakdown (`completed + in_progress + pending = total_tasks`).

2. **Accurate Date Boundaries for `due_soon` Tasks**
   * **Challenge:** Extracting tasks due in "the next 3 days" resulted in standard UTC timezone discrepancies. When local time crossed midnight before UTC, tasks due "yesterday" locally were still considered "today" by the server.
   * **Solution:** Addressed the timezone bug by explicitly configuring `TIME_ZONE = 'Asia/Karachi'` and utilizing Django's `timezone.localdate()` instead of the standard `timezone.now().date()`, guaranteeing strict alignment with local business hours.

3. **Optimizing Database Queries (The N+1 Problem)**
   * **Challenge:** Using DRF serializers to fetch tasks alongside their related project data triggered an N+1 query issue, causing an extra database hit for every single task.
   * **Solution:** Implemented `select_related('project')` for forward foreign key relationships and `prefetch_related('tasks')` for reverse relationships within the custom QuerySets, minimizing database roundtrips and optimizing response times.
