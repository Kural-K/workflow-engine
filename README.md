# FlowEngine — Workflow Automation System

A full-stack workflow automation system built with Django, React, and MongoDB. Design workflows, define dynamic rules, execute processes, and track every step.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11 + Django 4.2 + Django REST Framework |
| Database | MongoDB (via MongoEngine) |
| Frontend | React 18 + React Router |
| Rule Engine | Custom-built expression evaluator |

---

## Project Structure

```
workflow-engine/
├── workflow-backend/         # Django backend
│   ├── core/                 # Django project settings & URLs
│   │   ├── settings.py
│   │   └── urls.py
│   ├── workflows/            # Main app
│   │   ├── models.py         # MongoEngine models
│   │   ├── views.py          # API views
│   │   ├── urls.py           # API routes
│   │   ├── serializers.py    # DRF serializers
│   │   ├── rule_engine.py    # Dynamic rule evaluator
│   │   └── execution_engine.py # Workflow executor
│   ├── manage.py
│   ├── seed_data.py          # Sample workflow data
│   └── requirements.txt
└── workflow-frontend/        # React frontend
    └── src/
        ├── api/client.js     # Axios API client
        ├── pages/
        │   ├── WorkflowList.js    # Workflow list page
        │   ├── WorkflowEditor.js  # Workflow + step + rule editor
        │   ├── ExecutionPage.js   # Run workflows + view logs
        │   └── AuditLog.js        # Execution history
        ├── App.js
        └── index.css
```

---

## Prerequisites

- Python 3.11+
- Node.js 18+
- MongoDB 6.0+ (running on port 27017)

---

## Setup & Installation

### 1. Start MongoDB

```bash
# Windows
net start MongoDB

# Mac
brew services start mongodb-community

# Linux
sudo systemctl start mongod
```

### 2. Backend Setup

```bash
cd workflow-backend

# Install dependencies
pip install -r requirements.txt

# Run database migrations (SQLite for Django internals)
python manage.py migrate

# Start the server
python manage.py runserver
```

Backend runs at: `http://localhost:8000`

### 3. Seed Sample Data

In a new terminal:

```bash
cd workflow-backend
python seed_data.py
```

This creates 2 sample workflows:
- **Expense Approval** — multi-level approval based on amount, country, priority
- **Employee Onboarding** — IT setup and equipment provisioning flow

### 4. Frontend Setup

```bash
cd workflow-frontend

# Install dependencies
npm install

# Start the app
npm start
```

Frontend runs at: `http://localhost:3000`

---

## Environment Variables

### Backend (`workflow-backend/.env`)
```
SECRET_KEY=your-secret-key-change-in-production
DEBUG=True
MONGODB_HOST=mongodb://localhost:27017/workflow_engine
```

### Frontend (`workflow-frontend/.env`)
```
REACT_APP_API_URL=http://localhost:8000/api
```

---

## API Endpoints

### Workflows
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/workflows` | List all workflows (search, pagination) |
| POST | `/api/workflows` | Create a new workflow |
| GET | `/api/workflows/:id` | Get workflow with steps & rules |
| PUT | `/api/workflows/:id` | Update workflow (increments version) |
| DELETE | `/api/workflows/:id` | Delete workflow |

### Steps
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/workflows/:id/steps` | List steps for a workflow |
| POST | `/api/workflows/:id/steps` | Add a step |
| PUT | `/api/steps/:id` | Update a step |
| DELETE | `/api/steps/:id` | Delete a step |

### Rules
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/steps/:id/rules` | List rules for a step |
| POST | `/api/steps/:id/rules` | Add a rule |
| PUT | `/api/rules/:id` | Update a rule |
| DELETE | `/api/rules/:id` | Delete a rule |

### Executions
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/workflows/:id/execute` | Start a workflow execution |
| GET | `/api/executions` | List all executions |
| GET | `/api/executions/:id` | Get execution status & logs |
| POST | `/api/executions/:id/approve` | Approve a pending step |
| POST | `/api/executions/:id/cancel` | Cancel an execution |
| POST | `/api/executions/:id/retry` | Retry a failed execution |

---

## Rule Engine

Rules are evaluated at runtime using a custom expression evaluator.

### Supported Syntax

| Type | Operators |
|------|-----------|
| Comparison | `==`, `!=`, `<`, `>`, `<=`, `>=` |
| Logical | `&&` (AND), `\|\|` (OR) |
| String functions | `contains(field, "val")`, `startsWith(field, "pre")`, `endsWith(field, "suf")` |
| Fallback | `DEFAULT` — always matches, used as catch-all |

### Example Rules

```
amount > 100 && country == 'US' && priority == 'High'  → CEO Approval
amount <= 100 || department == 'HR'                    → Finance Notification
priority == 'Low' && country != 'US'                   → Task Rejection
DEFAULT                                                 → Task Rejection
```

Rules are evaluated in **priority order** (lowest number = highest priority). The first matching rule wins.

### Loop Detection
The engine tracks step visit counts and terminates with a `failed` status if any step is visited more than **10 times** (configurable via `MAX_LOOP_ITERATIONS` in `execution_engine.py`).

---

## Sample Workflows

### 1. Expense Approval

**Input Schema:**
```json
{
  "amount": 250,
  "country": "US",
  "department": "Finance",
  "priority": "High"
}
```

**Steps:**
1. Manager Approval (approval) — pauses for human approval
2. Finance Notification (notification) — auto-sends notification
3. CEO Approval (approval) — pauses for CEO approval
4. Task Rejection (task) — rejects the expense
5. Completion (task) — marks expense as approved

**Flow with above input:**
```
Manager Approval → [rule: amount <= 100 || department == 'HR' ✓] 
→ Finance Notification → Completion ✅
```

**Execution Log Example:**
```json
{
  "step_name": "Manager Approval",
  "step_type": "approval",
  "evaluated_rules": [
    {"rule": "amount > 100 && country == 'US' && priority == 'High'", "result": false},
    {"rule": "amount <= 100 || department == 'HR'", "result": true}
  ],
  "selected_next_step": "Finance Notification",
  "status": "completed",
  "approver_id": "user-001"
}
```

### 2. Employee Onboarding

**Input Schema:**
```json
{
  "employee_name": "John Doe",
  "department": "Engineering",
  "role": "Developer",
  "is_remote": true
}
```

**Flow:**
```
Send Welcome Email → IT Setup Approval → [is_remote == True] 
→ Provision Remote Equipment → Onboarding Complete ✅
```

---

## Workflow Engine Design

```
User submits input data
        ↓
Execution created (status: pending)
        ↓
Engine starts at start_step_id
        ↓
For each step:
  ├── If APPROVAL → pause, wait for human action
  ├── If NOTIFICATION → auto-complete, continue
  └── If TASK → auto-complete, continue
        ↓
Evaluate rules in priority order
        ↓
First matching rule → go to next_step_id
        ↓
If next_step_id is null → COMPLETED
If no rule matches → FAILED
```

---

## UI Features

- **Workflow List** — search, filter, paginate, create/edit/delete/run
- **Workflow Editor** — edit name, description, input schema, manage steps and rules inline
- **Step Rule Editor** — add/edit/delete rules with condition syntax, set priorities
- **Execution Page** — run workflows with JSON input, approve pending steps, view live logs
- **Audit Log** — filter executions by workflow/status, view detailed logs

---

## Running Everything (Quick Start)

Open 3 terminals:

```bash
# Terminal 1 — MongoDB
net start MongoDB

# Terminal 2 — Backend
cd workflow-backend
python manage.py runserver

# Terminal 3 — Frontend
cd workflow-frontend
npm start
```

Then open `http://localhost:3000` 🚀
