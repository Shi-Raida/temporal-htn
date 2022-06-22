"""Tests the resolution of some HTN problems."""

import logging
import os
import shutil

from temporal_htn import (
    HTN_EPSILON,
    HTN_FALSE,
    HTN_TRUE,
    HTN_ZERO,
    ChroniclesProblem,
    HtnCompoundTask,
    HtnCompoundTaskSymbol,
    HtnCondition,
    HtnConstant,
    HtnDomain,
    HtnEffect,
    HtnEffectFactory,
    HtnLabelMappingPair,
    HtnLanguage,
    HtnMethod,
    HtnMethodSymbol,
    HtnPrimitiveTask,
    HtnPrimitiveTaskSymbol,
    HtnProblem,
    HtnStateVariable,
    HtnStateVariableSymbol,
    HtnTaskNetwork,
    HtnTemporalConstraint,
    HtnTemporalInterval,
    HtnTemporalIntervalFactory,
    HtnType,
    HtnVariable,
    HtnVariableTimepoint,
    NoSolutionFoundError,
)

from .abstract_test import AbstractTest

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())


class TestSolve(AbstractTest):
    """
    Regroups all tests related to solving.
    """

    # pylint: disable=too-many-public-methods

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        if os.path.exists("output"):
            shutil.rmtree("output")

    def test(self):
        """Run all tests based on the getters."""
        for problem_getter in [
            v for v in dir(self) if callable(getattr(self, v)) and "get_" in v
        ]:
            logger.info("Testing %s", problem_getter)
            self.run_problem(getattr(self, problem_getter)())

    #################################################
    # Generic functions                             #
    #################################################

    def check_result_plan(self, problem_name: str) -> None:
        """
        Checks that the plan calculated by the solver is correct.
        """

        def extract_plan(file):
            lines = []
            plan = False
            for line in file:
                if line == "**** Plan ****\n":
                    plan = True
                    continue
                if not plan:
                    continue
                lines.append(line.strip())
            lines = [line for line in lines if line != ""]
            return lines

        with open(f"output/{problem_name}.plan", encoding="utf-8") as file:
            output_lines = extract_plan(file)
        with open(
            f"tests/expected_plans/{problem_name}.plan", encoding="utf-8"
        ) as file:
            expected_lines = extract_plan(file)
        self.assertEqual(output_lines, expected_lines)

    def run_problem(self, problem: HtnProblem) -> None:
        """
        Generic test function for a given problem.
        """
        ch_problem = ChroniclesProblem.from_htn(problem)
        if problem.name[-10:] == "impossible":
            with self.assertRaises(NoSolutionFoundError):
                ch_problem.solve()
        else:
            ch_problem.solve()
            self.check_result_plan(ch_problem.name)

    #################################################
    # Plan getters                                  #
    #################################################

    def get_move_problem(self) -> HtnProblem:
        """
        Creates and returns a moving problem.
        """
        return HtnProblem(
            HtnDomain(
                HtnLanguage(
                    {self.v_robot, self.v_from, self.v_to, self.v_location},
                    {self.o_loc0, self.o_loc1, self.o_loc2, self.o_robot},
                    {self.s_sv_at, self.s_sv_path},
                    {self.s_p_move},
                    {self.s_c_go},
                    {self.l_0},
                ),
                {self.p_move},
                {self.c_go, self.c_go_to},
                {self.m_go, self.m_already_there},
            ),
            {
                self.i_robot_loc0,
                self.i_path_loc0_loc1,
                self.i_path_loc0_loc2,
                self.i_path_loc1_loc0,
                self.i_path_loc1_loc2,
                self.i_path_loc2_loc0,
                self.i_path_loc2_loc1,
            },
            HtnTaskNetwork(
                (
                    HtnLabelMappingPair(
                        self.l_0,
                        HtnCompoundTask(self.s_c_go, (self.o_robot, self.o_loc1)),
                    ),
                )
            ),
            name="move",
        )

    def get_no_move_problem(self) -> HtnProblem:
        """
        Creates and returns a no moving problem.
        """
        move_problem = self.get_move_problem()
        move_problem.tn_I = HtnTaskNetwork(
            (
                HtnLabelMappingPair(
                    self.l_0, HtnCompoundTask(self.s_c_go, (self.o_robot, self.o_loc0))
                ),
            )
        )
        move_problem.name = "no-move"
        return move_problem

    def get_move_temporal_problem(self) -> HtnProblem:
        """
        Creates and returns a moving problem with temporal constraints.
        """
        problem = self.get_move_problem()
        problem.D.Tp = {self.p_move_durative}
        problem.name = "move-temporal"
        return problem

    def get_move_problem_same_action(self) -> HtnProblem:
        """
        Creates and return a moving problem A --> B --> A --> B.
        """
        problem = self.get_move_problem()
        move_to_loc0 = HtnCompoundTask(self.s_c_go, (self.o_robot, self.o_loc0))
        move_to_loc1 = HtnCompoundTask(self.s_c_go, (self.o_robot, self.o_loc1))
        problem.tn_I = HtnTaskNetwork(
            (
                HtnLabelMappingPair(self.l_0, move_to_loc1),
                HtnLabelMappingPair(self.l_1, move_to_loc0),
                HtnLabelMappingPair(self.l_2, move_to_loc1),
            ),
            (
                HtnTemporalConstraint(
                    move_to_loc1.end, move_to_loc0.start, "<=", self.l_0, self.l_1
                ),
                HtnTemporalConstraint(
                    move_to_loc0.end, move_to_loc1.start, "<=", self.l_1, self.l_2
                ),
            ),
        )
        problem.name = "move-same"
        return problem

    def get_move_impossible_problem(self) -> HtnProblem:
        """
        Creates and returns an impossible moving problem.
        """
        problem = self.get_move_problem()
        problem.s_I.remove(self.i_path_loc0_loc1)
        problem.name = "move-impossible"
        return problem

    def get_move_after_problem(self) -> HtnProblem:
        """
        Creates and return a moving problem which has to be done after 15 units of time.
        """
        problem = self.get_move_temporal_problem()
        move_to_loc1 = HtnCompoundTask(self.s_c_go, (self.o_robot, self.o_loc1))
        problem.tn_I = HtnTaskNetwork(
            (HtnLabelMappingPair(self.l_0, move_to_loc1),),
            (
                HtnTemporalConstraint(
                    move_to_loc1.start, HTN_ZERO + 15, ">=", self.l_0, None
                ),
            ),
        )
        problem.name = "move-after"
        return problem

    def get_move_before_problem(self) -> HtnProblem:
        """
        Creates and return a moving problem which has to be done before time 15.
        """
        problem = self.get_move_temporal_problem()
        move_to_loc1 = HtnCompoundTask(self.s_c_go, (self.o_robot, self.o_loc1))
        problem.tn_I = HtnTaskNetwork(
            (HtnLabelMappingPair(self.l_0, move_to_loc1),),
            (
                HtnTemporalConstraint(
                    move_to_loc1.end, HTN_ZERO + 15, "<=", self.l_0, None
                ),
            ),
        )
        problem.name = "move-before"
        return problem

    def get_transfer_problem(self) -> HtnProblem:
        """
        Creates and returns a delivering problem.
        """
        return self.problem

    def get_no_transfer_problem(self) -> HtnProblem:
        """
        Creates and returns a no delivering problem.
        """
        transfer_problem: HtnProblem = self.problem.copy_with()  # type: ignore
        transfer_problem.tn_I = HtnTaskNetwork(
            (
                HtnLabelMappingPair(
                    self.l_0,
                    HtnCompoundTask(self.s_c_transfer, (self.o_package, self.o_loc1)),
                ),
            )
        )
        transfer_problem.name = "no-transfer"
        return transfer_problem

    def get_transfer_temporal_problem(self) -> HtnProblem:
        """
        Creates and returns a delivering problem with temporal constraints.
        """
        return self.problem_durative

    def get_overlap_problem(self) -> HtnProblem:
        """Create and return an overlapping problem with temporal constraints."""
        move = HtnCompoundTask(self.s_c_go, (self.o_robot, self.o_loc1))
        speak = HtnPrimitiveTask(self.s_p_speak, (self.o_robot,))

        problem = self.get_move_temporal_problem()
        problem.D.L.Prims.add(self.s_p_speak)
        problem.D.Tp.add(self.p_speak)
        problem.tn_I = HtnTaskNetwork(
            (
                HtnLabelMappingPair(self.l_0, move),
                HtnLabelMappingPair(self.l_1, speak),
            ),
            (
                HtnTemporalConstraint(move.start, speak.start, "<", self.l_0, self.l_1),
                HtnTemporalConstraint(speak.end, move.end, "<", self.l_1, self.l_0),
            ),
        )
        problem.name = "overlap"
        return problem

    def get_exterior_temporal_constraints(self):
        """
        Create a problem with a temporal constraint where one
        part is out of the TaskNetwork.
        """
        # pylint: disable=too-many-locals

        # Variables & Constants
        t_robot = HtnType("robot")
        v_robot = HtnVariable("?r", t_robot)
        o_robot = HtnConstant("R", t_robot)

        start1, end1 = (HtnVariableTimepoint(v) for v in ["?ts1", "?te1"])
        start2, end2 = (HtnVariableTimepoint(v) for v in ["?ts2", "?te2"])
        start3, end3 = (HtnVariableTimepoint(v) for v in ["?ts3", "?te3"])

        # State variables
        s_sv_flag_end_action2 = HtnStateVariableSymbol("flag-end-action2")
        sv_flag_end_action2 = HtnStateVariable(s_sv_flag_end_action2, ())

        # Primitive tasks
        s_p_1 = HtnPrimitiveTaskSymbol("action1")
        s_p_2 = HtnPrimitiveTaskSymbol("action2")
        s_p_3 = HtnPrimitiveTaskSymbol("action3")

        p_1 = HtnPrimitiveTask(
            s_p_1,
            (v_robot,),
            interval=HtnTemporalInterval(start1, end1),
            constraints=(HtnTemporalConstraint(end1, start1 + 1, "=="),),
            conditions=(
                HtnCondition(
                    sv_flag_end_action2, interval=HtnTemporalInterval(start1 - 5, end1)
                ),
            ),
        )
        p_2 = HtnPrimitiveTask(
            s_p_2,
            (v_robot,),
            interval=HtnTemporalInterval(start2, end2),
            constraints=(HtnTemporalConstraint(end2, start2 + 2, "=="),),
            effects=(
                HtnEffect(
                    sv_flag_end_action2, HTN_TRUE, HtnTemporalIntervalFactory.at_end()
                ),
            ),
        )
        p_3 = HtnPrimitiveTask(
            s_p_3,
            (v_robot,),
            interval=HtnTemporalInterval(start3, end3),
            constraints=(HtnTemporalConstraint(end3, start3 + 3, "=="),),
        )

        # Compound tasks
        s_c_1 = HtnCompoundTaskSymbol("task1")
        s_c_2 = HtnCompoundTaskSymbol("task2")
        c_1 = HtnCompoundTask(s_c_1, (v_robot,))
        c_2 = HtnCompoundTask(s_c_2, (v_robot,))

        # Methods
        s_m_1 = HtnMethodSymbol("method1")
        s_m_2 = HtnMethodSymbol("method2")
        m_1 = HtnMethod(
            c_1,
            HtnTaskNetwork(
                (
                    HtnLabelMappingPair(self.l_1, p_1),
                    HtnLabelMappingPair(self.l_2, c_2),
                ),
            ),
            symbol=s_m_1,
        )
        m_2 = HtnMethod(
            c_2,
            HtnTaskNetwork(
                (
                    HtnLabelMappingPair(self.l_3, p_2),
                    HtnLabelMappingPair(self.l_4, p_3),
                ),
                (HtnTemporalConstraint(p_2.end, p_3.start, "<=", self.l_3, self.l_4),),
            ),
            symbol=s_m_2,
        )

        # Problem
        return HtnProblem(
            HtnDomain(
                HtnLanguage(
                    {v_robot},
                    {o_robot},
                    {s_sv_flag_end_action2},
                    {s_p_1, s_p_2, s_p_3},
                    {s_c_1, s_c_2},
                    {self.l_0, self.l_1, self.l_2, self.l_3, self.l_4},
                ),
                {p_1, p_2, p_3},
                {c_1, c_2},
                {m_1, m_2},
            ),
            set(),
            HtnTaskNetwork(
                (HtnLabelMappingPair(self.l_0, HtnCompoundTask(s_c_1, (o_robot,))),)
            ),
            "exterior",
        )

    def get_start_synchronisation_problem(self) -> HtnProblem:
        """Create a problem where two actions have to start at the same moment."""
        # pylint: disable=too-many-locals

        # Variables & Constants
        t_robot = HtnType("robot")
        v_robot = HtnVariable("?r", t_robot)
        o_robot = HtnConstant("R", t_robot)

        start1, end1 = (HtnVariableTimepoint(v) for v in ["?ts1", "?te1"])
        start2, end2 = (HtnVariableTimepoint(v) for v in ["?ts2", "?te2"])

        # State variables
        s_sv_flag_start_action1 = HtnStateVariableSymbol("flag-start-action1")
        sv_flag_start_action1 = HtnStateVariable(s_sv_flag_start_action1, ())

        # Primitive tasks
        s_p_1 = HtnPrimitiveTaskSymbol("action1")
        s_p_2 = HtnPrimitiveTaskSymbol("action2")

        p_1 = HtnPrimitiveTask(
            symbol=s_p_1,
            params=(v_robot,),
            interval=HtnTemporalInterval(start1, end1),
            constraints=(HtnTemporalConstraint(end1, start1 + 1, "=="),),
            effects=(
                *HtnEffectFactory.dirac_at_start(
                    sv=sv_flag_start_action1,
                    value=HTN_TRUE,
                ),
            ),
        )
        p_2 = HtnPrimitiveTask(
            symbol=s_p_2,
            params=(v_robot,),
            interval=HtnTemporalInterval(start2, end2),
            constraints=(HtnTemporalConstraint(end2, start2 + 2, "=="),),
            conditions=(
                HtnCondition(
                    sv=sv_flag_start_action1,
                    value=HTN_TRUE,
                    interval=HtnTemporalIntervalFactory.at_start(),
                ),
            ),
        )

        # Compound tasks
        s_c_1 = HtnCompoundTaskSymbol("task1")
        s_c_2 = HtnCompoundTaskSymbol("task2")
        s_c_3 = HtnCompoundTaskSymbol("task3")
        c_1 = HtnCompoundTask(s_c_1, (v_robot,))
        c_2 = HtnCompoundTask(s_c_2, (v_robot,))
        c_3 = HtnCompoundTask(s_c_3, (v_robot,))

        # Methods
        s_m_1 = HtnMethodSymbol("method1")
        s_m_2 = HtnMethodSymbol("method2")
        s_m_3 = HtnMethodSymbol("method3")
        m_1 = HtnMethod(
            c_1,
            HtnTaskNetwork(
                (
                    HtnLabelMappingPair(self.l_1, c_2),
                    HtnLabelMappingPair(self.l_2, c_3),
                ),
            ),
            symbol=s_m_1,
        )
        m_2 = HtnMethod(
            c_2,
            HtnTaskNetwork(
                label_mapping=(HtnLabelMappingPair(self.l_3, p_1),),
                constraints=(
                    HtnTemporalConstraint(p_1.start, HTN_ZERO + 5, "==", self.l_3),
                ),
            ),
            symbol=s_m_2,
        )
        m_3 = HtnMethod(
            c_3,
            HtnTaskNetwork(
                (HtnLabelMappingPair(self.l_4, p_2),),
            ),
            symbol=s_m_3,
        )

        # Problem
        return HtnProblem(
            HtnDomain(
                HtnLanguage(
                    {v_robot},
                    {o_robot},
                    {s_sv_flag_start_action1},
                    {s_p_1, s_p_2},
                    {s_c_1, s_c_2, s_c_3},
                    {self.l_0, self.l_1, self.l_2, self.l_3, self.l_4},
                ),
                {p_1, p_2},
                {c_1, c_2, c_3},
                {m_1, m_2, m_3},
            ),
            set(),
            HtnTaskNetwork(
                (HtnLabelMappingPair(self.l_0, HtnCompoundTask(s_c_1, (o_robot,))),)
            ),
            "start-sync",
        )

    def get_impossible_start_synchronisation_problem(self) -> HtnProblem:
        """Create an impossible problem of synchronisation."""
        problem = self.get_start_synchronisation_problem()
        problem.name += "-impossible"
        for method in problem.D.M:
            if method.symbol.name == "method3":
                problem.D.M.remove(method)
                problem.D.M.add(
                    method.copy_with(  # type: ignore
                        task_network=method.task_network.copy_with(
                            constraints=(
                                HtnTemporalConstraint(
                                    method.task_network.label_mapping[0].task.start,
                                    HTN_ZERO + 10,
                                    "==",
                                    self.l_4,
                                ),
                            )
                        )
                    )
                )
        return problem

    def get_end_synchronisation_problem(self) -> HtnProblem:
        """Create a problem where two actions have to end at the same moment."""
        # pylint: disable=too-many-locals

        # Variables & Constants
        t_robot = HtnType("robot")
        v_robot = HtnVariable("?r", t_robot)
        o_robot = HtnConstant("R", t_robot)

        start1, end1 = (HtnVariableTimepoint(v) for v in ["?ts1", "?te1"])
        start2, end2 = (HtnVariableTimepoint(v) for v in ["?ts2", "?te2"])

        # State variables
        s_sv_flag_end_action1 = HtnStateVariableSymbol("flag-end-action1")
        sv_flag_end_action1 = HtnStateVariable(s_sv_flag_end_action1, ())

        # Primitive tasks
        s_p_1 = HtnPrimitiveTaskSymbol("action1")
        s_p_2 = HtnPrimitiveTaskSymbol("action2")

        p_1 = HtnPrimitiveTask(
            symbol=s_p_1,
            params=(v_robot,),
            interval=HtnTemporalInterval(start1, end1),
            constraints=(HtnTemporalConstraint(end1, start1 + 1, "=="),),
            effects=(
                *HtnEffectFactory.dirac_at_end(
                    sv=sv_flag_end_action1,
                    value=HTN_TRUE,
                ),
            ),
        )
        p_2 = HtnPrimitiveTask(
            symbol=s_p_2,
            params=(v_robot,),
            interval=HtnTemporalInterval(start2, end2),
            constraints=(HtnTemporalConstraint(end2, start2 + 2, "=="),),
            conditions=(
                HtnCondition(
                    sv=sv_flag_end_action1,
                    value=HTN_TRUE,
                    interval=HtnTemporalIntervalFactory.at_end(),
                ),
            ),
        )

        # Compound tasks
        s_c_1 = HtnCompoundTaskSymbol("task1")
        s_c_2 = HtnCompoundTaskSymbol("task2")
        s_c_3 = HtnCompoundTaskSymbol("task3")
        c_1 = HtnCompoundTask(s_c_1, (v_robot,))
        c_2 = HtnCompoundTask(s_c_2, (v_robot,))
        c_3 = HtnCompoundTask(s_c_3, (v_robot,))

        # Methods
        s_m_1 = HtnMethodSymbol("method1")
        s_m_2 = HtnMethodSymbol("method2")
        s_m_3 = HtnMethodSymbol("method3")
        m_1 = HtnMethod(
            c_1,
            HtnTaskNetwork(
                (
                    HtnLabelMappingPair(self.l_1, c_2),
                    HtnLabelMappingPair(self.l_2, c_3),
                ),
            ),
            symbol=s_m_1,
        )
        m_2 = HtnMethod(
            c_2,
            HtnTaskNetwork(
                label_mapping=(HtnLabelMappingPair(self.l_3, p_1),),
                constraints=(
                    HtnTemporalConstraint(p_1.start, HTN_ZERO + 5, "==", self.l_3),
                ),
            ),
            symbol=s_m_2,
        )
        m_3 = HtnMethod(
            c_3,
            HtnTaskNetwork(
                (HtnLabelMappingPair(self.l_4, p_2),),
            ),
            symbol=s_m_3,
        )

        # Problem
        return HtnProblem(
            HtnDomain(
                HtnLanguage(
                    {v_robot},
                    {o_robot},
                    {s_sv_flag_end_action1},
                    {s_p_1, s_p_2},
                    {s_c_1, s_c_2, s_c_3},
                    {self.l_0, self.l_1, self.l_2, self.l_3, self.l_4},
                ),
                {p_1, p_2},
                {c_1, c_2, c_3},
                {m_1, m_2, m_3},
            ),
            set(),
            HtnTaskNetwork(
                (HtnLabelMappingPair(self.l_0, HtnCompoundTask(s_c_1, (o_robot,))),)
            ),
            "end-sync",
        )

    def get_impossible_end_synchronisation_problem(self) -> HtnProblem:
        """Create an impossible problem of synchronisation."""
        problem = self.get_end_synchronisation_problem()
        problem.name += "-impossible"
        for method in problem.D.M:
            if method.symbol.name == "method3":
                problem.D.M.remove(method)
                problem.D.M.add(
                    method.copy_with(  # type: ignore
                        task_network=method.task_network.copy_with(
                            constraints=(
                                HtnTemporalConstraint(
                                    method.task_network.label_mapping[0].task.start,
                                    HTN_ZERO + 10,
                                    "==",
                                    self.l_4,
                                ),
                            )
                        )
                    )
                )
        return problem

    def get_constraint_abstract_task_problem(self) -> HtnProblem:
        """Create a problem where the abstract task has temporal constraints."""
        # pylint: disable=too-many-locals

        # Variables & Constants
        start_c1, end_c1 = (HtnVariableTimepoint(v) for v in ["?ts1", "?te1"])
        start_p1, end_p1 = (HtnVariableTimepoint(v) for v in ["?ts2", "?te2"])
        start_p2, end_p2 = (HtnVariableTimepoint(v) for v in ["?ts3", "?te3"])

        # Primitive tasks
        s_p_1 = HtnPrimitiveTaskSymbol("action1")
        s_p_2 = HtnPrimitiveTaskSymbol("action2")

        p_1 = HtnPrimitiveTask(
            symbol=s_p_1,
            params=(),
            interval=HtnTemporalInterval(start_p1, end_p1),
            constraints=(HtnTemporalConstraint(end_p1, start_p1 + 1, "=="),),
        )
        p_2 = HtnPrimitiveTask(
            symbol=s_p_2,
            params=(),
            interval=HtnTemporalInterval(start_p2, end_p2),
            constraints=(HtnTemporalConstraint(end_p2, start_p2 + 2, "=="),),
        )

        # Compound tasks
        s_c_1 = HtnCompoundTaskSymbol("task1")
        c_1 = HtnCompoundTask(
            symbol=s_c_1,
            params=(),
            interval=HtnTemporalInterval(start_c1, end_c1),
        )

        # Methods
        s_m_1 = HtnMethodSymbol("method1")
        m_1 = HtnMethod(
            task=c_1,
            task_network=HtnTaskNetwork(
                label_mapping=(
                    HtnLabelMappingPair(self.l_1, p_1),
                    HtnLabelMappingPair(self.l_2, p_2),
                ),
                constraints=(
                    HtnTemporalConstraint(p_2.start, p_1.end, ">=", self.l_2, self.l_1),
                ),
            ),
            symbol=s_m_1,
        )

        # Problem
        return HtnProblem(
            HtnDomain(
                HtnLanguage(
                    set(),
                    set(),
                    set(),
                    {s_p_1, s_p_2},
                    {s_c_1},
                    {self.l_0, self.l_1, self.l_2},
                ),
                {p_1, p_2},
                {c_1},
                {m_1},
            ),
            set(),
            HtnTaskNetwork(
                label_mapping=(HtnLabelMappingPair(self.l_0, c_1),),
                constraints=(
                    HtnTemporalConstraint(c_1.start, HTN_ZERO + 5, "==", self.l_0),
                ),
            ),
            "abstract-constraint",
        )

    def get_outside_effect_problem(self) -> HtnProblem:
        """Create a problem with an effect outside the action scope."""
        # Predicate
        predicate_s = HtnStateVariableSymbol("predicate")
        predicate = HtnStateVariable(symbol=predicate_s, params=())

        # Intervals
        action_interval = HtnTemporalIntervalFactory.over_all()
        effect_interval = HtnTemporalInterval(
            start=action_interval.start + 5 - HTN_EPSILON,
            end=action_interval.start + 5 - HTN_EPSILON,
        )

        # Action
        effect_action_s = HtnPrimitiveTaskSymbol("action with effect")
        effect_action = HtnPrimitiveTask(
            symbol=effect_action_s,
            params=(),
            interval=action_interval,
            constraints=(
                HtnTemporalConstraint(
                    action_interval.end, action_interval.start + 2, "=="
                ),
            ),
            effects=(
                HtnEffect(sv=predicate, value=HTN_TRUE, interval=effect_interval),
            ),
        )

        condition_action_s = HtnPrimitiveTaskSymbol("action with condition")
        condition_action = HtnPrimitiveTask(
            symbol=condition_action_s,
            params=(),
            conditions=(HtnCondition(sv=predicate),),
        )

        # Task
        task_s = HtnCompoundTaskSymbol("task")
        task = HtnCompoundTask(symbol=task_s, params=())

        # Method
        method_s = HtnMethodSymbol("method")
        method = HtnMethod(
            task=task,
            task_network=HtnTaskNetwork(
                label_mapping=(
                    HtnLabelMappingPair(self.l_1, effect_action),
                    HtnLabelMappingPair(self.l_2, condition_action),
                ),
            ),
            symbol=method_s,
        )

        # Problem
        return HtnProblem(
            D=HtnDomain(
                L=HtnLanguage(
                    StVars={predicate_s},
                    Prims={effect_action_s, condition_action_s},
                    Comps={task_s},
                    Labs={self.l_0, self.l_1, self.l_2},
                ),
                Tp={effect_action, condition_action},
                Tc={task},
                M={method},
            ),
            s_I={HtnEffect(sv=predicate, value=HTN_FALSE)},
            tn_I=HtnTaskNetwork(
                label_mapping=(HtnLabelMappingPair(self.l_0, task),),
            ),
            name="outside-effect",
        )

    def get_instantaneous_action_without_effect_problem(self) -> HtnProblem:
        """Create a problem with an an instantaneous action without effect."""
        # Predicate
        predicate_s = HtnStateVariableSymbol("predicate")
        predicate = HtnStateVariable(symbol=predicate_s, params=())

        # Intervals
        action_interval = HtnTemporalIntervalFactory.over_all()

        # Action
        action_s = HtnPrimitiveTaskSymbol("action")
        action = HtnPrimitiveTask(
            symbol=action_s,
            params=(),
            interval=action_interval,
        )

        # Problem
        return HtnProblem(
            D=HtnDomain(
                L=HtnLanguage(
                    StVars={predicate_s},
                    Prims={action_s},
                    Labs={self.l_0},
                ),
                Tp={action},
            ),
            s_I={HtnEffect(sv=predicate, value=HTN_FALSE)},
            tn_I=HtnTaskNetwork(
                label_mapping=(HtnLabelMappingPair(self.l_0, action),),
            ),
            name="instant-action-without-effect",
        )

    def get_instantaneous_action_with_effect_problem(self) -> HtnProblem:
        """Create a problem with an an instantaneous action without effect."""
        # Predicate
        predicate_s = HtnStateVariableSymbol("predicate")
        predicate = HtnStateVariable(symbol=predicate_s, params=())

        # Intervals
        action_interval = HtnTemporalIntervalFactory.over_all()

        # Action
        action_s = HtnPrimitiveTaskSymbol("action")
        action = HtnPrimitiveTask(
            symbol=action_s,
            params=(),
            interval=action_interval,
            effects=(HtnEffect(sv=predicate, value=HTN_TRUE),),
        )

        # Problem
        return HtnProblem(
            D=HtnDomain(
                L=HtnLanguage(
                    StVars={predicate_s},
                    Prims={action_s},
                    Labs={self.l_0},
                ),
                Tp={action},
            ),
            s_I={HtnEffect(sv=predicate, value=HTN_FALSE)},
            tn_I=HtnTaskNetwork(
                label_mapping=(HtnLabelMappingPair(self.l_0, action),),
            ),
            name="instant-action-with-effect",
        )


if __name__ == "__main__":
    from unittest import main

    main()
