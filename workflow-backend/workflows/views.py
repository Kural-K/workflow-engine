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
