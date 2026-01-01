from typing import List, Set
from omop_cohort_builder.vocabulary import ConceptSetResolver, VocabularyProvider
from omop_cohort_builder.base import Concept
from omop_cohort_builder.domain import (
    ConceptSetExpression,
    ConceptSetItem,
    CohortExpression,
    ConceptSet,
)


class MockVocabularyProvider(VocabularyProvider):
    def __init__(self):
        self.descendants_map = {
            100: {100, 101, 102},  # 100 is parent of 101, 102
            200: {200, 201},
        }
        self.mapped_map = {
            300: {300, 3000},  # 300 maps to 3000
            400: {400, 4000},  # 400 maps to 4000
        }

    def get_descendants(self, concept_ids: List[int]) -> Set[int]:
        result = set()
        for cid in concept_ids:
            result.update(self.descendants_map.get(cid, {cid}))
        return result

    def get_mapped(self, concept_ids: List[int]) -> Set[int]:
        result = set()
        for cid in concept_ids:
            result.update(self.mapped_map.get(cid, set()))
        return result


def create_concept(concept_id: int) -> Concept:
    return Concept(CONCEPT_ID=concept_id, CONCEPT_NAME=f"Concept {concept_id}")


def test_resolve_simple_inclusion():
    resolver = ConceptSetResolver()
    expression = ConceptSetExpression(
        items=[
            ConceptSetItem(concept=create_concept(1)),
            ConceptSetItem(concept=create_concept(2)),
        ]
    )
    result = resolver.resolve_concept_set_expression(expression)
    assert result == [1, 2]


def test_resolve_exclusion():
    resolver = ConceptSetResolver()
    expression = ConceptSetExpression(
        items=[
            ConceptSetItem(concept=create_concept(1)),
            ConceptSetItem(concept=create_concept(2)),
            ConceptSetItem(concept=create_concept(1), is_excluded=True),
        ]
    )
    result = resolver.resolve_concept_set_expression(expression)
    assert result == [2]


def test_resolve_descendants():
    provider = MockVocabularyProvider()
    resolver = ConceptSetResolver(provider)
    expression = ConceptSetExpression(
        items=[
            ConceptSetItem(concept=create_concept(100), include_descendants=True),
        ]
    )
    result = resolver.resolve_concept_set_expression(expression)
    assert result == [100, 101, 102]


def test_resolve_mapped():
    provider = MockVocabularyProvider()
    resolver = ConceptSetResolver(provider)
    expression = ConceptSetExpression(
        items=[
            ConceptSetItem(concept=create_concept(300), include_mapped=True),
        ]
    )
    # 300 maps to 3000, and usually mapped implies standard, so 300 is included in base,
    # and 3000 comes from mapped.
    result = resolver.resolve_concept_set_expression(expression)
    assert 300 in result
    assert 3000 in result


def test_resolve_descendants_exclusion():
    provider = MockVocabularyProvider()
    resolver = ConceptSetResolver(provider)
    expression = ConceptSetExpression(
        items=[
            # Include 100 and its descendants (100, 101, 102)
            ConceptSetItem(concept=create_concept(100), include_descendants=True),
            # Exclude 102 explicitly
            ConceptSetItem(concept=create_concept(102), is_excluded=True),
        ]
    )
    result = resolver.resolve_concept_set_expression(expression)
    assert result == [100, 101]


def test_resolve_descendants_exclusion_recursive():
    provider = MockVocabularyProvider()
    resolver = ConceptSetResolver(provider)
    expression = ConceptSetExpression(
        items=[
            # Include 100 and its descendants (100, 101, 102)
            ConceptSetItem(concept=create_concept(100), include_descendants=True),
            # Exclude 200 and descendants (200, 201) - no overlap
            ConceptSetItem(
                concept=create_concept(200),
                include_descendants=True,
                is_excluded=True,
            ),
        ]
    )
    result = resolver.resolve_concept_set_expression(expression)
    assert result == [100, 101, 102]


def test_build_concept_set_map():
    provider = MockVocabularyProvider()
    resolver = ConceptSetResolver(provider)

    cs1 = ConceptSet(
        id=1,
        name="CS1",
        expression=ConceptSetExpression(
            items=[ConceptSetItem(concept=create_concept(1))]
        ),
    )
    cs2 = ConceptSet(
        id=2,
        name="CS2",
        expression=ConceptSetExpression(
            items=[
                ConceptSetItem(concept=create_concept(100), include_descendants=True)
            ]
        ),
    )

    # Minimal valid cohort object
    from omop_cohort_builder.domain import (
        PrimaryCriteria,
        ResultLimit,
        CollapseSettings,
    )

    cohort = CohortExpression(
        ConceptSets=[cs1, cs2],
        PrimaryCriteria=PrimaryCriteria(),
        QualifiedLimit=ResultLimit(),
        ExpressionLimit=ResultLimit(),
        CollapseSettings=CollapseSettings(),
    )

    map_result = resolver.build_concept_set_map(cohort)

    assert 1 in map_result
    assert map_result[1] == [1]

    assert 2 in map_result
    assert map_result[2] == [100, 101, 102]


def test_resolve_descendants_no_provider():
    # Test fallback behavior when provider is missing but expansion requested
    resolver = ConceptSetResolver(provider=None)
    expression = ConceptSetExpression(
        items=[
            ConceptSetItem(concept=create_concept(100), include_descendants=True),
        ]
    )
    # Should only return the base concept, skipping descendants
    result = resolver.resolve_concept_set_expression(expression)
    assert result == [100]


def test_build_concept_set_map_ignored_expression():
    resolver = ConceptSetResolver()

    # Create a ConceptSet with a non-ConceptSetExpression payload (e.g. raw dict or Any)
    cs1 = ConceptSet(
        id=1,
        name="CS1",
        expression={"foo": "bar"},  # Not a ConceptSetExpression instance
    )

    from omop_cohort_builder.domain import (
        PrimaryCriteria,
        ResultLimit,
        CollapseSettings,
    )

    cohort = CohortExpression(
        ConceptSets=[cs1],
        PrimaryCriteria=PrimaryCriteria(),
        QualifiedLimit=ResultLimit(),
        ExpressionLimit=ResultLimit(),
        CollapseSettings=CollapseSettings(),
    )

    map_result = resolver.build_concept_set_map(cohort)
    # Should be empty or not contain key 1 because we skip non-ConceptSetExpression
    assert 1 not in map_result


def test_resolve_empty_result():
    resolver = ConceptSetResolver()
    # Case 1: Empty items
    expression = ConceptSetExpression(items=[])
    result = resolver.resolve_concept_set_expression(expression)
    assert result == []

    # Case 2: Excluded matches included
    expression2 = ConceptSetExpression(
        items=[
            ConceptSetItem(concept=create_concept(1)),
            ConceptSetItem(concept=create_concept(1), is_excluded=True),
        ]
    )
    result2 = resolver.resolve_concept_set_expression(expression2)
    assert result2 == []


def test_resolve_simple_inclusion_with_provider():
    # Provider present but no descendants logic requested
    provider = MockVocabularyProvider()
    resolver = ConceptSetResolver(provider)
    expression = ConceptSetExpression(
        items=[
            ConceptSetItem(concept=create_concept(1)),
        ]
    )
    result = resolver.resolve_concept_set_expression(expression)
    assert result == [1]


def test_resolve_simple_exclusion_with_provider():
    # Provider present but no descendants logic requested on excluded item
    provider = MockVocabularyProvider()
    resolver = ConceptSetResolver(provider)
    expression = ConceptSetExpression(
        items=[
            ConceptSetItem(concept=create_concept(1)),
            ConceptSetItem(concept=create_concept(2), is_excluded=True),
        ]
    )
    result = resolver.resolve_concept_set_expression(expression)
    assert result == [1]


def test_resolve_mapped_exclusion():
    provider = MockVocabularyProvider()
    resolver = ConceptSetResolver(provider)
    expression = ConceptSetExpression(
        items=[
            # Include 400 and mapped (400, 4000)
            ConceptSetItem(concept=create_concept(400), include_mapped=True),
            # Exclude 400 and mapped (400, 4000) explicitly
            ConceptSetItem(
                concept=create_concept(400), include_mapped=True, is_excluded=True
            ),
        ]
    )
    result = resolver.resolve_concept_set_expression(expression)
    assert result == []

    # Mixed case: Include 400+mapped, exclude just 4000 via some other path (mocking collision)
    # Actually simpler: Include 400+mapped. Exclude 300+mapped (300, 3000). No overlap.
    expression2 = ConceptSetExpression(
        items=[
            ConceptSetItem(concept=create_concept(400), include_mapped=True),
            ConceptSetItem(
                concept=create_concept(300), include_mapped=True, is_excluded=True
            ),
        ]
    )
    result2 = resolver.resolve_concept_set_expression(expression2)
    assert 400 in result2
    assert 4000 in result2
    assert 300 not in result2
