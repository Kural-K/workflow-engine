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
