import graphene
from django.core.exceptions import PermissionDenied
from django.contrib.contenttypes.models import ContentType

from contribution_plan.apps import ContributionPlanConfig
from contribution_plan.gql.util import model_obj_to_json
from contribution_plan.models import ContributionPlanBundle, ContributionPlan, \
    ContributionPlanBundleDetails, PaymentPlan
from core import ExtendedConnection, prefix_filterset
from graphene_django import DjangoObjectType
from django.utils.translation import gettext as _


class ContributionPlanGQLType(DjangoObjectType):
    benefit_plan = graphene.JSONString()
    benefit_plan_type__model = graphene.String()
    benefit_plan_type_name = graphene.String()

    @staticmethod
    def resolve_benefit_plan_type__model(root, info):
        if not info.context.user.has_perms(ContributionPlanConfig.gql_query_contributionplan_perms):
            raise PermissionDenied(_("unauthorized"))
        return root.benefit_plan_type.model

    @staticmethod
    def resolve_benefit_plan_type_id(root, info):
        if not info.context.user.has_perms(ContributionPlanConfig.gql_query_contributionplan_perms):
            raise PermissionDenied(_("unauthorized"))
        return root.benefit_plan_type.id

    @staticmethod
    def resolve_benefit_plan_type_name(root, info):
        if not info.context.user.has_perms(ContributionPlanConfig.gql_query_contributionplan_perms):
            raise PermissionDenied(_("unauthorized"))
        return root.benefit_plan_type.name

    @staticmethod
    def resolve_benefit_plan(root, info):
        if not info.context.user.has_perms(ContributionPlanConfig.gql_query_contributionplan_perms):
            raise PermissionDenied(_("unauthorized"))
        return model_obj_to_json(root.benefit_plan)

    class Meta:
        model = ContributionPlan
        interfaces = (graphene.relay.Node,)
        filter_fields = {
            "id": ["exact"],
            "version": ["exact"],
            "code": ["exact", "istartswith", "icontains", "iexact"],
            "name": ["exact", "istartswith", "icontains", "iexact"],
            'benefit_plan_id': ["exact"],
            'benefit_plan_type__model': ["exact"],
            'benefit_plan_type_id': ["exact"],
            "calculation": ["exact"],
            "periodicity": ["exact", "lt", "lte", "gt", "gte"],
            "date_created": ["exact", "lt", "lte", "gt", "gte"],
            "date_updated": ["exact", "lt", "lte", "gt", "gte"],
            "user_created": ["exact"],
            "user_updated": ["exact"],
            "is_deleted": ["exact"]
        }

        connection_class = ExtendedConnection

    @classmethod
    def get_queryset(cls, queryset, info):
        return ContributionPlan.get_queryset(queryset, info)


class ContributionPlanBundleGQLType(DjangoObjectType):

    class Meta:
        model = ContributionPlanBundle
        interfaces = (graphene.relay.Node,)
        filter_fields = {
            "id": ["exact"],
            "version": ["exact"],
            "code": ["exact", "istartswith", "icontains", "iexact"],
            "name": ["exact", "istartswith", "icontains", "iexact"],
            "periodicity": ["exact", "lt", "lte", "gt", "gte"],
            "date_created": ["exact", "lt", "lte", "gt", "gte"],
            "date_updated": ["exact", "lt", "lte", "gt", "gte"],
            "user_created": ["exact"],
            "user_updated": ["exact"],
            "is_deleted": ["exact"]
        }

        connection_class = ExtendedConnection

    @classmethod
    def get_queryset(cls, queryset, info):
        return ContributionPlanBundle.get_queryset(queryset, info)


class ContributionPlanBundleDetailsGQLType(DjangoObjectType):

    class Meta:
        model = ContributionPlanBundleDetails
        interfaces = (graphene.relay.Node,)
        filter_fields = {
            "id": ["exact"],
            "version": ["exact"],
            **prefix_filterset("contribution_plan_bundle__",
                               ContributionPlanBundleGQLType._meta.filter_fields),
            **prefix_filterset("contribution_plan__",
                               ContributionPlanGQLType._meta.filter_fields),
            "date_created": ["exact", "lt", "lte", "gt", "gte"],
            "date_updated": ["exact", "lt", "lte", "gt", "gte"],
            "user_created": ["exact"],
            "user_updated": ["exact"],
            "is_deleted": ["exact"]
        }

        connection_class = ExtendedConnection

    @classmethod
    def get_queryset(cls, queryset, info):
        return ContributionPlanBundleDetails.get_queryset(queryset, info)


class PaymentPlanGQLType(DjangoObjectType):
    benefit_plan = graphene.JSONString()
    benefit_plan_type = graphene.Int()
    benefit_plan_type_name = graphene.String()

    @staticmethod
    def resolve_benefit_plan_type(root, info):
        if not info.context.user.has_perms(ContributionPlanConfig.gql_query_paymentplan_perms):
            raise PermissionDenied(_("unauthorized"))
        return root.benefit_plan_type.id

    @staticmethod
    def resolve_benefit_plan_type_name(root, info):
        if not info.context.user.has_perms(ContributionPlanConfig.gql_query_contributionplan_perms):
            raise PermissionDenied(_("unauthorized"))
        return root.benefit_plan_type.name

    @staticmethod
    def resolve_benefit_plan(root, info):
        if not info.context.user.has_perms(ContributionPlanConfig.gql_query_contributionplan_perms):
            raise PermissionDenied(_("unauthorized"))
        return model_obj_to_json(root.benefit_plan)

    class Meta:
        model = PaymentPlan
        interfaces = (graphene.relay.Node,)
        filter_fields = {
            "id": ["exact"],
            "version": ["exact"],
            "code": ["exact", "istartswith", "icontains", "iexact"],
            "name": ["exact", "istartswith", "icontains", "iexact"],
            'benefit_plan_id': ["exact"],
            'benefit_plan_type': ["exact"],
            "calculation": ["exact"],
            "periodicity": ["exact", "lt", "lte", "gt", "gte"],
            "date_created": ["exact", "lt", "lte", "gt", "gte"],
            "date_updated": ["exact", "lt", "lte", "gt", "gte"],
            "user_created": ["exact"],
            "user_updated": ["exact"],
            "is_deleted": ["exact"]
        }

        connection_class = ExtendedConnection

    @classmethod
    def get_queryset(cls, queryset, info):
        return PaymentPlan.get_queryset(queryset, info).order_by("-date_created")
