from temporal_htn import (
    HTN_FALSE,
    HTN_TIMEPOINT,
    HTN_TRUE,
    HtnCondition,
    HtnConstantTimepoint,
    HtnConstraint,
    HtnEffect,
    HtnTemporalInterval,
    HtnTemporalIntervalFactory,
)

from .abstract_test import AbstractTest


class TestHTNCreation(AbstractTest):
    """
    Regroups all tests related to temporal HTN creation.
    """

    def test_type_str(self) -> None:
        """
        Checks the str format of a `HtnType`.
        """
        self.assertEqual(str(self.t_location), "location")

    def test_typed_object_str(self) -> None:
        """
        Checks the str format of a `HtnTypedObject`.
        """
        self.assertEqual(str(self.v_location), "?loc - location")
        self.assertEqual(str(self.o_loc0), "L0 - location")

    def test_timepoints(self) -> None:
        """
        Checks the correct behaviour of timepoints.
        """
        self.assertEqual(self.v_time_start.value, "?ts")
        self.assertEqual(self.v_time_start.tpe, HTN_TIMEPOINT)
        self.assertEqual(self.v_time_start.delay, 0)
        delayed = self.v_time_start + 5
        self.assertEqual(delayed.value, "?ts")
        self.assertEqual(delayed.tpe, HTN_TIMEPOINT)
        self.assertEqual(delayed.delay, 5)
        with self.assertRaises(TypeError):
            self.v_time_start + [2, 3]  # pylint: disable=pointless-statement
        with self.assertRaises(ValueError):
            self.v_time_start + "plop"  # pylint: disable=pointless-statement

    def test_timepoint_str(self) -> None:
        """
        Checks the str format of a `HtnTimepoint`.
        """
        self.assertEqual(str(self.v_time_start), "?ts")
        self.assertEqual(str(self.v_time_start + 2), "?ts + 2.0")
        cst = HtnConstantTimepoint(5)
        self.assertEqual(str(cst), "5")
        self.assertEqual(str(cst + 2), "7.0")
        self.assertEqual(str(HtnTemporalIntervalFactory.default()), "")
        self.assertEqual(str(HtnTemporalIntervalFactory.at_start()), "at-start ")
        self.assertEqual(str(HtnTemporalIntervalFactory.at_end()), "at-end ")
        self.assertEqual(str(HtnTemporalIntervalFactory.over_all()), "over-all ")

    def test_symbol_str(self) -> None:
        """
        Checks the str format of a `HtnSymbol`.
        """
        self.assertEqual(str(self.s_sv_at), "at")
        self.assertEqual(str(self.s_p_move), "move")
        self.assertEqual(str(self.s_c_go), "go")

    def test_label_str(self) -> None:
        """
        Checks the str format of a `HtnLabel`.
        """
        self.assertEqual(str(self.l_1), "l1")

    def test_state_variable_str(self) -> None:
        """
        Checks the str format of a `HtnStateVariable`.
        """
        self.assertEqual(
            str(self.sv_at_package_location), "at(?p - package, ?loc - location)"
        )

    def test_condition_str(self) -> None:
        """
        Checks the str format of a `HtnCondition`.
        """
        cond = HtnCondition(self.sv_at_package_location)
        self.assertEqual(str(cond), f"{self.sv_at_package_location} = True")
        temp_cond = HtnCondition(
            self.sv_at_package_location,
            HTN_FALSE,
            HtnTemporalInterval(HtnConstantTimepoint(0), HtnConstantTimepoint(5)),
        )
        self.assertEqual(
            str(temp_cond), f"[0, 5] {self.sv_at_package_location} = False"
        )
        over_cond = HtnCondition(
            self.sv_at_package_location,
            HTN_FALSE,
            HtnTemporalIntervalFactory.over_all(),
        )
        self.assertEqual(
            str(over_cond), f"over-all {self.sv_at_package_location} = False"
        )

    def test_effect_str(self) -> None:
        """
        Checks the str format of a `HtnEffect`.
        """
        eff = HtnEffect(self.sv_at_package_location, HTN_TRUE)
        self.assertEqual(str(eff), f"{self.sv_at_package_location} <-- True")
        temp_eff = HtnEffect(
            self.sv_at_package_location,
            HTN_FALSE,
            HtnTemporalInterval(HtnConstantTimepoint(0), HtnConstantTimepoint(5)),
        )
        self.assertEqual(
            str(temp_eff), f"[0, 5] {self.sv_at_package_location} <-- False"
        )

    def test_constraint_str(self) -> None:
        """
        Checks the str format of a `HtnConstraint`.
        """
        constraint = HtnConstraint(
            self.v_location,
            self.o_loc0,
            "!=",
        )
        self.assertEqual(str(constraint), "?loc != L0")

    def test_task_str(self) -> None:
        """
        Checks the str format of a `HtnTask`.
        """
        self.assertEqual(
            str(self.p_drop),
            "drop(?r - robot, ?p - package, ?loc - location)",
        )

        self.assertEqual(
            str(self.p_move_durative),
            "[?ts, ?te] move(?r - robot, ?from - location, ?to - location)",
        )

    def test_problem(self) -> None:
        """
        Creates a complex HTN problem and returns it.
        If everything is OK, no errors should be raised.
        """
        self.assertSetEqual(
            self.problem_durative.state_variables,
            {
                self.sv_at_package_from,
                self.sv_at_package_location,
                self.sv_at_package_loc1,
                self.sv_at_robot_from,
                self.sv_at_robot_to,
                self.sv_at_robot_location,
                self.sv_at_robot_loc0,
                self.sv_empty_robot,
                self.sv_empty_robot_o,
                self.sv_holding_robot_package,
                self.sv_path_from_to,
                self.sv_path_loc0_loc1,
                self.sv_path_loc0_loc2,
                self.sv_path_loc1_loc0,
                self.sv_path_loc1_loc2,
                self.sv_path_loc2_loc0,
                self.sv_path_loc2_loc1,
            },
        )
