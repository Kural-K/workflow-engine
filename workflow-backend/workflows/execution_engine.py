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
