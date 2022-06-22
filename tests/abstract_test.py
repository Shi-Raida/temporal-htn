from unittest import TestCase

from temporal_htn import (
    HTN_FALSE,
    HTN_TRUE,
    HtnCompoundTask,
    HtnCompoundTaskSymbol,
    HtnCondition,
    HtnConstant,
    HtnConstraint,
    HtnDomain,
    HtnEffect,
    HtnLabel,
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
    HtnType,
    HtnVariable,
    HtnVariableTimepoint,
)


class AbstractTest(TestCase):
    """
    Abstract test class that creates the common attributes.
    """

    # pylint: disable=too-many-instance-attributes,too-many-statements

    def setUp(self) -> None:
        """
        Creates a delivering HTN problem with a durative action.
        """
        super().setUp()

        # Types
        self.t_location = HtnType("location")
        self.t_locatable = HtnType("locatable")
        self.t_package = HtnType("package", self.t_locatable)
        self.t_robot = HtnType("robot", self.t_locatable)

        # Variables
        self.v_from = HtnVariable("?from", self.t_location)
        self.v_to = HtnVariable("?to", self.t_location)
        self.v_location = HtnVariable("?loc", self.t_location)
        self.v_locatable = HtnVariable("?obj", self.t_locatable)
        self.v_robot = HtnVariable("?r", self.t_robot)
        self.v_package = HtnVariable("?p", self.t_package)
        self.v_time_start = HtnVariableTimepoint("?ts")
        self.v_time_end = HtnVariableTimepoint("?te")

        # Objects
        self.o_loc0 = HtnConstant("L0", self.t_location)
        self.o_loc1 = HtnConstant("L1", self.t_location)
        self.o_loc2 = HtnConstant("L2", self.t_location)
        self.o_robot = HtnConstant("R", self.t_robot)
        self.o_package = HtnConstant("P", self.t_package)

        # Symbols
        self.s_sv_at = HtnStateVariableSymbol("at")
        self.s_sv_holding = HtnStateVariableSymbol("holding")
        self.s_sv_empty = HtnStateVariableSymbol("empty")
        self.s_sv_path = HtnStateVariableSymbol("path")

        self.s_p_move = HtnPrimitiveTaskSymbol("move")
        self.s_p_pick = HtnPrimitiveTaskSymbol("pick-up")
        self.s_p_drop = HtnPrimitiveTaskSymbol("drop")
        self.s_p_speak = HtnPrimitiveTaskSymbol("speak")

        self.s_c_go = HtnCompoundTaskSymbol("go")
        self.s_c_transfer = HtnCompoundTaskSymbol("transfer")

        self.s_m_go = HtnMethodSymbol("m-go")
        self.s_m_already_there = HtnMethodSymbol("m-already-there")
        self.s_m_transfer = HtnMethodSymbol("m-tranfer")
        self.s_m_already_transferred = HtnMethodSymbol("m-already-transferred")

        self.l_0 = HtnLabel("l0")
        self.l_1 = HtnLabel("l1")
        self.l_2 = HtnLabel("l2")
        self.l_3 = HtnLabel("l3")
        self.l_4 = HtnLabel("l4")
        self.l_5 = HtnLabel("l5")

        # State Variables
        self.sv_at_robot_location = HtnStateVariable(
            self.s_sv_at, (self.v_robot, self.v_location)
        )
        self.sv_at_package_location = HtnStateVariable(
            self.s_sv_at, (self.v_package, self.v_location)
        )
        self.sv_at_robot_from = HtnStateVariable(
            self.s_sv_at, (self.v_robot, self.v_from)
        )
        self.sv_at_package_from = HtnStateVariable(
            self.s_sv_at, (self.v_package, self.v_from)
        )
        self.sv_at_robot_to = HtnStateVariable(self.s_sv_at, (self.v_robot, self.v_to))
        self.sv_holding_robot_package = HtnStateVariable(
            self.s_sv_holding, (self.v_robot, self.v_package)
        )
        self.sv_empty_robot = HtnStateVariable(self.s_sv_empty, (self.v_robot,))
        self.sv_path_from_to = HtnStateVariable(
            self.s_sv_path, (self.v_from, self.v_to)
        )

        # Actions
        self.p_move = HtnPrimitiveTask(
            self.s_p_move,
            (self.v_robot, self.v_from, self.v_to),
            constraints=(HtnConstraint(self.v_from, self.v_to, "!="),),
            conditions=(
                HtnCondition(
                    self.sv_at_robot_from,
                ),
                HtnCondition(self.sv_path_from_to),
            ),
            effects=(
                HtnEffect(
                    self.sv_at_robot_from,
                    HTN_FALSE,
                ),
                HtnEffect(
                    self.sv_at_robot_to,
                    HTN_TRUE,
                ),
            ),
        )
        self.p_move_durative = HtnPrimitiveTask(
            self.s_p_move,
            (self.v_robot, self.v_from, self.v_to),
            interval=HtnTemporalInterval(self.v_time_start, self.v_time_end),
            constraints=(
                HtnConstraint(self.v_from, self.v_to, "!="),
                HtnConstraint(self.v_time_end, self.v_time_start + 10, "=="),
            ),
            conditions=(
                HtnCondition(
                    self.sv_at_robot_from,
                    HTN_TRUE,
                    HtnTemporalInterval(self.v_time_start, self.v_time_start),
                ),
                HtnCondition(
                    self.sv_path_from_to,
                    HTN_TRUE,
                    HtnTemporalInterval(self.v_time_start, self.v_time_end),
                ),
            ),
            effects=(
                HtnEffect(
                    self.sv_at_robot_from,
                    HTN_FALSE,
                    HtnTemporalInterval(self.v_time_start, self.v_time_start),
                ),
                HtnEffect(
                    self.sv_at_robot_to,
                    HTN_TRUE,
                    HtnTemporalInterval(self.v_time_end, self.v_time_end),
                ),
            ),
        )
        self.p_pick = HtnPrimitiveTask(
            self.s_p_pick,
            (self.v_robot, self.v_package, self.v_location),
            conditions=(
                HtnCondition(self.sv_at_robot_location),
                HtnCondition(self.sv_at_package_location),
                HtnCondition(self.sv_empty_robot),
            ),
            effects=(
                HtnEffect(self.sv_at_package_location, HTN_FALSE),
                HtnEffect(self.sv_empty_robot, HTN_FALSE),
                HtnEffect(self.sv_holding_robot_package, HTN_TRUE),
            ),
        )
        self.p_pick_from = HtnPrimitiveTask(
            self.s_p_pick,
            (self.v_robot, self.v_package, self.v_from),
            conditions=(
                HtnCondition(self.sv_at_robot_from),
                HtnCondition(self.sv_at_package_from),
                HtnCondition(self.sv_empty_robot),
            ),
            effects=(
                HtnEffect(self.sv_at_package_from, HTN_FALSE),
                HtnEffect(self.sv_empty_robot, HTN_FALSE),
                HtnEffect(self.sv_holding_robot_package, HTN_TRUE),
            ),
        )
        self.p_drop = HtnPrimitiveTask(
            self.s_p_drop,
            (self.v_robot, self.v_package, self.v_location),
            conditions=(
                HtnCondition(self.sv_at_robot_location),
                HtnCondition(self.sv_holding_robot_package),
            ),
            effects=(
                HtnEffect(self.sv_at_package_location, HTN_TRUE),
                HtnEffect(self.sv_empty_robot, HTN_TRUE),
                HtnEffect(self.sv_holding_robot_package, HTN_FALSE),
            ),
        )
        self.p_speak = HtnPrimitiveTask(self.s_p_speak, (self.v_robot,))

        # Tasks
        self.c_go = HtnCompoundTask(self.s_c_go, (self.v_robot, self.v_location))
        self.c_go_to = HtnCompoundTask(self.s_c_go, (self.v_robot, self.v_to))
        self.c_go_from = HtnCompoundTask(self.s_c_go, (self.v_robot, self.v_from))
        self.c_transfer = HtnCompoundTask(
            self.s_c_transfer, (self.v_package, self.v_location)
        )

        # Methods
        self.m_go = HtnMethod(
            self.c_go_to,
            HtnTaskNetwork((HtnLabelMappingPair(self.l_1, self.p_move),)),
            symbol=self.s_m_go,
        )
        self.m_go_durative = HtnMethod(
            self.c_go_to,
            HtnTaskNetwork((HtnLabelMappingPair(self.l_1, self.p_move_durative),)),
            symbol=self.s_m_go,
        )
        self.m_already_there = HtnMethod(
            self.c_go,
            HtnTaskNetwork(),
            conditions=(HtnCondition(self.sv_at_robot_location),),
            symbol=self.s_m_already_there,
        )
        self.m_transfer = HtnMethod(
            self.c_transfer,
            HtnTaskNetwork(
                (
                    HtnLabelMappingPair(self.l_2, self.c_go_from),
                    HtnLabelMappingPair(self.l_3, self.p_pick_from),
                    HtnLabelMappingPair(self.l_4, self.c_go_to),
                    HtnLabelMappingPair(self.l_5, self.p_drop),
                ),
                (
                    HtnTemporalConstraint(
                        self.c_go_from.end,
                        self.p_pick_from.start,
                        "<=",
                        self.l_2,
                        self.l_3,
                    ),
                    HtnTemporalConstraint(
                        self.p_pick_from.end,
                        self.c_go_to.start,
                        "<=",
                        self.l_3,
                        self.l_4,
                    ),
                    HtnTemporalConstraint(
                        self.c_go_to.end, self.p_drop.start, "<=", self.l_4, self.l_5
                    ),
                ),
            ),
            symbol=self.s_m_transfer,
        )
        self.m_already_transferred = HtnMethod(
            self.c_transfer,
            HtnTaskNetwork(),
            conditions=(HtnCondition(self.sv_at_package_location),),
            symbol=self.s_m_already_transferred,
        )

        # Language
        self.language = HtnLanguage(
            {
                self.v_from,
                self.v_to,
                self.v_location,
                self.v_locatable,
                self.v_robot,
                self.v_package,
                self.v_time_start,
                self.v_time_end,
            },
            {self.o_loc0, self.o_loc1, self.o_loc2, self.o_package, self.o_robot},
            {self.s_sv_at, self.s_sv_holding, self.s_sv_empty, self.s_sv_path},
            {self.s_p_drop, self.s_p_move, self.s_p_pick},
            {self.s_c_go, self.s_c_transfer},
            {self.l_0, self.l_1, self.l_2, self.l_3, self.l_4, self.l_5},
        )

        # Domain
        self.domain = HtnDomain(
            self.language,
            {self.p_drop, self.p_move, self.p_pick, self.p_pick_from},
            {self.c_go, self.c_go_to, self.c_go_from, self.c_transfer},
            {
                self.m_go,
                self.m_already_there,
                self.m_transfer,
                self.m_already_transferred,
            },
        )
        self.domain_durative = HtnDomain(
            self.language,
            {self.p_drop, self.p_move_durative, self.p_pick, self.p_pick_from},
            {self.c_go, self.c_go_to, self.c_go_from, self.c_transfer},
            {
                self.m_go_durative,
                self.m_already_there,
                self.m_transfer,
                self.m_already_transferred,
            },
        )

        # Problem
        self.goal = HtnTaskNetwork(
            (
                HtnLabelMappingPair(
                    self.l_0,
                    HtnCompoundTask(self.s_c_transfer, (self.o_package, self.o_loc2)),
                ),
            ),
        )
        self.sv_at_robot_loc0 = HtnStateVariable(
            self.s_sv_at, (self.o_robot, self.o_loc0)
        )
        self.sv_at_package_loc1 = HtnStateVariable(
            self.s_sv_at, (self.o_package, self.o_loc1)
        )
        self.sv_empty_robot_o = HtnStateVariable(self.s_sv_empty, (self.o_robot,))
        self.sv_path_loc0_loc1 = HtnStateVariable(
            self.s_sv_path, (self.o_loc0, self.o_loc1)
        )
        self.sv_path_loc0_loc2 = HtnStateVariable(
            self.s_sv_path, (self.o_loc0, self.o_loc2)
        )
        self.sv_path_loc1_loc0 = HtnStateVariable(
            self.s_sv_path, (self.o_loc1, self.o_loc0)
        )
        self.sv_path_loc1_loc2 = HtnStateVariable(
            self.s_sv_path, (self.o_loc1, self.o_loc2)
        )
        self.sv_path_loc2_loc0 = HtnStateVariable(
            self.s_sv_path, (self.o_loc2, self.o_loc0)
        )
        self.sv_path_loc2_loc1 = HtnStateVariable(
            self.s_sv_path, (self.o_loc2, self.o_loc1)
        )
        self.i_robot_loc0 = HtnEffect(
            self.sv_at_robot_loc0,
            HTN_TRUE,
        )
        self.i_package_loc1 = HtnEffect(
            self.sv_at_package_loc1,
            HTN_TRUE,
        )
        self.i_robot_empty = HtnEffect(self.sv_empty_robot_o, HTN_TRUE)
        self.i_path_loc0_loc1 = HtnEffect(self.sv_path_loc0_loc1, HTN_TRUE)
        self.i_path_loc0_loc2 = HtnEffect(self.sv_path_loc0_loc2, HTN_TRUE)
        self.i_path_loc1_loc0 = HtnEffect(self.sv_path_loc1_loc0, HTN_TRUE)
        self.i_path_loc1_loc2 = HtnEffect(self.sv_path_loc1_loc2, HTN_TRUE)
        self.i_path_loc2_loc0 = HtnEffect(self.sv_path_loc2_loc0, HTN_TRUE)
        self.i_path_loc2_loc1 = HtnEffect(self.sv_path_loc2_loc1, HTN_TRUE)
        self.problem = HtnProblem(
            self.domain,
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
            self.goal,
            name="transfer",
        )
        self.problem_durative = HtnProblem(
            self.domain_durative,
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
            self.goal,
            name="transfer-temporal",
        )
