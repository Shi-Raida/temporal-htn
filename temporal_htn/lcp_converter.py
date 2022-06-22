from __future__ import annotations

import os
from enum import Enum, auto

# pylint: disable=no-name-in-module
from .chronicles import ChronicleProblem as LcpChronicleProblem
from .htn import (
    HTN_BOOLEAN,
    HTN_INTEGER,
    HTN_TIME_SCALE,
    HtnCompoundTask,
    HtnCondition,
    HtnConstant,
    HtnConstraint,
    HtnConstraintFactory,
    HtnEffect,
    HtnLabel,
    HtnMethod,
    HtnParametricSymbol,
    HtnPrimitiveTask,
    HtnProblem,
    HtnStateVariable,
    HtnSymbol,
    HtnTask,
    HtnTaskNetwork,
    HtnTemporalConstraint,
    HtnTemporalInterval,
    HtnTimepoint,
    HtnType,
    HtnTypedObject,
    HtnVariable,
)


def get_constraint(htn_constraint: HtnConstraint) -> list[str]:
    """
    Returns
    -------
    list[str]
        A list usable by chronicles, representing the HTN constraint.
    """
    if isinstance(htn_constraint, HtnTemporalConstraint):
        return get_temporal_constraint(htn_constraint)
    return [
        get_typed_object(htn_constraint.left),
        htn_constraint.relation,
        get_typed_object(htn_constraint.right),
    ]


def get_temporal_constraint(htn_constraint: HtnTemporalConstraint):
    """
    Returns
    -------
    list[str]
        A list usable by chronicles, representing the HTN temporal constraint.
    """
    return [
        get_timepoint(htn_constraint.left, htn_constraint.left_label),
        htn_constraint.relation,
        get_timepoint(htn_constraint.right, htn_constraint.right_label),
    ]


def get_interval(
    htn_interval: HtnTemporalInterval, htn_label: HtnLabel = None
) -> list[str]:
    """
    Parameters
    ----------
    htn_interval : HtnTemporalInterval
        The temporal interval to convert.
    htn_label : HtnLabel, optional
        A label to apply to the timepoint value.
        Typically used for a task network.

    Returns
    -------
    list[str]
        A list usable by chronicles, representing the HTN temporal interval.
    """
    return [
        get_timepoint(htn_interval.start, htn_label),
        get_timepoint(htn_interval.end, htn_label),
    ]


def get_timepoint(htn_timepoint: HtnTimepoint, htn_label: HtnLabel = None) -> str:
    """
    Parameters
    ----------
    htn_timepoint : HtnTimepoint
        The timepoint to convert.
    htn_label : HtnLabel, optional
        A label to apply to the timepoint value.
        Typically used for temporal constraints in a task network.

    Returns
    -------
    str
        A string usable by chronicles, representing the HTN timepoint.
    """
    value = f"{htn_timepoint.value}"
    if htn_label:
        value += f"{htn_label}"
    return (
        f"{value} + {int(htn_timepoint.delay * HTN_TIME_SCALE)} - {htn_timepoint.tpe}"
    )


def get_typed_object(htn_obj: HtnTypedObject) -> str:
    """
    Returns
    -------
    str
        A string usable by chronicles, representing the HTN typed object.
    """
    if isinstance(htn_obj, HtnTimepoint):
        return get_timepoint(htn_obj)
    return f"{htn_obj.value} - {htn_obj.tpe}"


class ChroniclesProblem:
    """
    Converter from temporal HTN formalism to Chronicles.
    """

    def __init__(self, name: str = "problem") -> None:
        self.name = name
        self.plan_file = f"output/{self.name}.plan"
        self.problem = LcpChronicleProblem()

        self.context_created: bool = False
        self.symbol_table_created: bool = False

        self.actions: set[HtnPrimitiveTask] = set()
        self.constants: set[HtnConstant] = set()
        self.initial_effects: set[HtnEffect] = set()
        self.methods: set[HtnMethod] = set()
        self.state_variables: set[HtnStateVariable] = set()
        self.symbols: set[HtnSymbol] = set()
        self.tasks: set[HtnCompoundTask] = set()
        self.types: set[HtnType] = set()
        self.variables: set[HtnVariable] = set()

    def add_action(self, htn_action: HtnPrimitiveTask) -> None:
        """
        Adds a new action to the problem.
        Does nothing if the action is in `self.actions`.

        Gets the signature, the constraints, the conditions and the effects.
        Then, adds the action.

        /!\\\
        The symbol of the action has to be already registered.
        The symbol table has to be created.
        The context has to be created.
        """
        if htn_action in self.actions:
            return
        self.check_symbol(htn_action.symbol)
        self.check_context()
        self.actions.add(htn_action)

        signature = self.get_signature_temporal(htn_action)
        constraints = [
            get_constraint(constraint) for constraint in htn_action.constraints
        ]
        conditions = [
            self.get_condition(condition) for condition in htn_action.conditions
        ]
        effects = [self.get_effect(effect) for effect in htn_action.effects]

        # Add a min duration if the action has at least one effect.
        # If the action has a duration of zero then the effect will be instantaneous,
        # which is not desirable.
        if len(effects) > 0:
            constraint = HtnConstraintFactory.min_duration_eps(htn_action)
            constraints.append(get_constraint(constraint))

        self.problem.add_action(signature, constraints, conditions, effects)

    def add_constant(self, htn_constant: HtnConstant) -> None:
        """
        Adds a new constant to the problem.
        Does nothing if the constant is in `self.constants`.

        Adds the type and the symbol of the constant.
        """
        if htn_constant in self.constants:
            return
        self.constants.add(htn_constant)

        self.add_type(htn_constant.tpe)
        self.add_symbol(
            HtnSymbol(str(htn_constant.value)),
            ChronicleSymbolType.CONSTANT,
            htn_constant.tpe,
        )

    def add_method(self, htn_method: HtnMethod) -> None:
        """
        Adds a new method to the problem.
        Does nothing if the method is in `self.methods`.

        Gets the signature, the constraints, the conditions, the task,
        the subtasks, and the temporal constraints between subtasks.
        Then, adds the method.

        /!\\\
        The symbol of the method has to be already registered.
        The symbol table has to be created.
        The context has to be created.
        """
        if htn_method in self.methods:
            return
        self.check_symbol(htn_method.symbol)
        self.check_context()
        self.methods.add(htn_method)

        signature = self.get_signature_temporal(htn_method)
        constraints = [
            get_constraint(constraint) for constraint in htn_method.constraints
        ]
        conditions = [
            self.get_condition(condition) for condition in htn_method.conditions
        ]
        task = self.get_signature(htn_method.task)
        subtasks = [
            self.get_signature_temporal(lmp.task, lmp.label)
            for lmp in htn_method.task_network.label_mapping
        ]
        subtasks_constraints = [
            get_constraint(constraint)
            for constraint in htn_method.task_network.constraints
        ]

        self.problem.add_method(
            signature, constraints, conditions, task, subtasks, subtasks_constraints
        )

    def add_initial_effect(self, htn_effect: HtnEffect) -> None:
        """
        Adds a new effect describing a part of the initial state of the problem.
        Does nothing if the effect is in `self.initial_effects`.

        Gets the signature, then adds the predicate.

        /!\\\
        The symbol of the effect has to be already registered.
        The symbol table has to be created.
        The context has to be created.
        """
        if htn_effect in self.initial_effects:
            return
        self.check_symbol(htn_effect.sv.symbol)
        self.check_context()
        self.initial_effects.add(htn_effect)

        self.problem.add_initial_effect(self.get_effect(htn_effect))

    def add_state_variable(self, htn_sv: HtnStateVariable) -> None:
        """
        Adds a new state variable to the problem.
        Does nothing if the state variable is in `self.state_variable`.

        Adds the signature of the state variable.

        /!\\\
        The symbol of the state variable has to be already registered.
        The symbol table has to be created.

        Raises
        ------
        NotImplementedError
            If the type of the state variable is not handled by the solver.
        """
        if htn_sv in self.state_variables:
            return
        self.check_symbol(htn_sv.symbol)
        self.state_variables.add(htn_sv)

        signature = self.get_signature(htn_sv)

        if htn_sv.tpe == HTN_BOOLEAN:
            self.problem.add_predicate(signature)
        elif htn_sv.tpe == HTN_INTEGER:
            self.problem.add_function(signature)
        else:
            raise NotImplementedError(
                f"The solver can only handle booleans and integers state variables, got {htn_sv.tpe}"  # noqa: E501
            )

    def add_symbol(
        self,
        symbol: HtnSymbol,
        symbol_type: ChronicleSymbolType,
        htn_type: HtnType = None,
    ) -> None:
        """
        Adds a new symbol to the problem.
        Does nothing if the symbol is in `self.symbols`.

        Parameters
        ----------
        symbol : HtnSymbol
            The symbol to add.
        symbol_type : ChronicleSymbolType
            The type of the symbol (i.e. Action, Constant, Method, Predicate, Task).
        htn_type : HtnType
            Type of the symbol if it is a constant.

        Raises
        ------
        ValueError
            If try to add a `CONSTANT` with an undefined type.
        RuntimeError
            If `symbol_type` is not handled.
        """
        if symbol in self.symbols:
            return
        self.symbols.add(symbol)

        if symbol_type == ChronicleSymbolType.ACTION:
            self.problem.add_action_symbol(symbol.name)
        elif symbol_type == ChronicleSymbolType.CONSTANT:
            if htn_type is None:
                raise ValueError(
                    "`htn_type` cannot be null for adding a constant symbol."
                )
            self.problem.add_constant_symbol(symbol.name, htn_type.name)
        elif symbol_type == ChronicleSymbolType.METHOD:
            self.problem.add_method_symbol(symbol.name)
        elif symbol_type == ChronicleSymbolType.PREDICATE:
            self.problem.add_predicate_symbol(symbol.name)
        elif symbol_type == ChronicleSymbolType.FUNCTION:
            self.problem.add_function_symbol(symbol.name)
        elif symbol_type == ChronicleSymbolType.TASK:
            self.problem.add_task_symbol(symbol.name)
        else:
            raise RuntimeError("The given symbol type is not handled.")

    def add_type(self, htn_type: HtnType) -> None:
        """
        Adds a new type to the problem.
        Does nothing if the type is in `self.types`.

        It calls itself recursively to create the whole
        hierarchy until the root is reached.
        """
        if htn_type in self.types:
            return
        self.types.add(htn_type)

        parent = htn_type.parent.name if htn_type.parent else None
        self.problem.add_type(htn_type.name, parent)
        if htn_type.parent is not None:
            self.add_type(htn_type.parent)

    def add_variable(self, htn_variable: HtnVariable) -> None:
        """
        Adds a new variable to the problem.
        Does nothing if the variable is in `self.variables`.

        Adds the type of the variable.
        """
        if htn_variable in self.variables:
            return
        self.variables.add(htn_variable)

        self.add_type(htn_variable.tpe)

    def check_context(self) -> None:
        """
        Raises
        ------
        UncreatedContextError
            If the context has not been created.
        """
        if not self.context_created:
            raise UncreatedContextError()

    def check_symbol(self, symbol: HtnSymbol) -> None:
        """
        Raises
        ------
        UnregisteredSymbolError
            If `symbol` has not been added.
        """
        self.check_symbol_table()
        if symbol not in self.symbols:
            raise UnregisteredSymbolError(symbol)

    def check_symbol_table(self) -> None:
        """
        Raises
        ------
        UncreatedSymbolTableError
            If the symbol table has not been created.
        """
        if not self.symbol_table_created:
            raise UncreatedSymbolTableError()

    def create_context(self) -> None:
        """
        Creates the context of the problem.

        Should be called after the creation of all state variables.
        """
        self.problem.create_context()
        self.context_created = True

    def create_symbol_table(self) -> None:
        """
        Creates the symbol table of the problem.

        Should be called:
        - after the creation of all types and symbols
        - before the creation of state variables
        """
        self.problem.create_symbol_table()
        self.symbol_table_created = True

    def get_condition(self, htn_condition: HtnCondition) -> list[str]:
        """
        Returns
        -------
        list[str]
            A list usable by chronicles, representing the HTN condition.
        """
        return (
            self.get_signature(htn_condition.sv)
            + [str(htn_condition.value.value)]
            + get_interval(htn_condition.interval)
        )

    def get_effect(self, htn_effect: HtnEffect) -> list[str]:
        """
        Returns
        -------
        list[str]
            A list usable by chronicles, representing the HTN effect.
        """
        return (
            self.get_signature(htn_effect.sv)
            + [str(htn_effect.value.value)]
            + get_interval(htn_effect.interval)
        )

    def get_signature(
        self,
        htn_param_sym: HtnParametricSymbol | HtnMethod,
    ) -> list[str]:
        """
        Returns
        -------
        list[str]
            Returns the signature of the parametric symbol.
            It is its symbol followed by the parameter values.
        """
        self.check_symbol(htn_param_sym.symbol)
        self.check_symbol_table()
        return [htn_param_sym.symbol.name] + [
            get_typed_object(param) for param in htn_param_sym.all_params
        ]

    def get_signature_temporal(
        self, htn_obj: HtnTask | HtnMethod, htn_label: HtnLabel = None
    ) -> list[str]:
        """
        Returns
        -------
        list[str]
            Returns the temporal signature of the task or the method.
            It is its symbol followed by the parameter values
            followed by the temporal interval.
        """
        return self.get_signature(htn_obj) + get_interval(htn_obj.interval, htn_label)

    @classmethod
    def from_htn(  # noqa: C901  # pylint: disable=too-many-branches
        cls, htn_problem: HtnProblem
    ) -> ChroniclesProblem:
        """
        Converts an `HtnProblem` to Chronicles.

        Raises
        ------
        NotImplementedError
            If the type of the state variable is not handled by the solver.
        """
        # Init
        problem = ChroniclesProblem(name=htn_problem.name)
        # Map state variable symbols to the state variable type.
        sv_map = {sv.symbol: sv.tpe for sv in htn_problem.state_variables}
        # Types & Symbols
        for constant in htn_problem.D.L.Csts:
            problem.add_constant(constant)
        for variable in htn_problem.D.L.Vars:
            problem.add_variable(variable)
        # Note: Use intersection because a state variable can be defined
        # in the language without being used by the problem.
        # Therefore, it is not registered.
        for sv_sym in htn_problem.D.L.StVars.intersection(
            sv.symbol for sv in htn_problem.state_variables
        ):
            if sv_map[sv_sym] == HTN_BOOLEAN:
                problem.add_symbol(sv_sym, ChronicleSymbolType.PREDICATE)
            elif sv_map[sv_sym] == HTN_INTEGER:
                problem.add_symbol(sv_sym, ChronicleSymbolType.FUNCTION)
            else:
                raise NotImplementedError(
                    f"The solver can only handle booleans and integers state variables, got {sv_map[sv_sym]}"  # noqa: E501
                )
        for action_sym in htn_problem.D.L.Prims:
            problem.add_symbol(action_sym, ChronicleSymbolType.ACTION)
        for task_sym in htn_problem.D.L.Comps:
            problem.add_symbol(task_sym, ChronicleSymbolType.TASK)
        for method in htn_problem.D.M:
            problem.add_symbol(method.symbol, ChronicleSymbolType.METHOD)
        # Symbol table
        problem.create_symbol_table()
        # State Variables
        for sv in htn_problem.state_variables:
            problem.add_state_variable(sv)
        # Context
        problem.create_context()
        # Actions
        for action in htn_problem.D.Tp:
            problem.add_action(action)
        # Methods
        for method in htn_problem.D.M:
            problem.add_method(method)
        # Goal
        problem.set_goal(htn_problem.tn_I)
        # Initial state
        for init_effect in htn_problem.s_I:
            problem.add_initial_effect(init_effect)
        # End of the conversion
        return problem

    def set_goal(self, htn_task_network: HtnTaskNetwork | None) -> None:
        """
        Sets the goal of the problem.

        Gets the subtasks of the goal and their constraints.
        Then, add the goal.

        /!\\\
        The symbol table and the context has to be created.
        """
        if htn_task_network is None:
            return

        self.check_symbol_table()
        self.check_context()

        tasks = [
            self.get_signature_temporal(lmp.task, lmp.label)
            for lmp in htn_task_network.label_mapping
        ]
        constraints = [
            get_constraint(constraint) for constraint in htn_task_network.constraints
        ]

        self.problem.add_goal(tasks, constraints)

    def solve(self, output_file: str = None, verbose: bool = False) -> None:
        """
        Solves the problem.

        Parameters
        ----------
        output_file : str, optional
            Path to the output file where the plan will be saved.
        verbose : bool, optional
            Whether or not information must be printed in the console, by default False.

        Raises
        ------
        NoSolutionFoundError
            If there is no solution to the given problem.
        """
        self.plan_file = output_file or self.plan_file
        os.makedirs(os.path.dirname(self.plan_file), exist_ok=True)
        solved = self.problem.solve(self.plan_file, verbose)
        if not solved:
            raise NoSolutionFoundError(self)


class ChronicleSymbolType(Enum):
    """
    Groups all type of possible symbols.
    """

    ACTION = auto()
    CONSTANT = auto()
    METHOD = auto()
    PREDICATE = auto()
    FUNCTION = auto()
    TASK = auto()


class UncreatedContextError(RuntimeError):
    """
    The context is not created.
    """


class UncreatedSymbolTableError(RuntimeError):
    """
    The symbol table is not created.
    """


class UnregisteredSymbolError(RuntimeError):
    """
    The symbol is not registered.
    """


class NoSolutionFoundError(RuntimeError):
    """There is no solution to the given problem."""

    def __init__(self, problem: ChroniclesProblem, *args: object) -> None:
        self.problem = problem
        super().__init__(*args)
