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
