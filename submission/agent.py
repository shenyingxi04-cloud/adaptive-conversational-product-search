from __future__ import annotations

import json
import math
import re
import sqlite3
from pathlib import Path


# ============================================================
# Tokenization
# ============================================================

TOKEN_RE = re.compile(r"[a-z0-9]+", re.IGNORECASE)


# V5.9:
# Add benchmark-template noise such as "key requirement".
STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "but", "by",
    "for", "from", "i", "in", "is", "it", "me", "my", "of",
    "on", "or", "please", "some", "that", "the", "this", "to",
    "want", "with", "would", "you", "looking", "need",
    "something", "like", "find", "show", "give", "can",
    "have", "has", "had", "do", "does", "did", "get", "got",
    "am", "im", "ive", "id", "ill", "just", "really",
    "very", "also", "one", "two", "any",
    "there", "here",

    # Evaluator/template noise
    "key",
    "requirement",
    "requirements",
    "additional",
    "preference",
    "preferences",
    "matters",
}


# ============================================================
# Attribute vocabulary
# ============================================================

ATTRIBUTE_VALUES = {

    "material": {
        "cotton",
        "polyester",
        "nylon",
        "leather",
        "wool",
        "spandex",
        "silk",
        "rayon",
        "alloy",
    },

    "color": {
        "black",
        "white",
        "blue",
        "red",
        "pink",
        "green",
        "brown",
        "gray",
        "grey",
        "purple",
        "yellow",
        "orange",
        "silver",
        "gold",
    },

    "use_case": {
        "running",
        "hiking",
        "gym",
        "outdoor",
        "winter",
        "work",
        "travel",
    },

    "style": {
        "fashion",
        "casual",
        "sport",
        "formal",
        "vintage",
        "classic",
        "modern",
    },
}


ASK_ORDER = [
    "material",
    "feature",
    "use_case",
    "color",
    "style",
    "size",
    "brand",
    "budget",
]


# ============================================================
# Normalization used for RERANKING only
# ============================================================

SYNONYMS = {

    "tee": "shirt",
    "tees": "shirt",
    "tshirt": "shirt",
    "tshirts": "shirt",

    "sneaker": "shoes",
    "sneakers": "shoes",
    "shoe": "shoes",

    "jacket": "coat",
    "jackets": "coat",

    "pants": "trousers",
    "pant": "trousers",

    "backpacks": "backpack",
    "bags": "bag",
    "bottles": "bottle",

    "headphones": "headphone",
    "earbuds": "earbud",

    "watches": "watch",
    "cameras": "camera",
    "laptops": "laptop",
    "phones": "phone",

    "dresses": "dress",
    "skirts": "skirt",
    "boots": "boot",
    "gloves": "glove",
    "socks": "sock",
}


STEM_SUFFIXES = (
    "ing",
    "ers",
    "er",
    "ed",
    "es",
    "s",
)


# ============================================================
# Intent
# ============================================================

BUYING_SIGNALS = [
    "buy",
    "purchase",
    "order",
    "must",
    "require",
    "requirement",
    "need to buy",
    "ready to buy",
    "i want to buy",
    "i need to buy",
    "going to buy",
    "looking to buy",
]


OVERRIDE_SIGNALS = [
    "ignore my earlier",
    "ignore earlier",
    "ignore what i said",
    "forget my earlier",
    "forget earlier",
    "forget what i said",
    "change my mind",
    "never mind",
    "no longer",
    "not anymore",
    "instead",
]


# ============================================================
# Generic helpers
# ============================================================

def _text(value: object) -> str:

    if value is None:
        return ""

    if isinstance(value, dict):

        return " ".join(
            f"{key} {item}"
            for key, item in value.items()
        )

    if isinstance(value, list):

        return " ".join(
            str(item)
            for item in value
        )

    return str(value)


# ============================================================
# V5.9 IMPORTANT:
#
# There are TWO tokenization paths.
#
# _fts_terms:
#     Retrieval.
#     NO stemming.
#
# _terms:
#     Reranking/comparison.
#     Existing normalized behavior.
# ============================================================

def _fts_terms(text: str) -> list[str]:
    """
    Surface-form tokens for SQLite FTS5.

    DO NOT STEM.

    Examples:
        running   -> running
        leather   -> leather
        polyester -> polyester

    This is the main V5.9 retrieval fix.
    """

    result = []

    for token in TOKEN_RE.findall(text):

        token = token.lower()

        if len(token) <= 1:
            continue

        if token in STOPWORDS:
            continue

        if token not in result:
            result.append(token)

    return result


def _normalize_token(token: str) -> str:
    """
    Lightweight normalization for reranking only.
    """

    token = token.lower()

    if token in SYNONYMS:
        token = SYNONYMS[token]

    if len(token) > 4:

        for suffix in STEM_SUFFIXES:

            if token.endswith(suffix):

                candidate = token[:-len(suffix)]

                if len(candidate) >= 3:
                    token = candidate

                break

    return token


def _terms(text: str) -> list[str]:
    """
    Normalized tokens for reranking.
    """

    result = []

    for token in TOKEN_RE.findall(text):

        token = token.lower()

        if len(token) <= 1:
            continue

        if token in STOPWORDS:
            continue

        token = _normalize_token(token)

        if token:
            result.append(token)

    return result


# ============================================================
# Constraint extraction
# ============================================================

def extract_constraints(
        text: str,
) -> dict[str, list[str]]:

    # Use SURFACE tokens here.
    terms = set(
        _fts_terms(text)
    )

    constraints: dict[
        str,
        list[str],
    ] = {}

    for attribute, values in ATTRIBUTE_VALUES.items():

        matches = [
            value
            for value in values
            if value in terms
        ]

        if matches:

            constraints[
                attribute
            ] = sorted(
                matches
            )

    return constraints


# ============================================================
# Category anchor
# ============================================================

def _category_fragment(
        text: str,
) -> str:

    lower = text.lower()

    marker = "looking for"

    if marker not in lower:
        return ""

    index = lower.find(marker)

    remainder = text[
                index + len(marker):
                ].strip()

    first_sentence = re.split(
        r"[.!?]",
        remainder,
        maxsplit=1,
    )[0]

    first_sentence = re.split(
        r"\ba key requirement\b",
        first_sentence,
        maxsplit=1,
        flags=re.IGNORECASE,
    )[0]

    return first_sentence.strip()


def extract_category_anchor(
        text: str,
) -> list[str]:
    """
    Normalized category anchor for reranking.
    """

    fragment = _category_fragment(
        text
    )

    if not fragment:
        return []

    return list(
        dict.fromkeys(
            _terms(fragment)
        )
    )[:8]


def extract_category_surface_terms(
        text: str,
) -> list[str]:
    """
    V5.9:
    Surface-form category terms for FTS retrieval.

    Running -> running
    Boots   -> boots
    Cases   -> cases
    """

    fragment = _category_fragment(
        text
    )

    if not fragment:
        return []

    return _fts_terms(
        fragment
    )[:8]


# ============================================================
# Non-informative replies
# ============================================================

def is_noninformative_reply(
        text: str,
) -> bool:

    lower = (
        text.lower()
        .strip()
    )

    signals = [

        "i don't have an additional preference for",

        "i do not have an additional preference for",

        "i don't have a preference for",

        "i do not have a preference for",

        "no additional preference",

        "no preference for",

        "those options are not quite right yet",

        "ask me about one specific attribute",
    ]

    return any(
        signal in lower
        for signal in signals
    )


# ============================================================
# Feature phrases
# ============================================================

def extract_feature_phrases(
        text: str,
) -> list[str]:

    lower = text.lower()

    markers = [

        "for that, what matters is:",

        "what matters is:",

        "a key requirement is:",

        "key requirement is:",

        "what i need is:",
    ]

    content = None

    for marker in markers:

        index = lower.find(
            marker
        )

        if index >= 0:

            content = text[
                      index + len(marker):
                      ]

            break

    if content is None:
        return []

    parts = re.split(
        r"[;|]",
        content.strip(),
    )

    phrases = []

    for part in parts:

        phrase = part.strip(
            " \t\r\n.,!?"
        )

        if not phrase:
            continue

        if is_noninformative_reply(
                phrase
        ):
            continue

        if phrase not in phrases:

            phrases.append(
                phrase
            )

    return phrases[:8]


def feature_phrase_terms(
        phrases: list[str],
) -> list[str]:

    result = []

    for phrase in phrases:

        for term in _terms(
                phrase
        ):

            if term not in result:

                result.append(
                    term
                )

    return result


def feature_phrase_fts_terms(
        phrases: list[str],
) -> list[str]:
    """
    Surface-form features for retrieval.
    """

    result = []

    for phrase in phrases:

        for term in _fts_terms(
                phrase
        ):

            if term not in result:

                result.append(
                    term
                )

    return result


# ============================================================
# Agent
# ============================================================

class Agent:
    """
    V5.9

    Main difference from V5.8:

    Retrieval and reranking no longer share the same
    stemmed tokens.

    Retrieval:
        surface-form FTS tokens.

    Reranking:
        normalized/stemmed tokens.

    This directly targets the V5.8 retrieval failures.
    """


    # ========================================================
    # Candidate configuration
    # ========================================================

    # V5.10e: retain more candidates from the existing routes.
    CANDIDATE_K = 250

    RECENT_TURN_COUNT = 3


    # V5.9 route quotas.
    GENERAL_ROUTE_K = 110

    CATEGORY_ROUTE_K = 70

    STRICT_FEATURE_ROUTE_K = 60

    STRICT_FEATURE_MATCH_BONUS = 1.0

    FEATURE_ROUTE_K = 60

    CONSTRAINT_ROUTE_K = 60

    BUYING_HARD_ROUTE_K = 70


    # ========================================================
    # Field weights
    # ========================================================

    FIELD_WEIGHTS = {

        "title": 7.0,

        "categories": 4.5,

        "features": 3.5,

        "details": 2.0,

        "store": 1.5,

        "description": 1.0,
    }


    # ========================================================
    # V5.8 scoring preserved
    # ========================================================

    COVERAGE_WEIGHT = 7.0

    TITLE_MATCH_WEIGHT = 3.0

    LATEST_TERM_BONUS = 1.5


    EXPLICIT_TITLE_BONUS = 16.0

    EXPLICIT_FIELD_BONUS = 6.0


    OLD_CONSTRAINT_TITLE_BONUS = 3.0

    OLD_CONSTRAINT_FIELD_BONUS = 1.0


    OLD_GENERAL_TITLE_BONUS = 1.5

    OLD_GENERAL_FIELD_BONUS = 0.5


    PROFILE_MATCH_WEIGHT = 0.50


    CURRENT_MISSING_PENALTY = 4.0

    CURRENT_COVERAGE_BONUS = 5.0


    BUYING_EXPLICIT_MULTIPLIER = 1.50

    BUYING_HARD_MATCH_BONUS = 10.0

    BUYING_MISSING_PENALTY = 10.0


    CATEGORY_TITLE_BONUS = 4.0

    CATEGORY_CATEGORY_BONUS = 5.0

    CATEGORY_GENERAL_BONUS = 1.0

    CATEGORY_COVERAGE_BONUS = 5.0


    FEATURE_TITLE_BONUS = 3.0

    FEATURE_FEATURES_BONUS = 8.0

    FEATURE_GENERAL_BONUS = 1.0

    FEATURE_COVERAGE_BONUS = 6.0

    FEATURE_EXACT_PHRASE_BONUS = 1.0

    SEMANTIC_SIMILARITY_WEIGHT = 2.0

    # A deliberately small, bounded browsing-only trust prior.  Review
    # volume is public catalog evidence and cannot outweigh intent matches.
    BROWSING_POPULARITY_WEIGHT = 0.5


    # ========================================================
    # Initialization
    # ========================================================

    def __init__(
            self,
            catalog_path: str | Path =
            "data/catalog.jsonl",
    ) -> None:

        self.catalog_path = Path(
            catalog_path
        )

        if not self.catalog_path.exists():

            raise FileNotFoundError(
                f"Catalog does not exist: "
                f"{self.catalog_path}"
            )

        self.connection = (
            sqlite3.connect(
                ":memory:"
            )
        )

        self._sessions: set[str] = set()

        self._session_state: dict[
            str,
            dict,
        ] = {}

        self._products: dict[
            str,
            dict[str, str],
        ] = {}

        self._build_index()

        self.semantic_model = None

        try:

            from model2vec import StaticModel

            agent_dir = Path(__file__).resolve().parent
            model_paths = (
                agent_dir / "models" / "potion-base-8M",
                agent_dir.parent
                / "submission"
                / "models"
                / "potion-base-8M",
                agent_dir.parent
                / "experiments"
                / "semantic"
                / "potion-base-8M",
            )
            model_path = next(
                (path for path in model_paths if path.exists()),
                None,
            )

            if model_path is not None:

                self.semantic_model = (
                    StaticModel.from_pretrained(
                        model_path,
                        normalize=True,
                        force_download=False,
                    )
                )

        except (ImportError, OSError, ValueError):

            self.semantic_model = None


    # ========================================================
    # Catalog index
    # ========================================================

    def _build_index(
            self,
    ) -> None:

        cursor = (
            self.connection.cursor()
        )

        cursor.execute(
            """
            CREATE VIRTUAL TABLE products
            USING fts5(
                parent_asin UNINDEXED,
                title,
                categories,
                features,
                details,
                store,
                description,
                tokenize='unicode61 remove_diacritics 2'
            )
            """
        )

        batch = []

        with self.catalog_path.open(
                encoding="utf-8",
                errors="replace",
        ) as handle:

            for line in handle:

                line = line.strip()

                if not line:
                    continue

                try:

                    product = json.loads(
                        line
                    )

                except json.JSONDecodeError:

                    continue

                parent_asin = str(
                    product.get(
                        "parent_asin",
                        "",
                    )
                )

                if not parent_asin:
                    continue


                title = _text(
                    product.get(
                        "title"
                    )
                )

                categories = _text(
                    product.get(
                        "categories"
                    )
                )

                features = _text(
                    product.get(
                        "features"
                    )
                )

                details = _text(
                    product.get(
                        "details"
                    )
                )

                store = _text(
                    product.get(
                        "store"
                    )
                )

                description = _text(
                    product.get(
                        "description"
                    )
                )

                try:
                    rating_number = max(
                        0,
                        int(product.get("rating_number", 0) or 0),
                    )
                except (TypeError, ValueError):
                    rating_number = 0


                self._products[
                    parent_asin
                ] = {

                    "title":
                        title,

                    "categories":
                        categories,

                    "features":
                        features,

                    "details":
                        details,

                    "store":
                        store,

                    "description":
                        description,

                    "rating_number":
                        rating_number,
                }


                batch.append(
                    (
                        parent_asin,
                        title,
                        categories,
                        features,
                        details,
                        store,
                        description,
                    )
                )


                if len(batch) >= 1000:

                    cursor.executemany(
                        """
                        INSERT INTO products
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        batch,
                    )

                    batch.clear()


        if batch:

            cursor.executemany(
                """
                INSERT INTO products
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                batch,
            )


        self.connection.commit()


    # ========================================================
    # Reset
    # ========================================================

    def reset(
            self,
            session_id: str,
            user_profile: dict,
    ) -> None:

        self._sessions.add(
            session_id
        )

        self._session_state[
            session_id
        ] = {

            "user_profile":
                user_profile,

            "history":
                [],

            "search_history":
                [],

            # Normalized version for ranking.
            "category_anchor_terms":
                [],

            # V5.9:
            # Surface version for FTS.
            "category_surface_terms":
                [],

            "constraints":
                {},

            "current_constraints":
                {},

            "explicit_constraints":
                {},

            "feature_phrases":
                [],

            "asked_attributes":
                set(),

            "mode":
                "browsing",

            "override_active":
                False,
        }


    # ========================================================
    # Intent detection
    # ========================================================

    def _is_override(
            self,
            user_message: str,
    ) -> bool:

        text = (
            user_message.lower()
        )

        return any(
            signal in text
            for signal in OVERRIDE_SIGNALS
        )


    def _is_buying(
            self,
            user_message: str,
    ) -> bool:

        text = (
            user_message.lower()
        )

        return any(
            signal in text
            for signal in BUYING_SIGNALS
        )


    # ========================================================
    # Attribute selection
    # ========================================================

    def choose_attribute(
            self,
            state: dict,
    ) -> str | None:

        asked = state[
            "asked_attributes"
        ]

        constraints = state[
            "constraints"
        ]

        for attribute in ASK_ORDER:

            if attribute in asked:
                continue

            if attribute in constraints:
                continue

            asked.add(
                attribute
            )

            return attribute

        return None


    # ========================================================
    # Search history
    # ========================================================

    def _store_search_message(
            self,
            state: dict,
            user_message: str,
    ) -> None:

        if is_noninformative_reply(
                user_message
        ):
            return

        state[
            "search_history"
        ].append(
            user_message
        )


    # ========================================================
    # Reranking query
    # ========================================================

    def _build_query(
            self,
            state: dict,
    ) -> list[str]:

        """
        Normalized terms.
        Used by reranker.
        """

        result = []


        for term in state.get(
                "category_anchor_terms",
                [],
        ):

            if term not in result:

                result.append(
                    term
                )


        search_history = state.get(
            "search_history",
            [],
        )


        recent_history = (
            search_history[
            -self.RECENT_TURN_COUNT:
            ]
        )


        for term in _terms(
                " ".join(
                    recent_history
                )
        ):

            if term not in result:

                result.append(
                    term
                )


        for values in state.get(
                "constraints",
                {},
        ).values():

            for value in values:

                normalized = (
                    _normalize_token(
                        value
                    )
                )

                if normalized not in result:

                    result.append(
                        normalized
                    )


        for term in feature_phrase_terms(
                state.get(
                    "feature_phrases",
                    [],
                )
        ):

            if term not in result:

                result.append(
                    term
                )


        return result[:40]


    # ========================================================
    # V5.9 FTS query construction
    # ========================================================

    def _build_fts_query_terms(
            self,
            state: dict,
    ) -> list[str]:

        """
        Surface-form query for candidate retrieval.
        """

        result = []


        # ----------------------------------------------------
        # Category surface terms
        # ----------------------------------------------------

        for term in state.get(
                "category_surface_terms",
                [],
        ):

            if term not in result:

                result.append(
                    term
                )


        # ----------------------------------------------------
        # Recent informative raw messages
        # ----------------------------------------------------

        search_history = state.get(
            "search_history",
            [],
        )


        recent_history = (
            search_history[
            -self.RECENT_TURN_COUNT:
            ]
        )


        for term in _fts_terms(
                " ".join(
                    recent_history
                )
        ):

            if term not in result:

                result.append(
                    term
                )


        # ----------------------------------------------------
        # Constraints:
        # use ORIGINAL values.
        #
        # polyester stays polyester.
        # leather stays leather.
        # running stays running.
        # ----------------------------------------------------

        for values in state.get(
                "constraints",
                {},
        ).values():

            for value in values:

                for term in _fts_terms(
                        value
                ):

                    if term not in result:

                        result.append(
                            term
                        )


        # ----------------------------------------------------
        # Persistent features
        # ----------------------------------------------------

        for term in feature_phrase_fts_terms(
                state.get(
                    "feature_phrases",
                    [],
                )
        ):

            if term not in result:

                result.append(
                    term
                )


        return result[:40]


    # ========================================================
    # Latest terms for reranking
    # ========================================================

    def _latest_terms(
            self,
            state: dict,
    ) -> set[str]:

        history = state.get(
            "search_history",
            [],
        )

        if not history:
            return set()

        return set(
            _terms(
                history[-1]
            )
        )


    # ========================================================
    # FTS primitive
    # ========================================================

    def _retrieve_expression(
            self,
            expression: str,
            candidate_k: int,
    ) -> list[str]:

        if not expression:
            return []

        try:

            rows = (
                self.connection.execute(
                    """
                    SELECT parent_asin
                    FROM products
                    WHERE products MATCH ?
                    ORDER BY bm25(
                        products,
                        0.0,
                        7.0,
                        4.5,
                        3.5,
                        2.0,
                        1.5,
                        1.0
                    )
                    LIMIT ?
                    """,
                    (
                        expression,
                        candidate_k,
                    ),
                )
                .fetchall()
            )

        except sqlite3.OperationalError:

            return []


        return [
            str(row[0])
            for row in rows
        ]


    # ========================================================
    # Merge routes
    # ========================================================

    def _merge_routes(
            self,
            routes: list[list[str]],
    ) -> list[str]:

        result = []

        seen = set()


        max_length = max(
            (
                len(route)
                for route in routes
            ),
            default=0,
        )


        for index in range(
                max_length
        ):

            for route in routes:

                if index >= len(route):
                    continue

                asin = route[
                    index
                ]

                if asin in seen:
                    continue

                seen.add(
                    asin
                )

                result.append(
                    asin
                )

                if (
                        len(result)
                        >= self.CANDIDATE_K
                ):

                    return result


        return result


    # ========================================================
    # V5.9 multi-route retrieval
    # ========================================================

    def _retrieve_candidates(
            self,
            query_terms: list[str],
            state: dict,
    ) -> list[str]:

        """
        query_terms is kept in the signature for compatibility
        with the debug tools.

        Actual FTS retrieval uses SURFACE terms.
        """

        fts_query_terms = (
            self._build_fts_query_terms(
                state
            )
        )


        if not fts_query_terms:
            return []


        routes = []

        state["strict_feature_candidates"] = set()


        mode = state.get(
            "mode",
            "browsing",
        )


        category_terms = list(
            dict.fromkeys(
                state.get(
                    "category_surface_terms",
                    [],
                )
            )
        )


        constraint_terms = []

        for values in state.get(
                "constraints",
                {},
        ).values():

            for value in values:

                for term in _fts_terms(
                        value
                ):

                    if term not in constraint_terms:

                        constraint_terms.append(
                            term
                        )


        feature_terms = (
            feature_phrase_fts_terms(
                state.get(
                    "feature_phrases",
                    [],
                )
            )
        )


        # ====================================================
        # Route 1:
        # Buying hard constraints
        # ====================================================

        if mode == "buying":

            current_constraints = (
                state.get(
                    "current_constraints",
                    {},
                )
            )

            hard_terms = []

            for values in (
                    current_constraints.values()
            ):

                for value in values:

                    for term in _fts_terms(
                            value
                    ):

                        if term not in hard_terms:

                            hard_terms.append(
                                term
                            )


            if hard_terms:

                expression = (
                    " AND ".join(
                        f'"{term}"'
                        for term in hard_terms
                    )
                )


                route = (
                    self._retrieve_expression(
                        expression,
                        self.BUYING_HARD_ROUTE_K,
                    )
                )


                if route:

                    routes.append(
                        route
                    )


        # ====================================================
        # Route 2 — V5.11:
        # Field-scoped strict category and feature route
        # ====================================================

        strict_feature_terms = [
            term
            for term in feature_terms
            if term not in {
                "color",
                "material",
                "style",
                "size",
                "brand",
                "budget",
                "feature",
                "use",
                "case",
            }
        ]

        if (
                len(category_terms) >= 2
                and len(strict_feature_terms) >= 2
        ):

            category_part = (
                    "categories : ("
                    + " AND ".join(
                f'"{term}"'
                for term in category_terms
            )
                    + ")"
            )

            feature_part = (
                    "{title features details} : ("
                    + " AND ".join(
                f'"{term}"'
                for term in strict_feature_terms
            )
                    + ")"
            )

            expression = (
                    category_part
                    + " AND "
                    + feature_part
            )

            route = (
                self._retrieve_expression(
                    expression,
                    self.STRICT_FEATURE_ROUTE_K,
                )
            )

            if route:

                state[
                    "strict_feature_candidates"
                ] = set(route)

                routes.append(
                    route
                )


        # ====================================================
        # Route 3:
        # Category-only
        # ====================================================

        if category_terms:

            expression = (
                " OR ".join(
                    f'"{term}"'
                    for term in category_terms
                )
            )


            route = (
                self._retrieve_expression(
                    expression,
                    self.CATEGORY_ROUTE_K,
                )
            )


            if route:

                routes.append(
                    route
                )


        # ====================================================
        # Route 3:
        # Category AND constraint
        # ====================================================

        if (
                category_terms
                and constraint_terms
        ):

            category_part = (
                    "("
                    + " OR ".join(
                f'"{term}"'
                for term in category_terms
            )
                    + ")"
            )


            constraint_part = (
                    "("
                    + " OR ".join(
                f'"{term}"'
                for term in constraint_terms
            )
                    + ")"
            )


            expression = (
                    category_part
                    + " AND "
                    + constraint_part
            )


            route = (
                self._retrieve_expression(
                    expression,
                    self.CATEGORY_ROUTE_K,
                )
            )


            if route:

                routes.append(
                    route
                )


        # ====================================================
        # Route 4:
        # Category AND feature
        # ====================================================

        if (
                category_terms
                and feature_terms
        ):

            category_part = (
                    "("
                    + " OR ".join(
                f'"{term}"'
                for term in category_terms
            )
                    + ")"
            )


            feature_part = (
                    "("
                    + " OR ".join(
                f'"{term}"'
                for term in feature_terms
            )
                    + ")"
            )


            expression = (
                    category_part
                    + " AND "
                    + feature_part
            )


            route = (
                self._retrieve_expression(
                    expression,
                    self.FEATURE_ROUTE_K,
                )
            )


            if route:

                routes.append(
                    route
                )


        # ====================================================
        # Route 5:
        # Feature route
        # ====================================================

        if feature_terms:

            expression = (
                " OR ".join(
                    f'"{term}"'
                    for term in feature_terms
                )
            )


            route = (
                self._retrieve_expression(
                    expression,
                    self.FEATURE_ROUTE_K,
                )
            )


            if route:

                routes.append(
                    route
                )


        # ====================================================
        # Route 6:
        # Constraint route
        # ====================================================

        if constraint_terms:

            expression = (
                " OR ".join(
                    f'"{term}"'
                    for term in constraint_terms
                )
            )


            route = (
                self._retrieve_expression(
                    expression,
                    self.CONSTRAINT_ROUTE_K,
                )
            )


            if route:

                routes.append(
                    route
                )


        # ====================================================
        # Route 7:
        # General surface-form lexical route
        # ====================================================

        expression = (
            " OR ".join(
                f'"{term}"'
                for term in fts_query_terms
            )
        )


        route = (
            self._retrieve_expression(
                expression,
                self.GENERAL_ROUTE_K,
            )
        )


        if route:

            routes.append(
                route
            )


        return self._merge_routes(
            routes
        )[
               :self.CANDIDATE_K
               ]


    # ========================================================
    # Product normalization for reranking
    # ========================================================

    def _field_terms(
            self,
            text: str,
    ) -> set[str]:

        return set(
            _terms(
                text
            )
        )


    # ========================================================
    # Profile terms
    # ========================================================

    def _profile_terms(
            self,
            state: dict,
    ) -> set[str]:

        profile = state.get(
            "user_profile",
            {},
        )

        result = set()


        tags = profile.get(
            "preference_tags",
            [],
        )


        if isinstance(
                tags,
                list,
        ):

            for tag in tags:

                result.update(
                    _terms(
                        str(tag)
                    )
                )


        summary = profile.get(
            "summary",
            "",
        )


        if summary:

            result.update(
                _terms(
                    str(summary)
                )
            )


        return result


    # ========================================================
    # Scoring
    #
    # V5.8 reranker intentionally preserved.
    # ========================================================

    def _score_candidate(
            self,
            parent_asin: str,
            query_terms: list[str],
            state: dict,
    ) -> float:

        product = (
            self._products.get(
                parent_asin
            )
        )

        if not product:

            return float(
                "-inf"
            )


        if not query_terms:

            return 0.0


        query_set = set(
            query_terms
        )


        total_score = 0.0


        mode = state.get(
            "mode",
            "browsing",
        )


        # ====================================================
        # Field terms
        # ====================================================

        field_term_sets = {

            field:
                self._field_terms(
                    product.get(
                        field,
                        "",
                    )
                )

            for field
            in self.FIELD_WEIGHTS
        }


        all_product_terms = set()


        for terms in (
                field_term_sets.values()
        ):

            all_product_terms.update(
                terms
            )


        # ====================================================
        # Generic field matching
        # ====================================================

        matched_terms = set()


        for field, weight in (
                self.FIELD_WEIGHTS.items()
        ):

            overlap = (
                query_set
                .intersection(
                    field_term_sets[
                        field
                    ]
                )
            )


            if overlap:

                total_score += (
                        weight
                        * len(
                    overlap
                )
                )

                matched_terms.update(
                    overlap
                )


        # ====================================================
        # Coverage
        # ====================================================

        coverage = (
                len(
                    matched_terms
                )
                /
                max(
                    len(
                        query_set
                    ),
                    1,
                )
        )


        total_score += (
                coverage
                * self.COVERAGE_WEIGHT
        )


        # ====================================================
        # Title
        # ====================================================

        title_terms = (
            field_term_sets[
                "title"
            ]
        )


        title_overlap = (
            query_set
            .intersection(
                title_terms
            )
        )


        if title_overlap:

            total_score += (
                    self.TITLE_MATCH_WEIGHT
                    * len(
                title_overlap
            )
            )


        # ====================================================
        # Latest
        # ====================================================

        latest_terms = (
            self._latest_terms(
                state
            )
        )


        latest_overlap = (
            latest_terms
            .intersection(
                title_terms
            )
        )


        if latest_overlap:

            total_score += (
                    self.LATEST_TERM_BONUS
                    * len(
                latest_overlap
            )
            )


        # ====================================================
        # Structured constraints
        # ====================================================

        constraints = state.get(
            "constraints",
            {},
        )


        current_constraints = (
            state.get(
                "current_constraints",
                {},
            )
        )


        explicit_constraints = (
            state.get(
                "explicit_constraints",
                {},
            )
        )


        current_required = 0

        current_matched = 0


        for attribute, values in (
                constraints.items()
        ):

            for value in values:

                normalized = (
                    _normalize_token(
                        value
                    )
                )


                if not normalized:
                    continue


                in_title = (
                        normalized
                        in title_terms
                )


                in_product = (
                        normalized
                        in all_product_terms
                )


                is_current = (
                        value
                        in current_constraints.get(
                    attribute,
                    [],
                )
                )


                is_explicit = (
                        value
                        in explicit_constraints.get(
                    attribute,
                    [],
                )
                )


                if is_current:

                    current_required += 1


                    multiplier = (
                        self.BUYING_EXPLICIT_MULTIPLIER
                        if mode == "buying"
                        else 1.0
                    )


                    if in_title:

                        current_matched += 1

                        total_score += (
                                self.EXPLICIT_TITLE_BONUS
                                * multiplier
                        )


                    elif in_product:

                        current_matched += 1

                        total_score += (
                                self.EXPLICIT_FIELD_BONUS
                                * multiplier
                        )


                    else:

                        total_score -= (
                                self.CURRENT_MISSING_PENALTY
                                * multiplier
                        )


                elif is_explicit:

                    if in_title:

                        total_score += (
                            self.OLD_CONSTRAINT_TITLE_BONUS
                        )

                    elif in_product:

                        total_score += (
                            self.OLD_CONSTRAINT_FIELD_BONUS
                        )


                else:

                    if in_title:

                        total_score += (
                            self.OLD_GENERAL_TITLE_BONUS
                        )

                    elif in_product:

                        total_score += (
                            self.OLD_GENERAL_FIELD_BONUS
                        )


        # ====================================================
        # Current constraint coverage
        # ====================================================

        if current_required > 0:

            ratio = (
                    current_matched
                    /
                    current_required
            )


            total_score += (
                    ratio
                    * self.CURRENT_COVERAGE_BONUS
            )


            if mode == "buying":

                if (
                        current_matched
                        == current_required
                ):

                    total_score += (
                        self.BUYING_HARD_MATCH_BONUS
                    )


                else:

                    missing = (
                            current_required
                            - current_matched
                    )


                    total_score -= (
                            self.BUYING_MISSING_PENALTY
                            * missing
                    )


        # ====================================================
        # Category anchor scoring
        # ====================================================

        category_anchor_terms = set(
            state.get(
                "category_anchor_terms",
                [],
            )
        )


        if category_anchor_terms:

            category_title_overlap = (
                category_anchor_terms
                .intersection(
                    title_terms
                )
            )


            category_category_overlap = (
                category_anchor_terms
                .intersection(
                    field_term_sets[
                        "categories"
                    ]
                )
            )


            category_product_overlap = (
                category_anchor_terms
                .intersection(
                    all_product_terms
                )
            )


            total_score += (
                    self.CATEGORY_TITLE_BONUS
                    * len(
                category_title_overlap
            )
            )


            total_score += (
                    self.CATEGORY_CATEGORY_BONUS
                    * len(
                category_category_overlap
            )
            )


            other_matches = (
                    category_product_overlap
                    - category_title_overlap
                    - category_category_overlap
            )


            total_score += (
                    self.CATEGORY_GENERAL_BONUS
                    * len(
                other_matches
            )
            )


            category_coverage = (
                    len(
                        category_product_overlap
                    )
                    /
                    max(
                        len(
                            category_anchor_terms
                        ),
                        1,
                    )
            )


            total_score += (
                    category_coverage
                    * self.CATEGORY_COVERAGE_BONUS
            )


        # ====================================================
        # Feature scoring
        # ====================================================

        feature_terms = set(
            feature_phrase_terms(
                state.get(
                    "feature_phrases",
                    [],
                )
            )
        )


        if feature_terms:

            feature_title_overlap = (
                feature_terms
                .intersection(
                    title_terms
                )
            )


            feature_field_overlap = (
                feature_terms
                .intersection(
                    field_term_sets[
                        "features"
                    ]
                )
            )


            feature_product_overlap = (
                feature_terms
                .intersection(
                    all_product_terms
                )
            )


            total_score += (
                    self.FEATURE_TITLE_BONUS
                    * len(
                feature_title_overlap
            )
            )


            total_score += (
                    self.FEATURE_FEATURES_BONUS
                    * len(
                feature_field_overlap
            )
            )


            other_matches = (
                    feature_product_overlap
                    - feature_title_overlap
                    - feature_field_overlap
            )


            total_score += (
                    self.FEATURE_GENERAL_BONUS
                    * len(
                other_matches
            )
            )


            feature_coverage = (
                    len(
                        feature_product_overlap
                    )
                    /
                    max(
                        len(
                            feature_terms
                        ),
                        1,
                    )
            )


            total_score += (
                    feature_coverage
                    * self.FEATURE_COVERAGE_BONUS
            )


            # Reward a multi-word feature phrase only when its
            # normalized terms occur contiguously in the Features field.
            normalized_feature_text = (
                " "
                + " ".join(
                    _terms(
                        product.get(
                            "features",
                            "",
                        )
                    )
                )
                + " "
            )

            for phrase in state.get(
                    "feature_phrases",
                    [],
            ):

                phrase_terms = _terms(
                    phrase
                )

                if (
                        len(phrase_terms) >= 2
                        and (
                            " "
                            + " ".join(phrase_terms)
                            + " "
                        ) in normalized_feature_text
                ):

                    total_score += (
                        self.FEATURE_EXACT_PHRASE_BONUS
                    )


        # ====================================================
        # Profile
        # ====================================================

        profile_terms = (
            self._profile_terms(
                state
            )
        )


        if profile_terms:

            total_score += (
                    self.PROFILE_MATCH_WEIGHT
                    * len(
                profile_terms
                .intersection(
                    all_product_terms
                )
            )
            )


        # ====================================================
        # Rating style
        # ====================================================

        rating_style = str(
            state.get(
                "user_profile",
                {},
            ).get(
                "rating_style",
                "",
            )
        ).lower()


        if (
                rating_style
                == "critical"
                and title_overlap
        ):

            total_score += 0.50


        elif (
                rating_style
                == "usually positive"
                and matched_terms
        ):

            total_score += 0.25


        if parent_asin in state.get(
                "strict_feature_candidates",
                set(),
        ):

            total_score += (
                self.STRICT_FEATURE_MATCH_BONUS
            )

        if mode == "browsing":
            # Saturates at 100k reviews, contributing at most 0.5 point.
            # This acts as a tie-breaker among similarly relevant products.
            review_count = int(
                product.get("rating_number", 0) or 0
            )
            total_score += (
                self.BROWSING_POPULARITY_WEIGHT
                * min(math.log1p(review_count) / math.log1p(100_000), 1.0)
            )


        return total_score


    # ========================================================
    # Reranking
    # ========================================================

    def _rerank(
            self,
            candidate_ids: list[str],
            query_terms: list[str],
            state: dict,
            top_k: int,
    ) -> list[dict]:

        scored = []

        seen = set()


        for parent_asin in candidate_ids:

            if parent_asin in seen:
                continue

            seen.add(
                parent_asin
            )


            score = (
                self._score_candidate(
                    parent_asin,
                    query_terms,
                    state,
                )
            )


            scored.append(
                (
                    score,
                    parent_asin,
                )
            )


        if (
                self.semantic_model is not None
                and state.get("mode") == "browsing"
                and len(scored) >= 2
        ):

            query_parts = [
                " ".join(
                    state.get(
                        "category_surface_terms",
                        [],
                    )
                )
            ]

            for values in state.get(
                    "constraints",
                    {},
            ).values():

                query_parts.extend(values)

            query_parts.extend(
                state.get(
                    "feature_phrases",
                    [],
                )
            )

            semantic_query = " | ".join(
                part
                for part in query_parts
                if part
            )

            if semantic_query:

                semantic_ids = [
                    parent_asin
                    for _, parent_asin in scored
                ]

                semantic_texts = []

                for parent_asin in semantic_ids:

                    product = self._products[parent_asin]

                    semantic_texts.append(
                        " | ".join(
                            [
                                product.get("title", ""),
                                product.get("categories", ""),
                                product.get("features", "")[:600],
                            ]
                        )
                    )

                try:

                    query_vector = (
                        self.semantic_model.encode(
                            [semantic_query]
                        )[0]
                    )

                    product_vectors = (
                        self.semantic_model.encode(
                            semantic_texts
                        )
                    )

                    semantic_scores = {
                        parent_asin: float(
                            product_vectors[index]
                            @ query_vector
                        )
                        for index, parent_asin
                        in enumerate(semantic_ids)
                    }

                    scored = [
                        (
                            score
                            + self.SEMANTIC_SIMILARITY_WEIGHT
                            * semantic_scores[parent_asin],
                            parent_asin,
                        )
                        for score, parent_asin in scored
                    ]

                except (
                        MemoryError,
                        RuntimeError,
                        TypeError,
                        ValueError,
                ):

                    pass


        scored.sort(
            key=lambda item: (
                -item[0],
                item[1],
            )
        )


        return [

            {
                "parent_asin":
                    parent_asin,

                "score":
                    round(
                        score,
                        6,
                    ),
            }

            for score, parent_asin
            in scored[:top_k]
        ]


    # ========================================================
    # Fallback
    # ========================================================

    def _fallback_candidates(
            self,
            state: dict,
            query_terms: list[str],
    ) -> list[str]:

        candidates = []


        category_terms = set(
            state.get(
                "category_anchor_terms",
                [],
            )
        )


        feature_terms = set(
            feature_phrase_terms(
                state.get(
                    "feature_phrases",
                    [],
                )
            )
        )


        constraint_terms = set()


        for values in state.get(
                "constraints",
                {},
        ).values():

            for value in values:

                constraint_terms.update(
                    _terms(
                        value
                    )
                )


        for parent_asin, product in (
                self._products.items()
        ):

            title_terms = (
                self._field_terms(
                    product.get(
                        "title",
                        "",
                    )
                )
            )


            product_terms = (
                self._field_terms(
                    " ".join(
                        product.values()
                    )
                )
            )


            score = 0.0


            for term in query_terms:

                if term in title_terms:

                    score += 5.0

                elif term in product_terms:

                    score += 1.0


            for term in category_terms:

                if term in title_terms:

                    score += 8.0

                elif term in product_terms:

                    score += 3.0


            for term in constraint_terms:

                if term in title_terms:

                    score += 8.0

                elif term in product_terms:

                    score += 3.0


            for term in feature_terms:

                if term in title_terms:

                    score += 5.0

                elif term in product_terms:

                    score += 2.0


            if score > 0:

                candidates.append(
                    (
                        -score,
                        parent_asin,
                    )
                )


        candidates.sort()


        return [

            parent_asin

            for _, parent_asin
            in candidates[
               :self.CANDIDATE_K
               ]
        ]


    # ========================================================
    # Main API
    # ========================================================

    def respond(
            self,
            session_id: str,
            user_message: str,
            turn: int,
            top_k: int,
    ) -> dict:


        if session_id not in (
                self._sessions
        ):

            raise RuntimeError(
                "reset must be called "
                "before respond"
            )


        state = (
            self._session_state[
                session_id
            ]
        )


        # ====================================================
        # Intent
        # ====================================================

        override = (
            self._is_override(
                user_message
            )
        )


        buying = (
            self._is_buying(
                user_message
            )
        )


        # ====================================================
        # Category anchors
        # ====================================================

        if not state[
            "category_anchor_terms"
        ]:

            normalized_anchor = (
                extract_category_anchor(
                    user_message
                )
            )


            surface_anchor = (
                extract_category_surface_terms(
                    user_message
                )
            )


            if normalized_anchor:

                state[
                    "category_anchor_terms"
                ] = normalized_anchor


            if surface_anchor:

                state[
                    "category_surface_terms"
                ] = surface_anchor


        # ====================================================
        # Override
        # ====================================================

        if override:

            state[
                "override_active"
            ] = True


            state[
                "mode"
            ] = "intent_override"


            # IMPORTANT:
            # preserve BOTH category anchors.
            state[
                "constraints"
            ] = {}


            state[
                "current_constraints"
            ] = {}


            state[
                "explicit_constraints"
            ] = {}


            state[
                "feature_phrases"
            ] = []


            state[
                "search_history"
            ] = []


            state[
                "asked_attributes"
            ] = set()


        # ====================================================
        # History
        # ====================================================

        state[
            "history"
        ].append(
            user_message
        )


        self._store_search_message(
            state,
            user_message,
        )


        # ====================================================
        # Mode
        # ====================================================

        if override:

            state[
                "mode"
            ] = "intent_override"


        elif buying:

            state[
                "mode"
            ] = "buying"


        elif state.get(
                "override_active"
        ):

            state[
                "mode"
            ] = "intent_override"


        else:

            state[
                "mode"
            ] = "browsing"


        # ====================================================
        # Constraints
        # ====================================================

        new_constraints = (
            extract_constraints(
                user_message
            )
        )


        state[
            "current_constraints"
        ] = {

            attribute:
                list(values)

            for attribute, values
            in new_constraints.items()
        }


        for attribute, values in (
                new_constraints.items()
        ):

            state[
                "constraints"
            ].setdefault(
                attribute,
                [],
            )


            state[
                "explicit_constraints"
            ].setdefault(
                attribute,
                [],
            )


            for value in values:

                if value not in state[
                    "constraints"
                ][attribute]:

                    state[
                        "constraints"
                    ][attribute].append(
                        value
                    )


                if value not in state[
                    "explicit_constraints"
                ][attribute]:

                    state[
                        "explicit_constraints"
                    ][attribute].append(
                        value
                    )


        if override:

            state[
                "constraints"
            ] = {

                attribute:
                    list(values)

                for attribute, values
                in new_constraints.items()
            }


            state[
                "explicit_constraints"
            ] = {

                attribute:
                    list(values)

                for attribute, values
                in new_constraints.items()
            }


        # ====================================================
        # Features
        # ====================================================

        new_features = (
            extract_feature_phrases(
                user_message
            )
        )


        for phrase in new_features:

            if phrase not in state[
                "feature_phrases"
            ]:

                state[
                    "feature_phrases"
                ].append(
                    phrase
                )


        state[
            "feature_phrases"
        ] = state[
                "feature_phrases"
            ][-12:]


        # ====================================================
        # Normalized reranking query
        # ====================================================

        query_terms = (
            self._build_query(
                state
            )
        )


        # ====================================================
        # Surface-form FTS retrieval
        # ====================================================

        candidate_ids = (
            self._retrieve_candidates(
                query_terms,
                state,
            )
        )


        if not candidate_ids:

            candidate_ids = (
                self._fallback_candidates(
                    state,
                    query_terms,
                )
            )


        # ====================================================
        # Rerank
        # ====================================================

        recommendations = (
            self._rerank(
                candidate_ids,
                query_terms,
                state,
                top_k,
            )
        )


        # ====================================================
        # Question
        # ====================================================

        ask_attribute = (
            self.choose_attribute(
                state
            )
        )


        # ====================================================
        # Response
        # ====================================================

        if (
                state["mode"]
                == "intent_override"
        ):

            message = (
                "Understood. I'll use your "
                "updated preferences for these "
                "recommendations."
            )


        elif (
                state["mode"]
                == "buying"
        ):

            message = (
                "Here are the closest matches "
                "based on your requirements."
            )


        else:

            message = (
                "Here are the closest matches "
                "based on your preferences."
            )


        return {

            "message":
                message,

            "ask_attribute":
                ask_attribute,

            "recommendations":
                recommendations,

            "usage": {

                "prompt_tokens": 0,

                "completion_tokens": 0,
            },
        }
