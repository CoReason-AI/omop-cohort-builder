from __future__ import annotations

from typing import Protocol, List, Set, Dict

from omop_cohort_builder.domain import (
    CohortExpression,
    ConceptSetExpression,
)


class VocabularyProvider(Protocol):
    """
    Protocol for a vocabulary provider that resolves concept relationships.
    """

    def get_descendants(self, concept_ids: List[int]) -> Set[int]:
        """
        Returns a set of concept IDs that are descendants of the given concept IDs.
        Includes the original concept IDs themselves if they are valid.
        """
        ...

    def get_mapped(self, concept_ids: List[int]) -> Set[int]:
        """
        Returns a set of concept IDs that are mapped to the given concept IDs.
        """
        ...


class ConceptSetResolver:
    """
    Resolves ConceptSetExpressions into lists of Concept IDs using a VocabularyProvider.
    """

    def __init__(self, provider: VocabularyProvider | None = None):
        self.provider = provider

    def resolve_concept_set_expression(
        self, expression: ConceptSetExpression
    ) -> List[int]:
        """
        Resolves a single ConceptSetExpression into a flat list of distinct concept IDs.
        Logic mirrors Circe's implementation:
        1. Collect all Included concepts (Standard, Descendants, Mapped).
        2. Collect all Excluded concepts.
        3. Result = Included - Excluded.
        """
        included_concepts: Set[int] = set()
        excluded_concepts: Set[int] = set()

        # Group items by inclusion/exclusion to minimize vocabulary calls
        include_base: List[int] = []
        include_descendants: List[int] = []
        include_mapped: List[int] = []

        exclude_base: List[int] = []
        exclude_descendants: List[int] = []
        exclude_mapped: List[int] = []

        for item in expression.items:
            concept_id = item.concept.concept_id

            if item.is_excluded:
                exclude_base.append(concept_id)
                if item.include_descendants:
                    exclude_descendants.append(concept_id)
                if item.include_mapped:
                    exclude_mapped.append(concept_id)
            else:
                include_base.append(concept_id)
                if item.include_descendants:
                    include_descendants.append(concept_id)
                if item.include_mapped:
                    include_mapped.append(concept_id)

        # Resolve inclusions
        included_concepts.update(include_base)

        if self.provider:
            if include_descendants:
                included_concepts.update(
                    self.provider.get_descendants(include_descendants)
                )
            if include_mapped:
                included_concepts.update(self.provider.get_mapped(include_mapped))

        # Resolve exclusions
        excluded_concepts.update(exclude_base)

        if self.provider:
            if exclude_descendants:
                excluded_concepts.update(
                    self.provider.get_descendants(exclude_descendants)
                )
            if exclude_mapped:
                excluded_concepts.update(self.provider.get_mapped(exclude_mapped))

        # Apply exclusion
        final_set = included_concepts - excluded_concepts

        return sorted(list(final_set))

    def build_concept_set_map(
        self, cohort_expression: CohortExpression
    ) -> Dict[int, List[int]]:
        """
        Builds a map of {codesetId: [conceptIds]} for all ConceptSets in the CohortExpression.
        """
        concept_set_map: Dict[int, List[int]] = {}

        for concept_set in cohort_expression.concept_sets:
            # Handle both ConceptSetExpression object and potentially other types (Any)
            if isinstance(concept_set.expression, ConceptSetExpression):
                resolved_ids = self.resolve_concept_set_expression(
                    concept_set.expression
                )
                concept_set_map[concept_set.id] = resolved_ids
            # If expression is dict (raw JSON), we might need to parse it first.
            # But Pydantic should have handled this via the Union.
            # If it's something else, we skip or handle accordingly.

        return concept_set_map
