from django.apps import AppConfig


MODULE_NAME = "contribution_plan"


DEFAULT_CFG = {
    "gql_query_contributionplanbundle_perms": ["151101"],
    "gql_query_contributionplanbundle_admins_perms": [],
    "gql_query_contributionplan_perms": ["151201"],
    "gql_query_contributionplan_admins_perms": [],
    "gql_query_paymentplan_perms": ["157101"],
    "gql_query_paymentplan_admins_perms": [],

    "gql_mutation_create_contributionplanbundle_perms": ["151102"],
    "gql_mutation_update_contributionplanbundle_perms": ["151103"],
    "gql_mutation_delete_contributionplanbundle_perms": ["151104"],
    "gql_mutation_replace_contributionplanbundle_perms": ["151106"],

    "gql_mutation_create_contributionplan_perms": ["151202"],
    "gql_mutation_update_contributionplan_perms": ["151203"],
    "gql_mutation_delete_contributionplan_perms": ["151204"],
    "gql_mutation_replace_contributionplan_perms": ["151206"],

    "gql_mutation_create_paymentplan_perms": ["157102"],
    "gql_mutation_update_paymentplan_perms": ["157103"],
    "gql_mutation_delete_paymentplan_perms": ["157104"],
    "gql_mutation_replace_paymentplan_perms": ["157106"],
    "payment_plan_create_event": "contribution_plan.payment_plan_create",
    "payment_plan_update_event": "contribution_plan.payment_plan_update",
    "payment_plan_delete_event": "contribution_plan.payment_plan_delete",
}


class ContributionPlanConfig(AppConfig):
    name = MODULE_NAME

    gql_query_contributionplanbundle_perms = []
    gql_query_contributionplanbundle_admins_perms = []

    gql_query_contributionplan_perms = []
    gql_query_contributionplan_admins_perms = []

    gql_query_paymentplan_perms = []
    gql_query_paymentplan_admins_perms = []

    gql_mutation_create_contributionplanbundle_perms = []
    gql_mutation_update_contributionplanbundle_perms = []
    gql_mutation_delete_contributionplanbundle_perms = []
    gql_mutation_replace_contributionplanbundle_perms = []

    gql_mutation_create_contributionplan_perms = []
    gql_mutation_update_contributionplan_perms = []
    gql_mutation_delete_contributionplan_perms = []
    gql_mutation_replace_contributionplan_perms = []

    gql_mutation_create_paymentplan_perms = []
    gql_mutation_update_paymentplan_perms = []
    gql_mutation_delete_paymentplan_perms = []
    gql_mutation_replace_paymentplan_perms = []
    payment_plan_create_event = None
    payment_plan_update_event = None
    payment_plan_delete_event = None

    def __load_config(self, cfg):
        for field in cfg:
            if hasattr(ContributionPlanConfig, field):
                setattr(ContributionPlanConfig, field, cfg[field])

    def ready(self):
        from core.models import ModuleConfiguration
        cfg = ModuleConfiguration.get_or_default(MODULE_NAME, DEFAULT_CFG)
        self.__load_config(cfg)
