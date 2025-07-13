# Unified enums for Special Education Service
# Single source of truth for all enums used across models and schemas
from enum import Enum


class AssessmentType(str, Enum):
    """Standardized assessment types - unified across models and schemas"""
    WISC_V = "wisc_v"
    WIAT_IV = "wiat_iv"
    WJ_IV = "wj_iv"
    BASC_3 = "basc_3"
    CONNERS_3 = "conners_3"
    CTOPP_2 = "ctopp_2"
    KTEA_3 = "ktea_3"
    DAS_II = "das_ii"
    GORT_5 = "gort_5"
    TOWL_4 = "towl_4"
    BRIEF_2 = "brief_2"
    VINELAND_3 = "vineland_3"
    FBA = "functional_behavior_assessment"
    CBM = "curriculum_based_measure"
    OBSERVATION = "teacher_observation"
    PROGRESS_MONITORING = "progress_monitoring"