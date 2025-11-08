import logging

from core.models import User
from core.service_signals import ServiceSignalBindType
from core.signals import bind_service_signal
from tasks_management.models import Task

from contribution_plan.apps import ContributionPlanConfig
from contribution_plan.services import PaymentPlan as PaymentPlanService

logger = logging.getLogger(__name__)


def bind_service_signals():
    def on_task_complete_payment_plan_create(**kwargs):
        try:
            result = kwargs.get('result', None)
            if not result or not result.get('success'):
                logger.debug("on_task_complete_payment_plan_create: result not success or missing")
                return []
            task = result['data']['task']
            logger.info(f"on_task_complete_payment_plan_create: processing task {task.get('id')}, business_event={task.get('business_event')}, status={task.get('status')}")
            
            if task['business_event'] != ContributionPlanConfig.payment_plan_create_event:
                logger.debug(f"on_task_complete_payment_plan_create: business_event mismatch. Expected {ContributionPlanConfig.payment_plan_create_event}, got {task.get('business_event')}")
                return []
            if task['status'] != Task.Status.COMPLETED:
                logger.debug(f"on_task_complete_payment_plan_create: task status is {task.get('status')}, not COMPLETED")
                return []

            user = User.objects.get(id=result['data']['user']['id'])
            task_data = task.get('data', {})
            logger.info(f"on_task_complete_payment_plan_create: task data structure: {list(task_data.keys())}")
            
            # Les données peuvent être dans incoming_data ou directement dans data
            data = task_data.get('incoming_data', task_data)
            if not data:
                logger.error("on_task_complete_payment_plan_create: No incoming_data or data found in task")
                return [{"message": "No data found in task"}]

            logger.info(f"on_task_complete_payment_plan_create: Creating PaymentPlan with data keys: {list(data.keys())}")

            # Align dynamic ContentType input if provided as benefit_plan_type__model
            benefit_plan_type_model = data.pop('benefit_plan_type__model', None)
            if benefit_plan_type_model:
                from django.contrib.contenttypes.models import ContentType
                content_type = ContentType.objects.get(model=str(benefit_plan_type_model).lower())
                # Validate object existence if id provided
                model_id = data.get('benefit_plan_id')
                if model_id is not None:
                    content_type.get_object_for_this_type(pk=model_id)
                data['benefit_plan_type'] = content_type

            result = PaymentPlanService(user).create(data)
            logger.info(f"on_task_complete_payment_plan_create: PaymentPlanService.create returned: success={result.get('success')}")
            if not result.get('success'):
                logger.error(f"on_task_complete_payment_plan_create: PaymentPlanService.create failed: {result.get('message')}")
                return [{"message": result.get('message', 'Failed to create PaymentPlan')}]
            return []
        except Exception as exc:
            logger.error("Error while executing on_task_complete_payment_plan_create", exc_info=exc)
            return [{"message": str(exc)}]

    bind_service_signal(
        'task_service.complete_task',
        on_task_complete_payment_plan_create,
        bind_type=ServiceSignalBindType.AFTER
    )

    def on_task_complete_payment_plan_update(**kwargs):
        try:
            result = kwargs.get('result', None)
            if not result or not result.get('success'):
                return
            task = result['data']['task']
            if task['business_event'] != ContributionPlanConfig.payment_plan_update_event:
                return
            if task['status'] != Task.Status.COMPLETED:
                return
            user = User.objects.get(id=result['data']['user']['id'])
            data = task['data']['incoming_data']

            # Align dynamic ContentType input if provided as benefit_plan_type__model
            benefit_plan_type_model = data.pop('benefit_plan_type__model', None)
            if benefit_plan_type_model:
                from django.contrib.contenttypes.models import ContentType
                content_type = ContentType.objects.get(model=str(benefit_plan_type_model).lower())
                model_id = data.get('benefit_plan_id')
                if model_id is not None:
                    content_type.get_object_for_this_type(pk=model_id)
                data['benefit_plan_type'] = content_type

            PaymentPlanService(user).update(data)
        except Exception as exc:
            logger.error("Error while executing on_task_complete_payment_plan_update", exc_info=exc)

    bind_service_signal(
        'task_service.complete_task',
        on_task_complete_payment_plan_update,
        bind_type=ServiceSignalBindType.AFTER
    )

    def on_task_complete_payment_plan_delete(**kwargs):
        try:
            result = kwargs.get('result', None)
            if not result or not result.get('success'):
                return
            task = result['data']['task']
            if task['business_event'] != ContributionPlanConfig.payment_plan_delete_event:
                return
            if task['status'] != Task.Status.COMPLETED:
                return
            user = User.objects.get(id=result['data']['user']['id'])
            data = task['data']['incoming_data']

            ids = data.get('ids') or data.get('uuids') or []
            if ids:
                for id_ in ids:
                    PaymentPlanService(user).delete({'id': id_})
            else:
                id_ = data.get('id') or data.get('uuid')
                if id_:
                    PaymentPlanService(user).delete({'id': id_})
        except Exception as exc:
            logger.error("Error while executing on_task_complete_payment_plan_delete", exc_info=exc)

    bind_service_signal(
        'task_service.complete_task',
        on_task_complete_payment_plan_delete,
        bind_type=ServiceSignalBindType.AFTER
    )


