"""
Run this from ANYWHERE:
  python setup_backend.py

It will create the full backend folder structure in the current directory.
"""
import os, sys

ROOT = os.path.join(os.getcwd(), "workflow-backend")

files = {}

files["requirements.txt"] = """\
django==4.2.17
djangorestframework==3.15.2
mongoengine==0.29.1
django-cors-headers==4.6.0
python-dotenv==1.0.1
"""

files[".env"] = """\
SECRET_KEY=your-secret-key-change-in-production
DEBUG=True
MONGODB_HOST=mongodb://localhost:27017/workflow_engine
"""

files["manage.py"] = """\
#!/usr/bin/env python
import os
import sys

def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError("Couldn't import Django.") from exc
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()
"""

files["core/__init__.py"] = ""

files["core/wsgi.py"] = """\
import os
from django.core.wsgi import get_wsgi_application
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
application = get_wsgi_application()
"""

files["core/settings.py"] = """\
from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-dev-key')
DEBUG = True
ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'workflows',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [], 'APP_DIRS': True,
    'OPTIONS': {'context_processors': ['django.template.context_processors.request']},
}]

WSGI_APPLICATION = 'core.wsgi.application'

import mongoengine
MONGODB_HOST = os.getenv('MONGODB_HOST', 'mongodb://localhost:27017/workflow_engine')
mongoengine.connect(host=MONGODB_HOST)

DATABASES = {}
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True
STATIC_URL = 'static/'
CORS_ALLOW_ALL_ORIGINS = True

REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': ['rest_framework.renderers.JSONRenderer'],
    'DEFAULT_PARSER_CLASSES': ['rest_framework.parsers.JSONParser'],
    'EXCEPTION_HANDLER': 'workflows.utils.custom_exception_handler',
}
"""

files["core/urls.py"] = """\
from django.urls import path, include
urlpatterns = [
    path('api/', include('workflows.urls')),
]
"""

files["workflows/__init__.py"] = ""

files["workflows/apps.py"] = """\
from django.apps import AppConfig
class WorkflowsConfig(AppConfig):
    name = 'workflows'
"""

files["workflows/utils.py"] = """\
from rest_framework.views import exception_handler
from rest_framework.response import Response

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is not None:
        return Response({'error': response.data}, status=response.status_code)
    return None
"""

files["workflows/models.py"] = """\
import uuid
from datetime import datetime
from mongoengine import (
    Document, EmbeddedDocument, StringField, IntField,
    BooleanField, DictField, ListField, DateTimeField,
    EmbeddedDocumentField
)

def gen_uuid():
    return str(uuid.uuid4())

class Workflow(Document):
    meta = {'collection': 'workflows'}
    id = StringField(primary_key=True, default=gen_uuid)
    name = StringField(required=True, max_length=255)
    description = StringField(default='')
    version = IntField(default=1)
    is_active = BooleanField(default=True)
    input_schema = DictField(default=dict)
    start_step_id = StringField(null=True, default=None)
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)

    def save(self, *args, **kwargs):
        self.updated_at = datetime.utcnow()
        return super().save(*args, **kwargs)

class Step(Document):
    meta = {'collection': 'steps'}
    STEP_TYPES = ('task', 'approval', 'notification')
    id = StringField(primary_key=True, default=gen_uuid)
    workflow_id = StringField(required=True)
    name = StringField(required=True, max_length=255)
    step_type = StringField(choices=STEP_TYPES, required=True)
    order = IntField(default=0)
    metadata = DictField(default=dict)
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)

    def save(self, *args, **kwargs):
        self.updated_at = datetime.utcnow()
        return super().save(*args, **kwargs)

class Rule(Document):
    meta = {'collection': 'rules'}
    id = StringField(primary_key=True, default=gen_uuid)
    step_id = StringField(required=True)
    condition = StringField(required=True)
    next_step_id = StringField(null=True, default=None)
    priority = IntField(default=10)
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)

    def save(self, *args, **kwargs):
        self.updated_at = datetime.utcnow()
        return super().save(*args, **kwargs)

class StepLog(EmbeddedDocument):
    step_id = StringField()
    step_name = StringField()
    step_type = StringField()
    evaluated_rules = ListField(DictField())
    selected_next_step = StringField(null=True)
    status = StringField()
    approver_id = StringField(null=True)
    error_message = StringField(null=True)
    started_at = DateTimeField()
    ended_at = DateTimeField(null=True)

class Execution(Document):
    meta = {'collection': 'executions'}
    STATUSES = ('pending', 'in_progress', 'completed', 'failed', 'canceled')
    id = StringField(primary_key=True, default=gen_uuid)
    workflow_id = StringField(required=True)
    workflow_version = IntField(required=True)
    status = StringField(choices=STATUSES, default='pending')
    data = DictField(default=dict)
    logs = ListField(EmbeddedDocumentField(StepLog))
    current_step_id = StringField(null=True, default=None)
    retries = IntField(default=0)
    triggered_by = StringField(default='anonymous')
    started_at = DateTimeField(default=datetime.utcnow)
    ended_at = DateTimeField(null=True)
"""

files["workflows/rule_engine.py"] = """\
import re, operator
from typing import Any

def _resolve(token, data):
    token = token.strip()
    if token in data:
        return data[token]
    if (token.startswith("'") and token.endswith("'")) or (token.startswith('"') and token.endswith('"')):
        return token[1:-1]
    try: return int(token)
    except ValueError: pass
    try: return float(token)
    except ValueError: pass
    if token.lower() == 'true': return True
    if token.lower() == 'false': return False
    return token

OPS = {'==': operator.eq, '!=': operator.ne, '<=': operator.le, '>=': operator.ge, '<': operator.lt, '>': operator.gt}

def _eval_string_fn(expr, data):
    m = re.match(r'(contains|startsWith|endsWith)\\(\\s*(\\w+)\\s*,\\s*(["\\''])(.*?)\\3\\s*\\)', expr.strip())
    if not m: raise ValueError(f"Invalid string function: {expr}")
    fn, field, _, val = m.group(1), m.group(2), m.group(3), m.group(4)
    fv = str(data.get(field, ''))
    if fn == 'contains': return val in fv
    if fn == 'startsWith': return fv.startswith(val)
    if fn == 'endsWith': return fv.endswith(val)
    return False

def _eval_comparison(expr, data):
    expr = expr.strip()
    if re.match(r'(contains|startsWith|endsWith)\\(', expr):
        return _eval_string_fn(expr, data)
    for op_str in ('==', '!=', '<=', '>=', '<', '>'):
        parts = expr.split(op_str, 1)
        if len(parts) == 2:
            left = _resolve(parts[0].strip(), data)
            right = _resolve(parts[1].strip(), data)
            try: left, right = float(left), float(right)
            except (TypeError, ValueError): left, right = str(left), str(right)
            return OPS[op_str](left, right)
    raise ValueError(f"Cannot parse: {expr}")

def _split_logical(expr, delimiter):
    depth, parts, current, i = 0, [], [], 0
    d_len = len(delimiter)
    while i < len(expr):
        if expr[i] == '(': depth += 1; current.append(expr[i])
        elif expr[i] == ')': depth -= 1; current.append(expr[i])
        elif depth == 0 and expr[i:i+d_len] == delimiter:
            parts.append(''.join(current).strip()); current = []; i += d_len; continue
        else: current.append(expr[i])
        i += 1
    parts.append(''.join(current).strip())
    return parts

def _eval_expr(expr, data):
    expr = expr.strip()
    if expr.startswith('(') and expr.endswith(')'): return _eval_expr(expr[1:-1], data)
    or_parts = _split_logical(expr, '||')
    if len(or_parts) > 1: return any(_eval_expr(p, data) for p in or_parts)
    and_parts = _split_logical(expr, '&&')
    if len(and_parts) > 1: return all(_eval_expr(p, data) for p in and_parts)
    return _eval_comparison(expr, data)

def evaluate_condition(condition, data):
    if condition.strip().upper() == 'DEFAULT': return True
    return _eval_expr(condition, data)

def evaluate_rules(rules, data):
    evaluated = []
    for rule in sorted(rules, key=lambda r: r.priority):
        try:
            result = evaluate_condition(rule.condition, data)
        except Exception as e:
            evaluated.append({"rule": rule.condition, "result": False, "error": str(e)}); continue
        evaluated.append({"rule": rule.condition, "result": result})
        if result:
            return {"matched_rule_id": str(rule.id), "condition": rule.condition, "next_step_id": rule.next_step_id, "evaluated": evaluated}
    return {"matched_rule_id": None, "condition": None, "next_step_id": None, "evaluated": evaluated}
"""

files["workflows/execution_engine.py"] = """\
from datetime import datetime
from .models import Execution, Step, Rule, StepLog
from .rule_engine import evaluate_rules

MAX_LOOP_ITERATIONS = 10

def _get_step(step_id):
    try: return Step.objects.get(id=step_id)
    except Step.DoesNotExist: return None

def _get_rules(step_id):
    return list(Rule.objects(step_id=step_id).order_by('priority'))

def _build_step_log(step, rule_result, status, error=None, approver_id=None):
    return StepLog(
        step_id=str(step.id), step_name=step.name, step_type=step.step_type,
        evaluated_rules=rule_result.get('evaluated', []),
        selected_next_step=rule_result.get('next_step_id'),
        status=status, approver_id=approver_id, error_message=error,
        started_at=datetime.utcnow(), ended_at=datetime.utcnow(),
    )

def run_execution(execution):
    execution.status = 'in_progress'
    execution.save()
    visited_counts = {}
    step_id = execution.current_step_id

    while step_id:
        visited_counts[step_id] = visited_counts.get(step_id, 0) + 1
        if visited_counts[step_id] > MAX_LOOP_ITERATIONS:
            execution.status = 'failed'
            execution.ended_at = datetime.utcnow()
            execution.save()
            return execution, f"Max loop iterations reached at step {step_id}"

        step = _get_step(step_id)
        if not step:
            execution.status = 'failed'; execution.ended_at = datetime.utcnow(); execution.save()
            return execution, f"Step {step_id} not found"

        rules = _get_rules(step_id)

        if step.step_type == 'approval':
            already_approved = any(log.step_id == step_id and log.status == 'completed' for log in execution.logs)
            if not already_approved:
                execution.current_step_id = step_id
                execution.status = 'in_progress'
                execution.save()
                pending_exists = any(log.step_id == step_id and log.status == 'pending' for log in execution.logs)
                if not pending_exists:
                    execution.logs.append(StepLog(
                        step_id=str(step.id), step_name=step.name, step_type=step.step_type,
                        evaluated_rules=[], selected_next_step=None, status='pending', started_at=datetime.utcnow(),
                    ))
                    execution.save()
                return execution, None

        if step.step_type == 'notification':
            print(f"[NOTIFICATION] {step.metadata}")

        rule_result = evaluate_rules(rules, execution.data)

        if rule_result['matched_rule_id'] is None and not rules:
            execution.logs.append(_build_step_log(step, rule_result, 'completed'))
            execution.status = 'completed'; execution.current_step_id = None
            execution.ended_at = datetime.utcnow(); execution.save()
            return execution, None

        if rule_result['matched_rule_id'] is None:
            execution.logs.append(_build_step_log(step, rule_result, 'failed', error='No rule matched and no DEFAULT rule'))
            execution.status = 'failed'; execution.ended_at = datetime.utcnow(); execution.save()
            return execution, 'No matching rule found'

        execution.logs.append(_build_step_log(step, rule_result, 'completed'))
        next_step_id = rule_result['next_step_id']
        execution.current_step_id = next_step_id
        execution.save()

        if next_step_id is None:
            execution.status = 'completed'; execution.ended_at = datetime.utcnow(); execution.save()
            return execution, None

        step_id = next_step_id

    execution.status = 'completed'; execution.ended_at = datetime.utcnow(); execution.save()
    return execution, None

def approve_step(execution, step_id, approver_id):
    step = _get_step(step_id)
    if not step: return None, f"Step {step_id} not found"
    rules = _get_rules(step_id)
    rule_result = evaluate_rules(rules, execution.data)
    execution.logs = [log for log in execution.logs if not (log.step_id == step_id and log.status == 'pending')]
    execution.logs.append(_build_step_log(step, rule_result, 'completed', approver_id=approver_id))
    next_step_id = rule_result.get('next_step_id')
    execution.current_step_id = next_step_id
    execution.save()
    if next_step_id is None:
        execution.status = 'completed'; execution.ended_at = datetime.utcnow(); execution.save()
        return execution, None
    return run_execution(execution)
"""

files["workflows/serializers.py"] = """\
from rest_framework import serializers

class WorkflowSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    name = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, default='', allow_blank=True)
    version = serializers.IntegerField(read_only=True)
    is_active = serializers.BooleanField(required=False, default=True)
    input_schema = serializers.DictField(required=False, default=dict)
    start_step_id = serializers.CharField(required=False, allow_null=True, default=None)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

    def create(self, validated_data):
        from .models import Workflow
        return Workflow(**validated_data).save()

    def update(self, instance, validated_data):
        instance.version += 1
        for k, v in validated_data.items(): setattr(instance, k, v)
        return instance.save()

class StepSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    workflow_id = serializers.CharField(read_only=True)
    name = serializers.CharField(max_length=255)
    step_type = serializers.ChoiceField(choices=['task', 'approval', 'notification'])
    order = serializers.IntegerField(required=False, default=0)
    metadata = serializers.DictField(required=False, default=dict)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

    def create(self, validated_data):
        from .models import Step
        return Step(**validated_data).save()

    def update(self, instance, validated_data):
        for k, v in validated_data.items(): setattr(instance, k, v)
        return instance.save()

class RuleSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    step_id = serializers.CharField(read_only=True)
    condition = serializers.CharField()
    next_step_id = serializers.CharField(required=False, allow_null=True, default=None)
    priority = serializers.IntegerField(required=False, default=10)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

    def create(self, validated_data):
        from .models import Rule
        return Rule(**validated_data).save()

    def update(self, instance, validated_data):
        for k, v in validated_data.items(): setattr(instance, k, v)
        return instance.save()

class StepLogSerializer(serializers.Serializer):
    step_id = serializers.CharField()
    step_name = serializers.CharField()
    step_type = serializers.CharField()
    evaluated_rules = serializers.ListField()
    selected_next_step = serializers.CharField(allow_null=True)
    status = serializers.CharField()
    approver_id = serializers.CharField(allow_null=True)
    error_message = serializers.CharField(allow_null=True)
    started_at = serializers.DateTimeField()
    ended_at = serializers.DateTimeField(allow_null=True)

class ExecutionSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    workflow_id = serializers.CharField(read_only=True)
    workflow_version = serializers.IntegerField(read_only=True)
    status = serializers.CharField(read_only=True)
    data = serializers.DictField(required=False, default=dict)
    logs = StepLogSerializer(many=True, read_only=True)
    current_step_id = serializers.CharField(read_only=True, allow_null=True)
    retries = serializers.IntegerField(read_only=True)
    triggered_by = serializers.CharField(required=False, default='anonymous')
    started_at = serializers.DateTimeField(read_only=True)
    ended_at = serializers.DateTimeField(read_only=True, allow_null=True)
"""

files["workflows/views.py"] = """\
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Workflow, Step, Rule, Execution
from .serializers import WorkflowSerializer, StepSerializer, RuleSerializer, ExecutionSerializer
from .execution_engine import run_execution, approve_step

def paginate(qs, request):
    page = int(request.query_params.get('page', 1))
    page_size = int(request.query_params.get('page_size', 10))
    total = qs.count()
    items = list(qs.skip((page - 1) * page_size).limit(page_size))
    return items, {'total': total, 'page': page, 'page_size': page_size}

class WorkflowListCreateView(APIView):
    def get(self, request):
        qs = Workflow.objects.all()
        search = request.query_params.get('search', '')
        if search: qs = qs.filter(name__icontains=search)
        active = request.query_params.get('is_active')
        if active is not None: qs = qs.filter(is_active=(active.lower() == 'true'))
        workflows, meta = paginate(qs, request)
        result = []
        for w in workflows:
            data = WorkflowSerializer(w).data
            data['step_count'] = Step.objects(workflow_id=str(w.id)).count()
            result.append(data)
        return Response({'data': result, 'meta': meta})

    def post(self, request):
        ser = WorkflowSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        workflow = ser.save()
        return Response(WorkflowSerializer(workflow).data, status=status.HTTP_201_CREATED)

class WorkflowDetailView(APIView):
    def _get(self, pk):
        try: return Workflow.objects.get(id=pk)
        except Workflow.DoesNotExist: return None

    def get(self, request, pk):
        w = self._get(pk)
        if not w: return Response({'error': 'Not found'}, status=404)
        data = WorkflowSerializer(w).data
        steps = Step.objects(workflow_id=pk).order_by('order')
        data['steps'] = StepSerializer(steps, many=True).data
        for sd in data['steps']:
            sd['rules'] = RuleSerializer(Rule.objects(step_id=sd['id']).order_by('priority'), many=True).data
        return Response(data)

    def put(self, request, pk):
        w = self._get(pk)
        if not w: return Response({'error': 'Not found'}, status=404)
        ser = WorkflowSerializer(w, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        return Response(WorkflowSerializer(ser.save()).data)

    def delete(self, request, pk):
        w = self._get(pk)
        if not w: return Response({'error': 'Not found'}, status=404)
        w.delete()
        return Response(status=204)

class StepListCreateView(APIView):
    def get(self, request, workflow_id):
        return Response(StepSerializer(Step.objects(workflow_id=workflow_id).order_by('order'), many=True).data)

    def post(self, request, workflow_id):
        try: Workflow.objects.get(id=workflow_id)
        except Workflow.DoesNotExist: return Response({'error': 'Workflow not found'}, status=404)
        ser = StepSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        step = Step(workflow_id=workflow_id, **ser.validated_data).save()
        return Response(StepSerializer(step).data, status=201)

class StepDetailView(APIView):
    def _get(self, pk):
        try: return Step.objects.get(id=pk)
        except Step.DoesNotExist: return None

    def put(self, request, pk):
        step = self._get(pk)
        if not step: return Response({'error': 'Not found'}, status=404)
        ser = StepSerializer(step, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        return Response(StepSerializer(ser.save()).data)

    def delete(self, request, pk):
        step = self._get(pk)
        if not step: return Response({'error': 'Not found'}, status=404)
        Rule.objects(step_id=pk).delete()
        step.delete()
        return Response(status=204)

class RuleListCreateView(APIView):
    def get(self, request, step_id):
        return Response(RuleSerializer(Rule.objects(step_id=step_id).order_by('priority'), many=True).data)

    def post(self, request, step_id):
        try: Step.objects.get(id=step_id)
        except Step.DoesNotExist: return Response({'error': 'Step not found'}, status=404)
        ser = RuleSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        rule = Rule(step_id=step_id, **ser.validated_data).save()
        return Response(RuleSerializer(rule).data, status=201)

class RuleDetailView(APIView):
    def _get(self, pk):
        try: return Rule.objects.get(id=pk)
        except Rule.DoesNotExist: return None

    def put(self, request, pk):
        rule = self._get(pk)
        if not rule: return Response({'error': 'Not found'}, status=404)
        ser = RuleSerializer(rule, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        return Response(RuleSerializer(ser.save()).data)

    def delete(self, request, pk):
        rule = self._get(pk)
        if not rule: return Response({'error': 'Not found'}, status=404)
        rule.delete()
        return Response(status=204)

class ExecuteWorkflowView(APIView):
    def post(self, request, workflow_id):
        try: workflow = Workflow.objects.get(id=workflow_id)
        except Workflow.DoesNotExist: return Response({'error': 'Not found'}, status=404)
        if not workflow.start_step_id: return Response({'error': 'No start step defined'}, status=400)
        execution = Execution(
            workflow_id=workflow_id, workflow_version=workflow.version,
            data=request.data.get('data', {}), triggered_by=request.data.get('triggered_by', 'anonymous'),
            current_step_id=workflow.start_step_id,
        ).save()
        execution, error = run_execution(execution)
        if error: return Response({'error': error, 'execution': ExecutionSerializer(execution).data}, status=400)
        return Response(ExecutionSerializer(execution).data, status=201)

class ExecutionDetailView(APIView):
    def get(self, request, pk):
        try: ex = Execution.objects.get(id=pk)
        except Execution.DoesNotExist: return Response({'error': 'Not found'}, status=404)
        return Response(ExecutionSerializer(ex).data)

class ExecutionListView(APIView):
    def get(self, request):
        qs = Execution.objects.all().order_by('-started_at')
        if request.query_params.get('workflow_id'): qs = qs.filter(workflow_id=request.query_params['workflow_id'])
        if request.query_params.get('status'): qs = qs.filter(status=request.query_params['status'])
        executions, meta = paginate(qs, request)
        return Response({'data': ExecutionSerializer(executions, many=True).data, 'meta': meta})

class CancelExecutionView(APIView):
    def post(self, request, pk):
        try: ex = Execution.objects.get(id=pk)
        except Execution.DoesNotExist: return Response({'error': 'Not found'}, status=404)
        if ex.status not in ('pending', 'in_progress'): return Response({'error': f'Cannot cancel: {ex.status}'}, status=400)
        from datetime import datetime
        ex.status = 'canceled'; ex.ended_at = datetime.utcnow(); ex.save()
        return Response(ExecutionSerializer(ex).data)

class RetryExecutionView(APIView):
    def post(self, request, pk):
        try: ex = Execution.objects.get(id=pk)
        except Execution.DoesNotExist: return Response({'error': 'Not found'}, status=404)
        if ex.status != 'failed': return Response({'error': 'Only failed executions can be retried'}, status=400)
        ex.status = 'in_progress'; ex.retries += 1; ex.save()
        ex, error = run_execution(ex)
        if error: return Response({'error': error, 'execution': ExecutionSerializer(ex).data}, status=400)
        return Response(ExecutionSerializer(ex).data)

class ApproveStepView(APIView):
    def post(self, request, pk):
        try: ex = Execution.objects.get(id=pk)
        except Execution.DoesNotExist: return Response({'error': 'Not found'}, status=404)
        step_id = request.data.get('step_id') or ex.current_step_id
        approver_id = request.data.get('approver_id', 'anonymous')
        ex, error = approve_step(ex, step_id, approver_id)
        if error: return Response({'error': error}, status=400)
        return Response(ExecutionSerializer(ex).data)
"""

files["workflows/urls.py"] = """\
from django.urls import path
from . import views

urlpatterns = [
    path('workflows', views.WorkflowListCreateView.as_view()),
    path('workflows/<str:pk>', views.WorkflowDetailView.as_view()),
    path('workflows/<str:workflow_id>/steps', views.StepListCreateView.as_view()),
    path('workflows/<str:workflow_id>/execute', views.ExecuteWorkflowView.as_view()),
    path('steps/<str:pk>', views.StepDetailView.as_view()),
    path('steps/<str:step_id>/rules', views.RuleListCreateView.as_view()),
    path('rules/<str:pk>', views.RuleDetailView.as_view()),
    path('executions', views.ExecutionListView.as_view()),
    path('executions/<str:pk>', views.ExecutionDetailView.as_view()),
    path('executions/<str:pk>/cancel', views.CancelExecutionView.as_view()),
    path('executions/<str:pk>/retry', views.RetryExecutionView.as_view()),
    path('executions/<str:pk>/approve', views.ApproveStepView.as_view()),
]
"""

files["seed_data.py"] = """\
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from workflows.models import Workflow, Step, Rule

Workflow.objects.delete()
Step.objects.delete()
Rule.objects.delete()

w1 = Workflow(
    name='Expense Approval',
    description='Multi-level expense approval based on amount and priority.',
    input_schema={
        'amount':     {'type': 'number', 'required': True},
        'country':    {'type': 'string', 'required': True},
        'department': {'type': 'string', 'required': False},
        'priority':   {'type': 'string', 'required': True, 'allowed_values': ['High', 'Medium', 'Low']},
    }
).save()

s1 = Step(workflow_id=str(w1.id), name='Manager Approval',     step_type='approval',     order=1, metadata={'assignee_email': 'manager@example.com'}).save()
s2 = Step(workflow_id=str(w1.id), name='Finance Notification', step_type='notification', order=2, metadata={'notification_channel': 'email'}).save()
s3 = Step(workflow_id=str(w1.id), name='CEO Approval',         step_type='approval',     order=3, metadata={'assignee_email': 'ceo@example.com'}).save()
s4 = Step(workflow_id=str(w1.id), name='Task Rejection',       step_type='task',         order=4, metadata={'action': 'reject'}).save()
s5 = Step(workflow_id=str(w1.id), name='Completion',           step_type='task',         order=5, metadata={'action': 'complete'}).save()

w1.start_step_id = str(s1.id); w1.save()

Rule(step_id=str(s1.id), condition="amount > 100 && country == 'US' && priority == 'High'", next_step_id=str(s3.id), priority=1).save()
Rule(step_id=str(s1.id), condition="amount <= 100 || department == 'HR'",                   next_step_id=str(s2.id), priority=2).save()
Rule(step_id=str(s1.id), condition="priority == 'Low' && country != 'US'",                  next_step_id=str(s4.id), priority=3).save()
Rule(step_id=str(s1.id), condition='DEFAULT',                                                next_step_id=str(s4.id), priority=4).save()
Rule(step_id=str(s2.id), condition='DEFAULT', next_step_id=str(s5.id), priority=1).save()
Rule(step_id=str(s3.id), condition='DEFAULT', next_step_id=str(s5.id), priority=1).save()
Rule(step_id=str(s4.id), condition='DEFAULT', next_step_id=None,       priority=1).save()
Rule(step_id=str(s5.id), condition='DEFAULT', next_step_id=None,       priority=1).save()

print(f'Workflow 1 created: Expense Approval')

w2 = Workflow(
    name='Employee Onboarding',
    description='Onboarding workflow for new hires.',
    input_schema={
        'employee_name': {'type': 'string', 'required': True},
        'department':    {'type': 'string', 'required': True},
        'role':          {'type': 'string', 'required': True},
        'is_remote':     {'type': 'boolean', 'required': False},
    }
).save()

t1 = Step(workflow_id=str(w2.id), name='Send Welcome Email',        step_type='notification', order=1, metadata={'notification_channel': 'email'}).save()
t2 = Step(workflow_id=str(w2.id), name='IT Setup Approval',         step_type='approval',     order=2, metadata={'assignee_email': 'it@example.com'}).save()
t3 = Step(workflow_id=str(w2.id), name='Provision Remote Equipment', step_type='task',        order=3, metadata={'action': 'provision_remote'}).save()
t4 = Step(workflow_id=str(w2.id), name='Assign Office Desk',        step_type='task',         order=4, metadata={'action': 'assign_desk'}).save()
t5 = Step(workflow_id=str(w2.id), name='Onboarding Complete',       step_type='notification', order=5, metadata={'notification_channel': 'slack'}).save()

w2.start_step_id = str(t1.id); w2.save()

Rule(step_id=str(t1.id), condition='DEFAULT',            next_step_id=str(t2.id), priority=1).save()
Rule(step_id=str(t2.id), condition='is_remote == True',  next_step_id=str(t3.id), priority=1).save()
Rule(step_id=str(t2.id), condition='is_remote == False', next_step_id=str(t4.id), priority=2).save()
Rule(step_id=str(t2.id), condition='DEFAULT',            next_step_id=str(t4.id), priority=3).save()
Rule(step_id=str(t3.id), condition='DEFAULT', next_step_id=str(t5.id), priority=1).save()
Rule(step_id=str(t4.id), condition='DEFAULT', next_step_id=str(t5.id), priority=1).save()
Rule(step_id=str(t5.id), condition='DEFAULT', next_step_id=None,       priority=1).save()

print(f'Workflow 2 created: Employee Onboarding')
print('Done! 2 workflows seeded.')
"""

# ── write all files ────────────────────────────────────────────────────────────
for rel_path, content in files.items():
    full_path = os.path.join(ROOT, rel_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, 'w', encoding='utf-8') as f:
        f.write(content)

print(f"\n✅ Backend created at: {ROOT}")
print("\nNext steps:")
print(f"  cd workflow-backend")
print(f"  pip install -r requirements.txt")
print(f"  python manage.py runserver")
print(f"  python seed_data.py   (in a second terminal)")
