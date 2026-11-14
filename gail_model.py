"""A Python implementation of the White reference branch of NCI BCRAT/Gail.

Ported from the BCRA 2.1.2 public source implementation of the BCRA 2.0-era
algorithm. This is a software translation/reference implementation, NOT a
clinically validated tool for Egyptian women or any population not represented
by the model's underlying incidence/mortality data.

Input ages are years (may be fractional). Risk factors follow BCRA coding:
N_Biop: 0, 1, 2+; HypPlas: 0=no, 1=yes, 99=unknown;
AgeMen: age at menarche (99=unknown); Age1st: age at first live birth
(98=nulliparous, 99=unknown); N_Rels: first-degree relatives (0,1,2+).
"""
from __future__ import annotations
from dataclasses import dataclass
from math import exp, log
from typing import Optional

# BCRA Gail/CARE White coefficients: NB, AM, AF, NR, NB*age>=50, AF*NR
WHITE_BETA = (0.5292641686, 0.0940103059, 0.2186262218,
              0.9583027845, -0.2880424830, -0.1908113865)
WHITE_ONE_MINUS_AR = (0.5788413, 0.5788413)  # <50, >=50

# SEER White 1983-87 incidence and NCHS White 1985-87 competing mortality.
# Fourteen five-year age bands, beginning at age 20-24.
WHITE_LAMBDA1_5Y = (
    0.00001000, 0.00007600, 0.00026600, 0.00066100, 0.00126500,
    0.00186600, 0.00221100, 0.00272100, 0.00334800, 0.00392300,
    0.00417800, 0.00443900, 0.00442100, 0.00410900,
)
WHITE_LAMBDA2_5Y = (
    0.00049300, 0.00053100, 0.00062500, 0.00082500, 0.00130700,
    0.00218100, 0.00365500, 0.00585200, 0.00943900, 0.01502800,
    0.02383900, 0.03883200, 0.06682800, 0.14490800,
)

@dataclass(frozen=True)
class RiskFactors:
    current_age: float
    projection_age: float
    biopsies: int
    atypical_hyperplasia: int
    menarche_age: int
    first_live_birth_age: int
    first_degree_relatives: int

@dataclass(frozen=True)
class GailResult:
    relative_risk_under_50: float
    relative_risk_50_plus: float
    absolute_risk_percent: float
    projection_years: float
    reference_population: str = "Non-Hispanic White (US reference rates)"


def _recode(x: RiskFactors) -> tuple[int, int, int, int, float]:
    """Translate raw risk factors to the BCRA categorical covariates."""
    if not (20 <= x.current_age < 90 and x.current_age < x.projection_age <= 90):
        raise ValueError("Require 20 <= current_age < projection_age <= 90.")
    if x.biopsies not in (0, 1, 2, 99):
        raise ValueError("biopsies must be 0, 1, 2 (meaning 2+), or 99 (unknown).")
    if x.atypical_hyperplasia not in (0, 1, 99):
        raise ValueError("atypical_hyperplasia must be 0, 1, or 99 (unknown).")
    if x.menarche_age not in (*range(8, 31), 99):
        raise ValueError("menarche_age must be a plausible age or 99 (unknown).")
    if x.first_live_birth_age not in (*range(10, 60), 98, 99):
        raise ValueError("first_live_birth_age must be an age, 98 (nulliparous), or 99 (unknown).")
    if x.first_degree_relatives not in (0, 1, 2, 99):
        raise ValueError("first_degree_relatives must be 0, 1, 2 (meaning 2+), or 99 (unknown).")

    nb = 0 if x.biopsies in (0, 99) else (1 if x.biopsies == 1 else 2)
    if nb == 0 and x.atypical_hyperplasia != 99:
        raise ValueError("BCRA input consistency: no biopsy/unknown biopsy count requires hyperplasia=99.")
    if nb > 0 and x.atypical_hyperplasia not in (0, 1, 99):
        raise ValueError("Invalid hyperplasia code.")

    am = 0 if x.menarche_age >= 14 or x.menarche_age == 99 else (1 if x.menarche_age >= 12 else 2)
    if x.menarche_age != 99 and x.menarche_age > x.current_age:
        raise ValueError("Menarche age cannot exceed current age.")

    af = (0 if x.first_live_birth_age < 20 or x.first_live_birth_age == 99
          else 1 if x.first_live_birth_age < 25
          else 2 if x.first_live_birth_age < 30 or x.first_live_birth_age == 98
          else 3)
    if x.first_live_birth_age not in (98, 99) and x.first_live_birth_age < x.menarche_age:
        raise ValueError("First live birth age cannot precede menarche age.")
    if x.first_live_birth_age not in (98, 99) and x.first_live_birth_age > x.current_age:
        raise ValueError("First live birth age cannot exceed current age.")

    nr = 0 if x.first_degree_relatives in (0, 99) else (1 if x.first_degree_relatives == 1 else 2)
    r_hyp = 1.0 if nb == 0 or x.atypical_hyperplasia == 99 else (0.93 if x.atypical_hyperplasia == 0 else 1.82)
    return nb, am, af, nr, r_hyp


def relative_risks(x: RiskFactors) -> tuple[float, float]:
    """Return Gail/BCRA relative risks for ages <50 and >=50."""
    nb, am, af, nr, r_hyp = _recode(x)
    b = WHITE_BETA
    lp_under_50 = nb*b[0] + am*b[1] + af*b[2] + nr*b[3] + af*nr*b[5] + log(r_hyp)
    lp_50_plus = lp_under_50 + nb*b[4]
    return exp(lp_under_50), exp(lp_50_plus)


def _annual_rate(age: float, rates: tuple[float, ...]) -> float:
    band = int((age - 20) // 5)
    if band < 0 or band >= len(rates):
        raise ValueError("Age outside the supported 20-89 year rate table.")
    return rates[band]


def absolute_risk_percent(x: RiskFactors) -> float:
    """Calculate cumulative invasive breast cancer risk over [current, projection] age.

    Uses the competing-risk integration used in BCRA absolute.risk. Output is
    percentage points (e.g. 1.23 means 1.23%), not a 0-1 fraction.
    """
    rr1, rr2 = relative_risks(x)
    t = float(x.current_age)
    end = float(x.projection_age)
    cumulative_hazard = 0.0
    risk = 0.0
    while t < end - 1e-12:
        next_year = min(end, int(t) + 1.0)
        duration = next_year - t
        rr = rr1 if t < 50 else rr2
        ar_rr = WHITE_ONE_MINUS_AR[0 if t < 50 else 1] * rr
        incidence = _annual_rate(t, WHITE_LAMBDA1_5Y)
        competing = _annual_rate(t, WHITE_LAMBDA2_5Y)
        total_hazard = ar_rr * incidence + competing
        if total_hazard <= 0:
            raise ArithmeticError("Non-positive total hazard encountered.")
        risk += (ar_rr * incidence / total_hazard) * exp(-cumulative_hazard) * (1 - exp(-total_hazard * duration))
        cumulative_hazard += total_hazard * duration
        t = next_year
    return 100.0 * risk


def calculate_gail_risk(x: RiskFactors) -> GailResult:
    rr1, rr2 = relative_risks(x)
    return GailResult(rr1, rr2, absolute_risk_percent(x), x.projection_age-x.current_age)
