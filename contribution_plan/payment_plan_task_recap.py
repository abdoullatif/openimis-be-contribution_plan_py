"""Récapitulatif des tâches maker-checker plan de paiement."""

import json
from datetime import date, datetime
from decimal import Decimal

from django.contrib.contenttypes.models import ContentType

PERIODICITY_LABELS = {
    1: "Mensuelle (1)",
    3: "Trimestrielle (3)",
    6: "Semestrielle (6)",
    12: "Annuelle (12)",
}

MAX_LOCATION_LABELS = 25
LOCATION_FALLBACK_LIMIT = 200
# Même module que le formulaire (fetchCustomFilter moduleName="social_protection")
CUSTOM_FILTER_MODULE = "social_protection"
CUSTOM_FILTER_OBJECT_TYPE = "BenefitPlan"
# Champs schema (prefecture, district, …) sont sur individual.json_ext
BENEFICIARY_FILTER_RELATION = "individual"

BENEFICIARY_SCOPE_KEYS = (
    "nombre_beneficiaires_regime",
    "nombre_beneficiaires_selectionnes",
    "criteres_filtrage_beneficiaires",
    "prefectures_concernees",
    "districts_concernees",
    "regions_concernees",
)

# Champs uniquement pour l'écran de tâche / businessData (pas des colonnes PaymentPlan).
PAYMENT_PLAN_TASK_DISPLAY_ONLY_KEYS = frozenset({
    *BENEFICIARY_SCOPE_KEYS,
    "districts_concernes",  # variante historique dans certains écrans
    "type_operation",
    "recapitulatif_plan_paiement",
    "modifications",
    "regime_prestations",
    "regle_calcul",
    "parametres_calcul",
    "nom",
    "date_debut",
    "date_fin",
    "periodicite",
})


def sanitize_payment_plan_payload_for_db(payload):
    """
    Retire les champs de récap avant create/update PaymentPlan (évite échec silencieux à la validation tâche).
    """
    if not isinstance(payload, dict):
        return {}
    return {key: value for key, value in payload.items() if key not in PAYMENT_PLAN_TASK_DISPLAY_ONLY_KEYS}


def _resolve_json_ext_dict(raw):
    if not raw:
        return {}
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                return parsed
            if isinstance(parsed, str):
                return _resolve_json_ext_dict(parsed)
        except (TypeError, ValueError):
            return {}
    return {}


def _plan_data_json_ext(plan_data):
    if not isinstance(plan_data, dict):
        return {}
    raw = plan_data.get("json_ext") if plan_data.get("json_ext") is not None else plan_data.get("jsonExt")
    return _resolve_json_ext_dict(raw)


def _plan_data_benefit_plan_id(plan_data):
    if not isinstance(plan_data, dict):
        return None
    return (
        plan_data.get("benefit_plan_id")
        or plan_data.get("benefitPlanId")
    )


def format_date_only(value):
    if not value:
        return None
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    text = str(value).strip()
    if not text:
        return None
    if "T" in text:
        return text.split("T", 1)[0]
    return text[:10]


def deep_to_json_safe(value):
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (datetime, date)):
        return format_date_only(value)
    if isinstance(value, (list, tuple)):
        return [deep_to_json_safe(item) for item in value]
    if isinstance(value, dict):
        return {key: deep_to_json_safe(item) for key, item in value.items()}
    if hasattr(value, "isoformat"):
        return format_date_only(value)
    return str(value)


def _infer_operation_type(data):
    incoming = data.get("incoming_data") if isinstance(data.get("incoming_data"), dict) else {}
    current = data.get("current_data") if isinstance(data.get("current_data"), dict) else {}
    if incoming.get("ids") or incoming.get("uuids"):
        return "Suppression"
    if current:
        return "Mise à jour"
    return "Création"


def _resolve_benefit_plan(plan_data):
    benefit_plan_id = _plan_data_benefit_plan_id(plan_data)
    if not benefit_plan_id:
        return None
    model_name = plan_data.get("benefit_plan_type__model")
    benefit_plan_type = plan_data.get("benefit_plan_type")
    try:
        if isinstance(benefit_plan_type, dict):
            model_class = benefit_plan_type.get("model")
        elif hasattr(benefit_plan_type, "model"):
            model_class = benefit_plan_type.model
        elif model_name:
            model_class = str(model_name).lower()
        else:
            model_class = "benefitplan"
        content_type = ContentType.objects.get(model=model_class)
        model = content_type.model_class()
        if not model:
            return None
        return model.objects.filter(pk=benefit_plan_id, is_deleted=False).first() or model.objects.filter(
            pk=benefit_plan_id
        ).first()
    except Exception:
        return None


def _resolve_benefit_plan_label(plan_data):
    benefit_plan = _resolve_benefit_plan(plan_data)
    if not benefit_plan:
        return str(plan_data.get("benefit_plan_id") or "")
    code = getattr(benefit_plan, "code", "") or ""
    name = getattr(benefit_plan, "name", "") or ""
    return f"{code} - {name}".strip(" -") or str(benefit_plan.id)


def _resolve_calculation_label(calculation_id):
    if not calculation_id:
        return None
    try:
        from calculation.services import get_calculation_object

        calculation = get_calculation_object(calculation_id)
        if calculation:
            return (
                getattr(calculation, "name", None)
                or getattr(calculation, "label", None)
                or calculation.__class__.__name__
            )
    except Exception:
        pass
    return str(calculation_id)


def _format_periodicity(value):
    if value is None:
        return None
    try:
        key = int(value)
    except (TypeError, ValueError):
        return str(value)
    return PERIODICITY_LABELS.get(key, str(key))


def _format_calculation_params(json_ext):
    if not isinstance(json_ext, dict):
        return None
    rule = json_ext.get("calculation_rule")
    if not isinstance(rule, dict):
        return None
    parts = [f"{key}={value}" for key, value in rule.items() if value not in (None, "")]
    return ", ".join(parts) if parts else None


def _extract_custom_filters_from_json_ext(json_ext):
    from core.custom_filters.filter_condition_utils import extract_custom_filters_from_json_ext

    return extract_custom_filters_from_json_ext(json_ext)


def _humanize_filter_condition(condition):
    if isinstance(condition, dict):
        field = condition.get("field", "")
        filt = condition.get("filter", "")
        value = condition.get("value", "")
        if isinstance(value, dict):
            value = value.get("name", value)
        return f"{field} ({filt}) = {value}"
    text = str(condition)
    if "=" in text:
        field_part, value = text.split("=", 1)
        return f"{field_part.replace('__', ' ')} = {value}"
    return text


def _format_filter_criteria_label(custom_filters):
    if not custom_filters:
        return None
    return "; ".join(_humanize_filter_condition(item) for item in custom_filters)


def _build_beneficiaries_queryset(benefit_plan, custom_filters):
    from social_protection.models import Beneficiary, BeneficiaryStatus

    from core.custom_filters import CustomFilterWizardStorage

    queryset = Beneficiary.objects.filter(
        benefit_plan=benefit_plan,
        status=BeneficiaryStatus.ACTIVE,
        is_deleted=False,
    )
    if custom_filters:
        queryset = CustomFilterWizardStorage.build_custom_filters_queryset(
            CUSTOM_FILTER_MODULE,
            CUSTOM_FILTER_OBJECT_TYPE,
            custom_filters,
            queryset,
            relation=BENEFICIARY_FILTER_RELATION,
        )
    return queryset


def _join_sorted_unique(values, max_items=MAX_LOCATION_LABELS):
    sorted_values = sorted({str(value).strip() for value in values if value})
    if not sorted_values:
        return None
    if len(sorted_values) > max_items:
        extra = len(sorted_values) - max_items
        return f"{', '.join(sorted_values[:max_items])} … (+{extra})"
    return ", ".join(sorted_values)


def _distinct_json_ext_values(beneficiaries_qs, key):
    """Valeurs distinctes depuis individual.json_ext (requête SQL, pas de boucle Python)."""
    lookup = f"individual__json_ext__{key}"
    values = (
        beneficiaries_qs.exclude(**{f"{lookup}__isnull": True})
        .exclude(**{lookup: ""})
        .values_list(lookup, flat=True)
        .distinct()[: MAX_LOCATION_LABELS + 1]
    )
    return [str(value).strip() for value in values if value]


def _count_distinct_menages(beneficiaries_qs, max_scan=50000):
    """Nombre de ménages distincts (code_menage dans individual.json_ext)."""
    menages = set()
    qs = beneficiaries_qs.select_related("individual").only("id", "json_ext", "individual__json_ext")
    for beneficiary in qs.iterator(chunk_size=1000):
        if len(menages) >= max_scan:
            break
        json_ext = beneficiary.json_ext or {}
        individual_ext = beneficiary.individual.json_ext if beneficiary.individual else {}
        code = json_ext.get("code_menage") or individual_ext.get("code_menage")
        if code:
            menages.add(str(code).strip())
    return len(menages)


def _summarize_beneficiary_locations_fast(beneficiaries_qs):
    """
    Agrège préfectures / districts / régions via json_ext en SQL.
    Repli limité uniquement si json_ext est vide pour une partie des bénéficiaires.
    """
    from django.db.models import Q

    prefectures = _distinct_json_ext_values(beneficiaries_qs, "prefecture")
    districts = _distinct_json_ext_values(beneficiaries_qs, "district")
    regions = _distinct_json_ext_values(beneficiaries_qs, "region")

    if len(prefectures) < MAX_LOCATION_LABELS:
        missing_qs = beneficiaries_qs.filter(
            Q(individual__json_ext__prefecture__isnull=True)
            | Q(individual__json_ext__prefecture="")
        ).values_list("individual_id", flat=True)[:LOCATION_FALLBACK_LIMIT]
        missing_ids = list(missing_qs)
        if missing_ids:
            from individual.models import Individual

            for individual in Individual.objects.filter(id__in=missing_ids).select_related(
                "location"
            ).only("id", "json_ext", "location_id"):
                location = getattr(individual, "location", None)
                if location:
                    current = location
                    while current and len(prefectures) < MAX_LOCATION_LABELS:
                        if getattr(current, "type", None) == "P" and getattr(current, "name", None):
                            prefectures.append(str(current.name).strip())
                            break
                        current = getattr(current, "parent", None)

    return {
        "prefectures": _join_sorted_unique(prefectures),
        "districts": _join_sorted_unique(districts),
        "regions": _join_sorted_unique(regions),
    }


def _beneficiary_scope_from_cache(plan_data):
    if plan_data.get("nombre_beneficiaires_regime") is None:
        return None
    return {key: plan_data.get(key) for key in BENEFICIARY_SCOPE_KEYS}


def _should_recompute_beneficiary_scope(plan_data):
    """Ne pas réutiliser un cache calculé sans critères si json_ext en contient."""
    json_ext = _plan_data_json_ext(plan_data)
    if _extract_custom_filters_from_json_ext(json_ext):
        return True
    cached = _beneficiary_scope_from_cache(plan_data)
    if cached is None:
        return True
    if cached.get("criteres_filtrage_beneficiaires"):
        return True
    return False


def build_beneficiary_scope_summary(plan_data, *, recompute=False):
    if not recompute and not _should_recompute_beneficiary_scope(plan_data):
        cached = _beneficiary_scope_from_cache(plan_data)
        if cached is not None:
            return cached

    benefit_plan = _resolve_benefit_plan(plan_data)
    if not benefit_plan:
        return {}

    json_ext = _plan_data_json_ext(plan_data)
    custom_filters = _extract_custom_filters_from_json_ext(json_ext)

    all_active_qs = _build_beneficiaries_queryset(benefit_plan, [])
    total_on_plan = all_active_qs.count()

    if custom_filters:
        selected_qs = _build_beneficiaries_queryset(benefit_plan, custom_filters)
        selected_count = selected_qs.count()
        locations = _summarize_beneficiary_locations_fast(selected_qs)
    else:
        selected_count = total_on_plan
        locations = _summarize_beneficiary_locations_fast(all_active_qs)

    return {
        "nombre_beneficiaires_regime": total_on_plan,
        "nombre_beneficiaires_selectionnes": selected_count,
        "criteres_filtrage_beneficiaires": _format_filter_criteria_label(custom_filters),
        "prefectures_concernees": locations.get("prefectures"),
        "districts_concernees": locations.get("districts"),
        "regions_concernees": locations.get("regions"),
    }


def attach_beneficiary_scope_to_task_payload(payload):
    """Pré-calcule le récap bénéficiaires à la création de la tâche (évite le recalcul à l'affichage)."""
    scope = build_beneficiary_scope_summary(payload, recompute=True)
    payload.update(scope)
    return payload


def _normalize_plan_snapshot(plan_data):
    if not isinstance(plan_data, dict):
        return {}
    json_ext = _plan_data_json_ext(plan_data)
    snapshot = {
        "code": plan_data.get("code"),
        "nom": plan_data.get("name"),
        "regime_prestations": _resolve_benefit_plan_label(plan_data),
        "regle_calcul": _resolve_calculation_label(plan_data.get("calculation")),
        "date_debut": format_date_only(plan_data.get("date_valid_from")),
        "date_fin": format_date_only(plan_data.get("date_valid_to")),
        "parametres_calcul": _format_calculation_params(json_ext),
    }
    snapshot.update(build_beneficiary_scope_summary(plan_data, recompute=True))
    return snapshot


def _build_changes(current, proposed):
    changes = []
    for key, label in (
        ("code", "Code"),
        ("nom", "Nom"),
        ("regime_prestations", "Régime de prestations"),
        ("regle_calcul", "Règle de calcul"),
        ("date_debut", "Date début"),
        ("date_fin", "Date fin"),
        ("parametres_calcul", "Paramètres calcul"),
        ("nombre_beneficiaires_regime", "Bénéficiaires actifs (régime)"),
        ("nombre_beneficiaires_selectionnes", "Bénéficiaires sélectionnés"),
        ("criteres_filtrage_beneficiaires", "Critères de filtrage"),
        ("prefectures_concernees", "Préfectures concernées"),
        ("districts_concernees", "Districts concernés"),
        ("regions_concernees", "Régions concernées"),
    ):
        old_value = current.get(key)
        new_value = proposed.get(key)
        if old_value != new_value and (old_value is not None or new_value is not None):
            changes.append({
                "champ": label,
                "valeur_actuelle": old_value,
                "valeur_proposee": new_value,
            })
    return changes


def format_payment_plan_recap_text(operation_type, proposed, current=None, changes=None):
    lines = [f"Opération : {operation_type}"]
    if operation_type == "Mise à jour" and current:
        lines.append(f"Plan actuel : {current.get('code')} - {current.get('nom')}")
    if proposed.get("code") or proposed.get("nom"):
        lines.append(f"Plan : {proposed.get('code')} - {proposed.get('nom')}")
    for label, key in (
        ("Régime de prestations", "regime_prestations"),
        ("Règle de calcul", "regle_calcul"),
        ("Validité du", "date_debut"),
        ("Validité au", "date_fin"),
        ("Paramètres calcul", "parametres_calcul"),
        ("Bénéficiaires actifs (régime)", "nombre_beneficiaires_regime"),
        ("Bénéficiaires sélectionnés", "nombre_beneficiaires_selectionnes"),
        ("Critères de filtrage", "criteres_filtrage_beneficiaires"),
        ("Préfectures concernées", "prefectures_concernees"),
        ("Districts concernés", "districts_concernees"),
        ("Régions concernées", "regions_concernees"),
    ):
        value = proposed.get(key)
        if value is not None and value != "":
            lines.append(f"{label} : {value}")
    if changes:
        lines.append("Modifications proposées :")
        for change in changes:
            lines.append(
                f"  - {change['champ']} : {change['valeur_actuelle'] or '-'} "
                f"→ {change['valeur_proposee'] or '-'}"
            )
    return "\n".join(lines)


def build_payment_plan_task_display(data):
    """Construit le payload d'affichage pour businessData d'une tâche payment_plan."""
    if not data:
        return data

    operation_type = _infer_operation_type(data)
    raw_incoming = data.get("incoming_data", data)
    raw_current = data.get("current_data") if isinstance(data.get("current_data"), dict) else {}

    if operation_type == "Suppression" and raw_current:
        proposed = _normalize_plan_snapshot(raw_current)
    else:
        proposed = _normalize_plan_snapshot(raw_incoming)

    current = _normalize_plan_snapshot(raw_current) if raw_current else None
    changes = _build_changes(current, proposed) if current and operation_type == "Mise à jour" else []

    incoming_display = {
        "type_operation": operation_type,
        **proposed,
        "recapitulatif_plan_paiement": format_payment_plan_recap_text(
            operation_type, proposed, current, changes
        ),
    }
    if changes:
        incoming_display["modifications"] = changes

    result = {
        "incoming_data": deep_to_json_safe(incoming_display),
    }
    if current:
        result["current_data"] = deep_to_json_safe({
            "type_operation": operation_type,
            **current,
        })
    return result
