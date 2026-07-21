# Seed terms for niche finance keyword tracking.
# Templates generate finance/loan variants with audience + intent tagging.

SUFFIXES = ["finance", "loan", "loans", "funding", "credit"]

COMMERCIAL_TEMPLATES = [
    # Vehicle niche finance
    "car tinting {suffix}",
    "car wrap {suffix}",
    "car detailing {suffix}",
    "motorbike {suffix}",
    "jet ski {suffix}",
    "boat {suffix}",
    "caravan {suffix}",
    "camper trailer {suffix}",
    "atv {suffix}",
    "trailer {suffix}",

    # Trade / equipment finance
    "tradie equipment {suffix}",
    "excavator {suffix}",
    "forklift {suffix}",
    "commercial vehicle {suffix}",
    "food truck {suffix}",
    "solar panel {suffix}",
    "generator {suffix}",
    "farm equipment {suffix}",
    "tractor {suffix}",

    # Small business / niche commercial
    "vending machine {suffix}",
    "gym equipment {suffix}",
    "salon equipment {suffix}",
    "dental equipment {suffix}",
    "restaurant equipment {suffix}",
    "franchise {suffix}",
    "invoice {suffix} small business",

    # Regional / broker-relevant modifiers (edit state/region as needed)
    "car {suffix} regional victoria",
    "boat {suffix} victoria",
    "caravan {suffix} melbourne",

    # Jim's franchise lines
    "jims mowing franchise {suffix}",
    "jims dog wash franchise {suffix}",
    "jims cleaning franchise {suffix}",
    "jims plumbing franchise {suffix}",
    "jims test and tag franchise {suffix}",
    "jims electrical franchise {suffix}",
]

CONSUMER_TEMPLATES = [
    "wedding {suffix}",
    "ivf {suffix}",
    "cosmetic surgery {suffix}",
    "home theatre {suffix}",
    "pool {suffix}",
    "granny flat {suffix}",
    "solar battery {suffix}",
]

PROBLEM_TERMS = [
    {"term": "can't afford a car", "audience": "consumer", "intent": "problem"},
    {"term": "need a car but no savings", "audience": "consumer", "intent": "problem"},
    {"term": "how to pay for a wedding", "audience": "consumer", "intent": "problem"},
    {"term": "finance for bad credit", "audience": "consumer", "intent": "problem"},
    {"term": "low deposit car loan", "audience": "consumer", "intent": "problem"},
    {"term": "urgent home repairs finance", "audience": "consumer", "intent": "problem"},
    {"term": "need equipment but no cash", "audience": "commercial", "intent": "problem"},
    {"term": "cashflow problems small business", "audience": "commercial", "intent": "problem"},
]

EXTRA_TERMS = [
    {"term": "4wd loan", "audience": "consumer", "intent": "product"},
    {"term": "four wheel drive finance", "audience": "consumer", "intent": "product"},
    {"term": "finance for a 4wd", "audience": "consumer", "intent": "product"},
    {"term": "used 4wd finance", "audience": "consumer", "intent": "product"},
    {"term": "4wd payment plans", "audience": "consumer", "intent": "product"},
    {"term": "buy a 4wd on finance", "audience": "consumer", "intent": "product"},
    {"term": "debt reset loan", "audience": "consumer", "intent": "problem"},
    {"term": "debt reset program", "audience": "consumer", "intent": "problem"},
    {"term": "debt consolidation loan", "audience": "consumer", "intent": "problem"},
    {"term": "combine debts into one loan", "audience": "consumer", "intent": "problem"},
    {"term": "help with credit card debt", "audience": "consumer", "intent": "problem"},
    {"term": "pay off debt faster loan", "audience": "consumer", "intent": "problem"},
    {"term": "deck building finance", "audience": "consumer", "intent": "product"},
    {"term": "deck construction loan", "audience": "consumer", "intent": "product"},
    {"term": "pay for a deck on finance", "audience": "consumer", "intent": "product"},
    {"term": "decking payment plans", "audience": "consumer", "intent": "product"},
    {"term": "deck renovation loan", "audience": "consumer", "intent": "product"},
    {"term": "finance for deck repairs", "audience": "consumer", "intent": "product"},
    {"term": "buy furniture on finance", "audience": "consumer", "intent": "product"},
    {"term": "furniture payment plans", "audience": "consumer", "intent": "product"},
    {"term": "furniture on instalments", "audience": "consumer", "intent": "product"},
    {"term": "sofa finance", "audience": "consumer", "intent": "product"},
    {"term": "bed finance", "audience": "consumer", "intent": "product"},
    {"term": "furniture loan", "audience": "consumer", "intent": "product"},
    {"term": "golf cart loans", "audience": "consumer", "intent": "product"},
    {"term": "golf cart finance", "audience": "consumer", "intent": "product"},
    {"term": "golf buggy finance", "audience": "consumer", "intent": "product"},
    {"term": "golf buggy loans", "audience": "consumer", "intent": "product"},
    {"term": "golf simulator finance", "audience": "consumer", "intent": "product"},
    {"term": "golf simulator loans", "audience": "consumer", "intent": "product"},
    {"term": "horse float finance", "audience": "consumer", "intent": "product"},
    {"term": "horse float loans", "audience": "consumer", "intent": "product"},
    {"term": "horse float repair finance", "audience": "consumer", "intent": "product"},
    {"term": "horse float repairs loan", "audience": "consumer", "intent": "product"},
    {"term": "horse float trailer finance", "audience": "consumer", "intent": "product"},
    {"term": "horse float trailer loans", "audience": "consumer", "intent": "product"},
    {"term": "pool loan", "audience": "consumer", "intent": "product"},
    {"term": "pool payment plans", "audience": "consumer", "intent": "product"},
    {"term": "swimming pool finance", "audience": "consumer", "intent": "product"},
    {"term": "finance for a pool", "audience": "consumer", "intent": "product"},
    {"term": "pool installation finance", "audience": "consumer", "intent": "product"},
    {"term": "pool loan australia", "audience": "consumer", "intent": "product"},
    {"term": "home renovation loan", "audience": "consumer", "intent": "product"},
    {"term": "renovation finance options", "audience": "consumer", "intent": "product"},
    {"term": "finance for renovations", "audience": "consumer", "intent": "product"},
    {"term": "home improvement loan", "audience": "consumer", "intent": "product"},
    {"term": "renovation payment plans", "audience": "consumer", "intent": "product"},
    {"term": "need money to renovate", "audience": "consumer", "intent": "problem"},
    {"term": "tiny home loan", "audience": "consumer", "intent": "product"},
    {"term": "tiny home finance", "audience": "consumer", "intent": "product"},
    {"term": "tiny house loans", "audience": "consumer", "intent": "product"},
    {"term": "finance for a tiny home", "audience": "consumer", "intent": "product"},
    {"term": "tiny home loan australia", "audience": "consumer", "intent": "product"},
    {"term": "tiny house finance", "audience": "consumer", "intent": "product"},
    {"term": "trailer loan", "audience": "consumer", "intent": "product"},
    {"term": "trailer on finance", "audience": "consumer", "intent": "product"},
    {"term": "trailer payment plans", "audience": "consumer", "intent": "product"},
    {"term": "box trailer finance", "audience": "consumer", "intent": "product"},
    {"term": "car trailer loan", "audience": "consumer", "intent": "product"},
    {"term": "trailer finance australia", "audience": "consumer", "intent": "product"},
    {"term": "wedding loan", "audience": "consumer", "intent": "product"},
    {"term": "finance for a wedding", "audience": "consumer", "intent": "product"},
    {"term": "wedding payment plans", "audience": "consumer", "intent": "product"},
    {"term": "pay for wedding on finance", "audience": "consumer", "intent": "product"},
    {"term": "wedding loan australia", "audience": "consumer", "intent": "product"},
    {"term": "wedding costs loan", "audience": "consumer", "intent": "product"},
]


def _expand_templates(templates, audience, intent):
    terms = []
    for template in templates:
        for suffix in SUFFIXES:
            term = template.format(suffix=suffix).strip()
            terms.append({"term": term, "audience": audience, "intent": intent})
    return terms


def _dedupe_terms(terms):
    seen = set()
    deduped = []
    for entry in terms:
        key = entry["term"].strip().lower()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(entry)
    return deduped


SEED_TERMS = _dedupe_terms(
    _expand_templates(COMMERCIAL_TEMPLATES, "commercial", "product")
    + _expand_templates(CONSUMER_TEMPLATES, "consumer", "product")
    + PROBLEM_TERMS
    + EXTRA_TERMS
)
