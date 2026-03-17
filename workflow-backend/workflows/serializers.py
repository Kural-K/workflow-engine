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
