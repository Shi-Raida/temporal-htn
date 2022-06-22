from temporal_htn.htn import (
    HTN_TIMEPOINT,
    HtnConstraint,
    HtnTemporalConstraint,
    HtnTemporalInterval,
)
from temporal_htn.lcp_converter import (
    ChroniclesProblem,
    ChronicleSymbolType,
    get_constraint,
    get_interval,
    get_timepoint,
    get_typed_object,
)

from .abstract_test import AbstractTest


class TestChronicles(AbstractTest):
    """
    Regroups all tests related to temporal HTN conversion to chronicles.
    """

    def setUp(self) -> None:
        super().setUp()
        self.ch_problem = ChroniclesProblem()

    def test_type(self, assertion: bool = True) -> None:
        """
        Checks that a `HtnType` is correctly converted.
        """
        self.ch_problem.add_type(self.t_location)
        self.ch_problem.add_type(self.t_locatable)
        self.ch_problem.add_type(self.t_package)
        self.ch_problem.add_type(self.t_robot)
        if assertion:
            self.assertSetEqual(
                self.ch_problem.types,
                {self.t_location, self.t_locatable, self.t_package, self.t_robot},
            )

    def test_variable(self, assertion: bool = True) -> None:
        """
        Checks that a `HtnVariable` is correctly converted.
        """
        self.ch_problem.add_variable(self.v_location)
        self.ch_problem.add_variable(self.v_from)
        self.ch_problem.add_variable(self.v_to)
        self.ch_problem.add_variable(self.v_locatable)
        self.ch_problem.add_variable(self.v_package)
        self.ch_problem.add_variable(self.v_robot)
        self.ch_problem.add_variable(self.v_time_start)
        self.ch_problem.add_variable(self.v_time_end)
        if assertion:
            self.assertSetEqual(
                self.ch_problem.types,
                {
                    self.t_location,
                    self.t_locatable,
                    self.t_package,
                    self.t_robot,
                    HTN_TIMEPOINT,
                },
            )
            self.assertSetEqual(
                self.ch_problem.variables,
                {
                    self.v_location,
                    self.v_from,
                    self.v_to,
                    self.v_locatable,
                    self.v_package,
                    self.v_robot,
                    self.v_time_start,
                    self.v_time_end,
                },
            )
            self.assertEqual(get_typed_object(self.v_location), "?loc - location")
            self.assertEqual(get_typed_object(self.v_locatable), "?obj - locatable")
            self.assertEqual(get_typed_object(self.v_package), "?p - package")
            self.assertEqual(get_typed_object(self.v_robot), "?r - robot")
            self.assertEqual(
                get_typed_object(self.v_time_start), "?ts + 0 - __timepoint__"
            )

    def test_constant(self, assertion: bool = True) -> None:
        """
        Checks that a `HtnConstant` is correctly converted.
        """
        self.ch_problem.add_constant(self.o_loc0)
        self.ch_problem.add_constant(self.o_loc1)
        self.ch_problem.add_constant(self.o_loc2)
        self.ch_problem.add_constant(self.o_package)
        self.ch_problem.add_constant(self.o_robot)
        if assertion:
            self.assertSetEqual(
                self.ch_problem.types,
                {self.t_location, self.t_locatable, self.t_package, self.t_robot},
            )
            self.assertSetEqual(
                self.ch_problem.constants,
                {self.o_loc0, self.o_loc1, self.o_loc2, self.o_package, self.o_robot},
            )
            self.assertEqual(get_typed_object(self.o_loc0), "L0 - location")
            self.assertEqual(get_typed_object(self.o_package), "P - package")
            self.assertEqual(get_typed_object(self.o_robot), "R - robot")

    def test_timepoint(self, assertion: bool = True) -> None:
        """
        Checks that a `HtnTimepoint` is correctly converted.
        """
        self.ch_problem.add_variable(self.v_time_start)
        self.ch_problem.add_variable(self.v_time_end)
        if assertion:
            self.assertSetEqual(self.ch_problem.types, {HTN_TIMEPOINT})
            self.assertSetEqual(
                self.ch_problem.variables, {self.v_time_start, self.v_time_end}
            )
            self.assertEqual(
                get_typed_object(self.v_time_start), "?ts + 0 - __timepoint__"
            )
            self.assertEqual(
                get_typed_object(self.v_time_start + 5), "?ts + 50 - __timepoint__"
            )
            self.assertEqual(
                get_timepoint(self.v_time_start), "?ts + 0 - __timepoint__"
            )
            self.assertEqual(
                get_timepoint(self.v_time_start + 5), "?ts + 50 - __timepoint__"
            )

    def test_temporal_interval(self, assertion: bool = True) -> None:
        """
        Checks that a `HtnTemporalInterval` is correctly converted.
        """
        if assertion:
            self.assertEqual(
                get_interval(
                    HtnTemporalInterval(self.v_time_start, self.v_time_end + 5)
                ),
                ["?ts + 0 - __timepoint__", "?te + 50 - __timepoint__"],
            )

    def test_get_constraint(self) -> None:
        """
        Checks that a `HtnConstraint` is correctly converted.
        """
        constraint = HtnConstraint(self.v_from, self.v_to, "!=")
        self.assertEqual(
            get_constraint(constraint), ["?from - location", "!=", "?to - location"]
        )

    def test_get_temporal_constraint(self) -> None:
        """
        Checks that a `HtnTemporalConstraint` is correctly converted.
        """
        constraint = HtnTemporalConstraint(self.v_time_start, self.v_time_end, "!=")
        self.assertEqual(
            get_constraint(constraint),
            ["?ts + 0 - __timepoint__", "!=", "?te + 0 - __timepoint__"],
        )

        labelled_constraint = HtnTemporalConstraint(
            self.v_time_start, self.v_time_end, "!=", self.l_1, self.l_5
        )
        self.assertEqual(
            get_constraint(labelled_constraint),
            ["?tsl1 + 0 - __timepoint__", "!=", "?tel5 + 0 - __timepoint__"],
        )

    def test_symbol(self, assertion: bool = True) -> None:
        """
        Checks that a `HtnSymbol` is correctly converted.
        """
        self.ch_problem.add_symbol(self.s_sv_at, ChronicleSymbolType.PREDICATE)
        self.ch_problem.add_symbol(self.s_sv_empty, ChronicleSymbolType.PREDICATE)
        self.ch_problem.add_symbol(self.s_sv_holding, ChronicleSymbolType.PREDICATE)
        self.ch_problem.add_symbol(self.s_sv_path, ChronicleSymbolType.PREDICATE)
        self.ch_problem.add_symbol(self.s_p_move, ChronicleSymbolType.ACTION)
        self.ch_problem.add_symbol(self.s_p_drop, ChronicleSymbolType.ACTION)
        self.ch_problem.add_symbol(self.s_p_pick, ChronicleSymbolType.ACTION)
        self.ch_problem.add_symbol(self.s_c_go, ChronicleSymbolType.TASK)
        self.ch_problem.add_symbol(self.s_c_transfer, ChronicleSymbolType.TASK)
        self.ch_problem.add_symbol(self.s_m_go, ChronicleSymbolType.METHOD)
        self.ch_problem.add_symbol(self.s_m_already_there, ChronicleSymbolType.METHOD)
        self.ch_problem.add_symbol(self.s_m_transfer, ChronicleSymbolType.METHOD)
        self.ch_problem.add_symbol(
            self.s_m_already_transferred, ChronicleSymbolType.METHOD
        )
        if assertion:
            self.assertSetEqual(
                self.ch_problem.symbols,
                {
                    self.s_m_go,
                    self.s_m_already_there,
                    self.s_m_transfer,
                    self.s_m_already_transferred,
                    self.s_c_go,
                    self.s_c_transfer,
                    self.s_p_drop,
                    self.s_p_pick,
                    self.s_p_move,
                    self.s_sv_at,
                    self.s_sv_holding,
                    self.s_sv_empty,
                    self.s_sv_path,
                },
            )

    def test_symbol_table_creation(self, assertion: bool = True) -> None:
        """
        Checks that the symbol table is correctly created.
        """
        self.test_constant(False)
        self.test_variable(False)
        self.test_timepoint(False)
        self.test_symbol(False)
        self.ch_problem.create_symbol_table()
        if assertion:
            self.assertTrue(self.ch_problem.symbol_table_created)

    def test_state_variable(self, assertion: bool = True) -> None:
        """
        Checks that a `HtnStateVariable` is correctly converted.
        """
        self.test_symbol_table_creation(False)
        self.ch_problem.add_state_variable(self.sv_at_package_location)
        self.ch_problem.add_state_variable(self.sv_at_package_from)
        self.ch_problem.add_state_variable(self.sv_at_package_loc1)
        self.ch_problem.add_state_variable(self.sv_at_robot_location)
        self.ch_problem.add_state_variable(self.sv_at_robot_from)
        self.ch_problem.add_state_variable(self.sv_at_robot_to)
        self.ch_problem.add_state_variable(self.sv_at_robot_loc0)
        self.ch_problem.add_state_variable(self.sv_empty_robot)
        self.ch_problem.add_state_variable(self.sv_empty_robot_o)
        self.ch_problem.add_state_variable(self.sv_holding_robot_package)
        self.ch_problem.add_state_variable(self.sv_path_from_to)
        self.ch_problem.add_state_variable(self.sv_path_loc0_loc1)
        self.ch_problem.add_state_variable(self.sv_path_loc0_loc2)
        self.ch_problem.add_state_variable(self.sv_path_loc1_loc0)
        self.ch_problem.add_state_variable(self.sv_path_loc1_loc2)
        self.ch_problem.add_state_variable(self.sv_path_loc2_loc0)
        self.ch_problem.add_state_variable(self.sv_path_loc2_loc1)
        if assertion:
            self.assertSetEqual(
                self.ch_problem.state_variables,
                {
                    self.sv_at_package_location,
                    self.sv_at_package_from,
                    self.sv_at_package_loc1,
                    self.sv_at_robot_location,
                    self.sv_at_robot_from,
                    self.sv_at_robot_to,
                    self.sv_at_robot_loc0,
                    self.sv_holding_robot_package,
                    self.sv_empty_robot,
                    self.sv_empty_robot_o,
                    self.sv_path_from_to,
                    self.sv_path_loc0_loc1,
                    self.sv_path_loc0_loc2,
                    self.sv_path_loc1_loc0,
                    self.sv_path_loc1_loc2,
                    self.sv_path_loc2_loc0,
                    self.sv_path_loc2_loc1,
                },
            )

    def test_context_creation(self, assertion: bool = True) -> None:
        """
        Checks that the context and the initial chronicle are correctly created.
        """
        self.test_state_variable(False)
        self.ch_problem.create_context()
        if assertion:
            self.assertTrue(self.ch_problem.context_created)

    def test_primitive_task(self, assertion: bool = True) -> None:
        """
        Checks that a `HtnPrimitiveTask` is correctly converted.
        """
        self.test_context_creation(False)
        self.ch_problem.add_action(self.p_move_durative)
        self.ch_problem.add_action(self.p_drop)
        self.ch_problem.add_action(self.p_pick)
        self.ch_problem.add_action(self.p_pick_from)
        if assertion:
            self.assertSetEqual(
                self.ch_problem.actions,
                {self.p_move_durative, self.p_drop, self.p_pick, self.p_pick_from},
            )

    def test_method(self, assertion: bool = True) -> None:
        """
        Checks that a `HtnMethod` is correctly converted.
        """
        self.test_primitive_task(False)
        self.ch_problem.add_method(self.m_transfer)
        self.ch_problem.add_method(self.m_already_transferred)
        self.ch_problem.add_method(self.m_go_durative)
        self.ch_problem.add_method(self.m_already_there)
        if assertion:
            self.assertSetEqual(
                self.ch_problem.methods,
                {
                    self.m_transfer,
                    self.m_already_transferred,
                    self.m_go_durative,
                    self.m_already_there,
                },
            )

    def test_goal(self) -> None:
        """
        Checks that a goal is correctly converted.
        Only checks that no errors occurred.
        """
        self.test_method(False)
        self.ch_problem.set_goal(self.goal)

    def test_initial_effect(self, assertion: bool = True) -> None:
        """
        Checks that an initial effect is correctly converted.
        """
        self.test_goal()
        self.ch_problem.add_initial_effect(self.i_robot_loc0)
        self.ch_problem.add_initial_effect(self.i_package_loc1)
        self.ch_problem.add_initial_effect(self.i_robot_empty)
        self.ch_problem.add_initial_effect(self.i_path_loc0_loc1)
        self.ch_problem.add_initial_effect(self.i_path_loc0_loc2)
        self.ch_problem.add_initial_effect(self.i_path_loc1_loc0)
        self.ch_problem.add_initial_effect(self.i_path_loc1_loc2)
        self.ch_problem.add_initial_effect(self.i_path_loc2_loc0)
        self.ch_problem.add_initial_effect(self.i_path_loc2_loc1)
        if assertion:
            self.assertSetEqual(
                self.ch_problem.initial_effects,
                {
                    self.i_robot_loc0,
                    self.i_package_loc1,
                    self.i_robot_empty,
                    self.i_path_loc0_loc1,
                    self.i_path_loc0_loc2,
                    self.i_path_loc1_loc0,
                    self.i_path_loc1_loc2,
                    self.i_path_loc2_loc0,
                    self.i_path_loc2_loc1,
                },
            )

    def test_complete_conversion(self) -> None:
        """
        Checks that a `HtnProblem` is correctly converted.
        """
        self.ch_problem = ChroniclesProblem.from_htn(self.problem_durative)
