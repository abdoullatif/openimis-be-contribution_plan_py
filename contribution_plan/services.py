import json

from django.core.serializers.json import DjangoJSONEncoder
from django.contrib.auth.models import AnonymousUser
from django.forms.models import model_to_dict
from contribution_plan.models import ContributionPlan as ContributionPlanModel, ContributionPlanBundle as ContributionPlanBundleModel, \
    ContributionPlanBundleDetails as ContributionPlanBundleDetailsModel, PaymentPlan as PaymentPlanModel


def check_authentication(function):
    def wrapper(self, *args, **kwargs):
        if type(self.user) is AnonymousUser or not self.user.id:
            return {
                "success": False,
                "message": "Authentication required",
                "detail": "PermissionDenied",
            }
        else:
            result = function(self, *args, **kwargs)
            return result
    return wrapper


class ContributionPlanService(object):

    def __init__(self, user):
        self.user = user

    @check_authentication
    def get_by_id(self, by_contribution_plan):
        try:
            cp = ContributionPlanModel.objects.get(id=by_contribution_plan.id)
            uuid_string = str(cp.id)
            dict_representation = model_to_dict(cp)
            dict_representation["id"], dict_representation["uuid"] = (str(uuid_string), str(uuid_string))
        except Exception as exc:
            return _output_exception(model_name="ContributionPlan", method="get", exception=exc)
        return _output_result_success(dict_representation=dict_representation)

    @check_authentication
    def create(self, contribution_plan):
        try:
            cp = ContributionPlanModel(**contribution_plan)
            cp.save(username=self.user.username)
            uuid_string = str(cp.id)
            dict_representation = model_to_dict(cp)
            dict_representation["id"], dict_representation["uuid"] = (str(uuid_string), str(uuid_string))
        except Exception as exc:
            return _output_exception(model_name="ContributionPlan", method="create", exception=exc)
        return _output_result_success(dict_representation=dict_representation)

    @check_authentication
    def update(self, contribution_plan):
        try:
            updated_cp = ContributionPlanModel.objects.filter(id=contribution_plan['id']).first()
            [setattr(updated_cp, key, contribution_plan[key]) for key in contribution_plan]
            updated_cp.save(username=self.user.username)
            uuid_string = str(updated_cp.id)
            dict_representation = model_to_dict(updated_cp)
            dict_representation["id"], dict_representation["uuid"] = (str(uuid_string), str(uuid_string))
        except Exception as exc:
            return _output_exception(model_name="ContributionPlan", method="update", exception=exc)
        return _output_result_success(dict_representation=dict_representation)

    @check_authentication
    def delete(self, contribution_plan):
        try:
            cp_to_delete = ContributionPlanModel.objects.filter(id=contribution_plan['id']).first()
            cp_to_delete.delete(username=self.user.username)
            return {
                "success": True,
                "message": "Ok",
                "detail": "",
            }
        except Exception as exc:
            return _output_exception(model_name="ContributionPlan", method="delete", exception=exc)

    @check_authentication
    def replace(self, contribution_plan):
        try:
            cp_to_replace = ContributionPlanModel.objects.filter(id=contribution_plan['uuid']).first()
            cp_to_replace.replace_object(data=contribution_plan, username=self.user.username)
            uuid_string = str(cp_to_replace.id)
            dict_representation = model_to_dict(cp_to_replace)
            dict_representation["id"], dict_representation["uuid"] = (str(uuid_string), str(uuid_string))
        except Exception as exc:
            return _output_exception(model_name="ContributionPlan", method="replace", exception=exc)
        return {
            "success": True,
            "message": "Ok",
            "detail": "",
            "old_object": json.loads(json.dumps(dict_representation, cls=DjangoJSONEncoder)),
            "uuid_new_object": str(cp_to_replace.replacement_uuid),
        }

    @staticmethod
    def check_unique_code(code):
        if ContributionPlanModel.objects.filter(code=code, is_deleted=0).exists():
            return [{"message": "Contribution plan code %s already exists" % code}]
        return []


class ContributionPlanBundleService(object):

    def __init__(self, user):
        self.user = user

    @check_authentication
    def get_by_id(self, by_contribution_plan_bundle):
        try:
            cpb = ContributionPlanBundleModel.objects.get(id=by_contribution_plan_bundle.id)
            uuid_string = str(cpb.id)
            dict_representation = model_to_dict(cpb)
            dict_representation["id"], dict_representation["uuid"] = (str(uuid_string), str(uuid_string))
        except Exception as exc:
            return _output_exception(model_name="ContributionPlanBundle", method="get", exception=exc)
        return _output_result_success(dict_representation=dict_representation)

    @check_authentication
    def create(self, contribution_plan_bundle):
        try:
            cpb = ContributionPlanBundleModel(**contribution_plan_bundle)
            cpb.save(username=self.user.username)
            uuid_string = str(cpb.id)
            dict_representation = model_to_dict(cpb)
            dict_representation["id"], dict_representation["uuid"] = (str(uuid_string), str(uuid_string))
        except Exception as exc:
            return _output_exception(model_name="ContributionPlanBundle", method="create", exception=exc)
        return _output_result_success(dict_representation=dict_representation)

    @check_authentication
    def update(self, contribution_plan_bundle):
        try:
            updated_cpb = ContributionPlanBundleModel.objects.filter(id=contribution_plan_bundle['id']).first()
            [setattr(updated_cpb, key, contribution_plan_bundle[key]) for key in contribution_plan_bundle]
            updated_cpb.save(username=self.user.username)
            uuid_string = str(updated_cpb.id)
            dict_representation = model_to_dict(updated_cpb)
            dict_representation["id"], dict_representation["uuid"] = (str(uuid_string), str(uuid_string))
        except Exception as exc:
            return _output_exception(model_name="ContributionPlanBundle", method="update", exception=exc)
        return _output_result_success(dict_representation=dict_representation)

    @check_authentication
    def delete(self, contribution_plan_bundle):
        try:
            cpb_to_delete = ContributionPlanBundleModel.objects.filter(id=contribution_plan_bundle['id']).first()
            cpb_to_delete.delete(username=self.user.username)
            return {
                "success": True,
                "message": "Ok",
                "detail": "",
            }
        except Exception as exc:
            return _output_exception(model_name="ContributionPlanBundle", method="delete", exception=exc)

    @check_authentication
    def replace(self, contribution_plan_bundle):
        try:
            cpb_to_replace = ContributionPlanBundleModel.objects.filter(id=contribution_plan_bundle['uuid']).first()
            cpb_to_replace.replace_object(data=contribution_plan_bundle, username=self.user.username)
            uuid_string = str(cpb_to_replace.id)
            dict_representation = model_to_dict(cpb_to_replace)
            dict_representation["id"], dict_representation["uuid"] = (str(uuid_string), str(uuid_string))
        except Exception as exc:
            return _output_exception(model_name="ContributionPlanBundle", method="replace", exception=exc)
        return {
            "success": True,
            "message": "Ok",
            "detail": "",
            "old_object": json.loads(json.dumps(dict_representation, cls=DjangoJSONEncoder)),
            "uuid_new_object": str(cpb_to_replace.replacement_uuid),
        }

    @staticmethod
    def check_unique_code(code):
        if ContributionPlanBundleModel.objects.filter(code=code, is_deleted=0).exists():
            return [{"message": "Contribution plan bundle code %s already exists" % code}]
        return []




class ContributionPlanBundleDetails(object):

    def __init__(self, user):
        self.user = user

    @check_authentication
    def get_by_id(self, by_contribution_plan_bundle_details):
        try:
            cpbd = ContributionPlanBundleDetailsModel.objects.get(id=by_contribution_plan_bundle_details.id)
            uuid_string = str(cpbd.id)
            dict_representation = model_to_dict(cpbd)
            dict_representation["id"], dict_representation["uuid"] = (str(uuid_string), str(uuid_string))
        except Exception as exc:
            return _output_exception(model_name="ContributionPlanBundleDetails", method="get", exception=exc)
        return _output_result_success(dict_representation=dict_representation)

    @check_authentication
    def create(self, contribution_plan_bundle_details):
        try:
            cpbd = ContributionPlanBundleDetailsModel(**contribution_plan_bundle_details)
            cpbd.save(username=self.user.username)
            uuid_string = str(cpbd.id)
            dict_representation = model_to_dict(cpbd)
            dict_representation["id"], dict_representation["uuid"] = (str(uuid_string), str(uuid_string))
        except Exception as exc:
            return _output_exception(model_name="ContributionPlanBundleDetails", method="create", exception=exc)
        return _output_result_success(dict_representation=dict_representation)

    @check_authentication
    def update(self, contribution_plan_bundle_details):
        try:
            updated_cpbd = ContributionPlanBundleDetailsModel.objects.filter(
                id=contribution_plan_bundle_details['id']).first()
            [setattr(updated_cpbd, key, contribution_plan_bundle_details[key]) for key in contribution_plan_bundle_details]
            updated_cpbd.save(username=self.user.username)
            uuid_string = str(updated_cpbd.id)
            dict_representation = model_to_dict(updated_cpbd)
            dict_representation["id"], dict_representation["uuid"] = (str(uuid_string), str(uuid_string))
        except Exception as exc:
            return _output_exception(model_name="ContributionPlanBundleDetails", method="update", exception=exc)
        return _output_result_success(dict_representation=dict_representation)

    @check_authentication
    def delete(self, contribution_plan_bundle_details):
        try:
            cpbd_to_delete = ContributionPlanBundleDetailsModel.objects.filter(id=contribution_plan_bundle_details['id']).first()
            cpbd_to_delete.delete(username=self.user.username)
            return {
                "success": True,
                "message": "Ok",
                "detail": "",
            }
        except Exception as exc:
            return _output_exception(model_name="ContributionPlanBundleDetails", method="delete", exception=exc)


class PaymentPlan(object):

    def __init__(self, user):
        self.user = user

    @check_authentication
    def get_by_id(self, by_payment_plan):
        try:
            pp = PaymentPlanModel.objects.get(id=by_payment_plan.id)
            uuid_string = str(pp.id)
            dict_representation = model_to_dict(pp)
            dict_representation["id"], dict_representation["uuid"] = (str(uuid_string), str(uuid_string))
        except Exception as exc:
            return _output_exception(model_name="PaymentPlan", method="get", exception=exc)
        return _output_result_success(dict_representation=dict_representation)

    @check_authentication
    def create(self, payment_plan):
        try:
            from contribution_plan.payment_plan_task_recap import sanitize_payment_plan_payload_for_db

            payment_plan = sanitize_payment_plan_payload_for_db(payment_plan)
            pp = PaymentPlanModel(**payment_plan)
            pp.save(username=self.user.username)
            uuid_string = str(pp.id)
            dict_representation = model_to_dict(pp)
            dict_representation["id"], dict_representation["uuid"] = (str(uuid_string), str(uuid_string))
        except Exception as exc:
            return _output_exception(model_name="PaymentPlan", method="create", exception=exc)
        return _output_result_success(dict_representation=dict_representation)

    @check_authentication
    def update(self, payment_plan):
        try:
            updated_pp = PaymentPlanModel.objects.filter(id=payment_plan['id']).first()
            [setattr(updated_pp, key, payment_plan[key]) for key in payment_plan]
            updated_pp.save(username=self.user.username)
            uuid_string = str(updated_pp.id)
            dict_representation = model_to_dict(updated_pp)
            dict_representation["id"], dict_representation["uuid"] = (str(uuid_string), str(uuid_string))
        except Exception as exc:
            return _output_exception(model_name="payment_plan", method="update", exception=exc)
        return _output_result_success(dict_representation=dict_representation)

    @check_authentication
    def delete(self, payment_plan):
        try:
            pp_to_delete = PaymentPlanModel.objects.filter(id=payment_plan['id']).first()
            pp_to_delete.delete(username=self.user.username)
            return {
                "success": True,
                "message": "Ok",
                "detail": "",
            }
        except Exception as exc:
            return _output_exception(model_name="PaymentPlanModel", method="delete", exception=exc)

    @check_authentication
    def replace(self, payment_plan):
        try:
            pp_to_replace = PaymentPlanModel.objects.filter(id=payment_plan['uuid']).first()
            pp_to_replace.replace_object(data=payment_plan, username=self.user.username)
            uuid_string = str(pp_to_replace.id)
            dict_representation = model_to_dict(pp_to_replace)
            dict_representation["id"], dict_representation["uuid"] = (str(uuid_string), str(uuid_string))
        except Exception as exc:
            return _output_exception(model_name="ContributionPlan", method="replace", exception=exc)
        return {
            "success": True,
            "message": "Ok",
            "detail": "",
            "old_object": json.loads(json.dumps(dict_representation, cls=DjangoJSONEncoder)),
            "uuid_new_object": str(pp_to_replace.replacement_uuid),
        }

    @staticmethod
    def check_unique_code(code, uuid=None):
        qs = PaymentPlanModel.objects.filter(code=code, is_deleted=False)
        if uuid:
            qs = qs.exclude(id=uuid)
        if qs:
            return [{"message": "Payment plan code %s already exists" % code}]
        return []

    @staticmethod
    def _business_data_serializer(data):
        """Formate les données de tâche PaymentPlan pour l'écran de validation."""
        from contribution_plan.payment_plan_task_recap import build_payment_plan_task_display

        return build_payment_plan_task_display(data)


def _output_exception(model_name, method, exception):
    return {
        "success": False,
        "message": f"Failed to {method} {model_name}",
        "detail": str(exception),
        "data": "",
    }


def _output_result_success(dict_representation):
    return {
        "success": True,
        "message": "Ok",
        "detail": "",
        "data": json.loads(json.dumps(dict_representation, cls=DjangoJSONEncoder)),
    }
