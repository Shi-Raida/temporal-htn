"""Tests on HtnEntity."""

from __future__ import annotations

import inspect
import sys
from dataclasses import dataclass
from unittest import TestCase

import temporal_htn.htn as htnf


@dataclass(frozen=True)
class MockHtnEntity(htnf.HtnEntity):
    """A mock HTN Entity for tests."""

    # pylint: disable=disallowed-name

    set_attr: set[str]
    bool_attr: bool
    int_attr: int
    tuple_attr: tuple[int, ...]
    list_attr: list[int]
    dict_attr: dict[str, int]


class HtnEntityTest(TestCase):
    """Regroup all tests related to HTN Entities."""

    def test_is_base_class(self) -> None:
        """Check that [HtnEntity] is the base class of the whole formalism."""
        # arrange
        excluded_classes = [
            htnf.HtnTemporalIntervalFactory,
            htnf.HtnEffectFactory,
            htnf.ConstraintArgumentError,
            htnf.HtnConstraintFactory,
        ]  # Just helper classes
        htnf_class_pairs = inspect.getmembers(
            sys.modules[htnf.__name__], inspect.isclass
        )
        htnf_classes = [
            htnf_class_pair[1]
            for htnf_class_pair in htnf_class_pairs
            if htnf_class_pair[1] not in excluded_classes
        ]
        # assert
        for htnf_class in htnf_classes:
            self.assertTrue(
                issubclass(htnf_class, htnf.HtnEntity),
                f"{htnf_class.__name__} does not inherit from HtnEntity",
            )

    def test_copy_with(self) -> None:
        """
        Check that copy_with() returns a copy
        where the specified arguments are overridden
        without updating the original entity.
        """
        # arrange
        entity = MockHtnEntity({"foo"}, True, 1, (1, 2), [1, 2], {"1": 1})
        # act
        entity_copied = entity.copy_with(set_attr={"bar"})
        # assert
        self.assertIsInstance(entity_copied, MockHtnEntity)
        self.assertEqual(
            entity_copied,
            MockHtnEntity({"bar"}, True, 1, (1, 2), [1, 2], {"1": 1}),
        )
        self.assertEqual(
            entity,
            MockHtnEntity({"foo"}, True, 1, (1, 2), [1, 2], {"1": 1}),
        )

    def test_copy_and_extend_with(self) -> None:
        """
        Check that copy_and_extend_with() returns a copy
        where the specified arguments are extended if there are sequences,
        else they are overridden without updating the original entity.
        """
        # arrange
        entity = MockHtnEntity({"foo"}, True, 1, (1, 2), [1, 2], {"1": 1})
        # act
        entity_extended = entity.copy_and_extend_with(
            set_attr={"bar"},
            tuple_attr=(3, 4),
            list_attr=[3, 4],
            dict_attr={"2": 2},
            int_attr=2,
        )
        # assert
        self.assertIsInstance(entity_extended, MockHtnEntity)
        self.assertEqual(
            entity_extended,
            MockHtnEntity(
                {"foo", "bar"},
                True,
                2,
                (1, 2, 3, 4),
                [1, 2, 3, 4],
                {"1": 1, "2": 2},
            ),
        )
        self.assertEqual(
            entity,
            MockHtnEntity({"foo"}, True, 1, (1, 2), [1, 2], {"1": 1}),
        )
