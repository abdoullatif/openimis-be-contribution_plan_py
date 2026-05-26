from django.contrib.contenttypes.models import ContentType

from core.gql.gql_mutations import DeleteInputType
from core.gql.gql_mutations.base_mutation import BaseMutation, BaseDeleteMutation, BaseReplaceMutation, \
    BaseHistoryModelCreateMutationMixin, BaseHistoryModelUpdateMutationMixin, \
    BaseHistoryModelDeleteMutationMixin, BaseHistoryModelReplaceMutationMixin
from contribution_plan.services import PaymentPlan as PaymentPlanService
from contribution_plan.gql.gql_mutations import PaymentPlanInputType, PaymentPlanUpdateInputType, \
    PaymentPlanReplaceInputType
from contribution_plan.apps import ContributionPlanConfig
from contribution_plan.models import PaymentPlan
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
from contribution_plan.payment_plan_task_recap import attach_beneficiary_scope_to_task_payload
from tasks_management.services import TaskService, _get_std_task_data_payload, _get_std_crud_task_data_payload
from tasks_management.models import Task
from tasks_management.apps import TasksManagementConfig


class CreatePaymentPlanMutation(BaseHistoryModelCreateMutationMixin, BaseMutation):
    _mutation_class = "PaymentPlanMutation"
    _mutation_module = "contribution_plan"
    _model = PaymentPlan

    @classmethod
    def create_object(cls, user, object_data):
        benefit_plan_type__model = object_data.pop('benefit_plan_type__model', None)
        if benefit_plan_type__model:
            content_type = ContentType.objects.get(model=benefit_plan_type__model.lower())
            model_id = object_data.get('benefit_plan_id')
            try:
                content_type.get_object_for_this_type(pk=model_id)
            except Exception as e:
                raise AttributeError(e)
            object_data['benefit_plan_type'] = content_type
        obj = cls._model(**object_data)
        obj.save(username=user.username)
        return obj

    @classmethod
    def _validate_mutation(cls, user, **data):
        if type(user) is AnonymousUser or not user.id or not user.has_perms(
                ContributionPlanConfig.gql_mutation_create_paymentplan_perms):
            raise ValidationError(_("mutation.authentication_required"))
        if PaymentPlanService.check_unique_code(data['code']):
            raise ValidationError(_("mutation.payment_plan_code_duplicated"))

    @classmethod
    def _mutate(cls, user, **data):
        # Permissions & validations
        cls._validate_mutation(user, **data)

        # Cleanup technical fields
        data.pop("client_mutation_id", None)
        data.pop("client_mutation_label", None)

        # Create validation task instead of creating DB object immediately
        # Pour la création, on utilise _get_std_task_data_payload qui retourne juste incoming_data
        # On le wrapper dans un dict pour correspondre au format attendu par le handler
        incoming_data = attach_beneficiary_scope_to_task_payload(
            _get_std_task_data_payload(data)
        )
        TaskService(user).create({
            'source': 'payment_plan',
            'status': Task.Status.RECEIVED,
            'executor_action_event': TasksManagementConfig.default_executor_event,
            'business_event': ContributionPlanConfig.payment_plan_create_event,
            'business_data_serializer': f'{PaymentPlanService.__module__}.{PaymentPlanService.__name__}._business_data_serializer',
            'data': {'incoming_data': incoming_data},  # Format attendu par le handler
        })
        # Async mutation success (actual object will be created on task completion)
        return None

    class Input(PaymentPlanInputType):
        pass

class UpdatePaymentPlanMutation(BaseHistoryModelUpdateMutationMixin, BaseMutation):
    _mutation_class = "PaymentPlanMutation"
    _mutation_module = "contribution_plan"
    _model = PaymentPlan

    @classmethod
    def _validate_mutation(cls, user, **data):
        # Vérifie les permissions
        if (
            type(user) is AnonymousUser
            or not user.id
            or not user.has_perms(
                ContributionPlanConfig.gql_mutation_update_paymentplan_perms
            )
        ):
            raise ValidationError(_("mutation.authentication_required"))

        code = data.get("code")
        plan_id = data.get("id") or data.get("uuid")

        # Vérifie s'il existe un autre plan actif avec le même code
        if PaymentPlanService.check_unique_code(code, plan_id):
            # Vérifie si c’est le même plan (sinon erreur)
            is_same = cls._model.objects.filter(id=plan_id, code=code).exists()
            if not is_same:
                raise ValidationError(_("mutation.payment_plan_code_duplicated"))

    @classmethod
    def _mutate(cls, user, **data):
        # Permissions & validations
        cls._validate_mutation(user, **data)

        # Cleanup technical fields
        data.pop("client_mutation_id", None)
        data.pop("client_mutation_label", None)

        # Defer update to a task for maker-checker
        # Récupérer l'objet existant pour avoir current_data
        plan_id = data.get("id") or data.get("uuid")
        existing_object = cls._model.objects.filter(id=plan_id).first() if plan_id else None
        task_data = _get_std_crud_task_data_payload(existing_object, data)
        task_data["incoming_data"] = attach_beneficiary_scope_to_task_payload(task_data["incoming_data"])
        TaskService(user).create({
            'source': 'payment_plan',
            'status': Task.Status.RECEIVED,
            'executor_action_event': TasksManagementConfig.default_executor_event,
            'business_event': ContributionPlanConfig.payment_plan_update_event,
            'business_data_serializer': f'{PaymentPlanService.__module__}.{PaymentPlanService.__name__}._business_data_serializer',
            'data': task_data,
        })
        return None

    class Input(PaymentPlanUpdateInputType):
        pass



class DeletePaymentPlanMutation(BaseHistoryModelDeleteMutationMixin, BaseDeleteMutation):
    _mutation_class = "PaymentPlanMutation"
    _mutation_module = "contribution_plan"
    _model = PaymentPlan

    @classmethod
    def _validate_mutation(cls, user, **data):
        if type(user) is AnonymousUser or not user.id or not user.has_perms(
                ContributionPlanConfig.gql_mutation_delete_paymentplan_perms):
            raise ValidationError(_("mutation.authentication_required"))

    @classmethod
    def _mutate(cls, user, **data):
        # Permissions & validations
        cls._validate_mutation(user, **data)

        # Cleanup technical fields
        data.pop("client_mutation_id", None)
        data.pop("client_mutation_label", None)

        # Defer delete to a task for maker-checker
        # Récupérer l'objet existant pour avoir current_data
        ids = data.get('ids') or data.get('uuids') or []
        if ids:
            existing_object = cls._model.objects.filter(id=ids[0]).first() if ids else None
        else:
            obj_id = data.get('id') or data.get('uuid')
            existing_object = cls._model.objects.filter(id=obj_id).first() if obj_id else None
        # Pour delete, on utilise _get_std_crud_task_data_payload pour avoir les données actuelles
        task_data = _get_std_crud_task_data_payload(existing_object, data)
        scope_source = task_data.get("current_data") or task_data.get("incoming_data") or {}
        task_data["incoming_data"] = attach_beneficiary_scope_to_task_payload({
            **(task_data.get("incoming_data") or {}),
            **scope_source,
        })
        TaskService(user).create({
            'source': 'payment_plan',
            'status': Task.Status.RECEIVED,
            'executor_action_event': TasksManagementConfig.default_executor_event,
            'business_event': ContributionPlanConfig.payment_plan_delete_event,
            'business_data_serializer': f'{PaymentPlanService.__module__}.{PaymentPlanService.__name__}._business_data_serializer',
            'data': task_data,
        })
        return None

    class Input(DeleteInputType):
        pass


class ReplacePaymentPlanMutation(BaseHistoryModelReplaceMutationMixin, BaseReplaceMutation):
    _mutation_class = "PaymentPlanMutation"
    _mutation_module = "contribution_plan"
    _model = PaymentPlan

    @classmethod
    def _validate_mutation(cls, user, **data):
        if type(user) is AnonymousUser or not user.id or not user.has_perms(
                ContributionPlanConfig.gql_mutation_replace_paymentplan_perms):
            raise ValidationError(_("mutation.authentication_required"))

    class Input(PaymentPlanReplaceInputType):
        pass
