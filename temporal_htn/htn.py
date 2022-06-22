"""
This file contains all elements related to the HTN formalism use with python structures.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any, Literal
from uuid import uuid4


class HtnEntity:
    """Base class for the whole HTN formalism."""

    def __get_attributes(self) -> dict[str, Any]:
        return deepcopy(self.__dict__)

    def copy_with(self, **attrs_to_override) -> HtnEntity:
        """Return a copy of the object where the given attributes are overridden."""
        attributes = self.__get_attributes()
        attributes.update(**attrs_to_override)
        return self.__class__(**attributes)

    def copy_and_extend_with(self, **attrs_to_extend) -> HtnEntity:
        """
        Return a copy of the object where the sequential attributes are extended,
        else there are overridden.
        """
        attributes = self.__get_attributes()
        for attr_name, attr_value in attrs_to_extend.items():
            if attr_name in attributes:
                current_attr_value = attributes[attr_name]
                if isinstance(current_attr_value, (set, dict)):
                    current_attr_value.update(attr_value)
                    continue
                if isinstance(current_attr_value, (tuple, list)):
                    attributes[attr_name] = current_attr_value + attr_value
                    continue
            attributes[attr_name] = attr_value
        return self.__class__(**attributes)


@dataclass(frozen=True)
class HtnType(HtnEntity):
    """
    Represents the type of a variable or a constant.
    e.g., `location - object`
    """

    name: str
    parent: HtnType | None = None

    def __str__(self) -> str:
        return self.name

    def __eq__(self, __o: object) -> bool:
        if not isinstance(__o, HtnType):
            return False
        if self.name != __o.name:
            return False
        return self.parent == __o.parent


HTN_TIMEPOINT = HtnType("__timepoint__")
HTN_BOOLEAN = HtnType("__boolean__")
HTN_INTEGER = HtnType("__integer__")


@dataclass(frozen=True)
class HtnTypedObject(HtnEntity):
    """
    Represents an object of the planning problem with a `HtnType`.

    It is an abstract class, it must **not be instantiated**.
    """

    value: str | int | bool
    tpe: HtnType

    @property
    def is_constant(self) -> bool:
        """Whether or not this object is a constant."""
        return isinstance(self, HtnConstant)

    @property
    def is_timepoint(self) -> bool:
        """Whether or not this object is a timepoint."""
        return isinstance(self, HtnTimepoint)

    @property
    def is_variable(self) -> bool:
        """Whether or not this object is a variable."""
        return isinstance(self, HtnVariable)

    def __str__(self) -> str:
        if self in (HTN_TRUE, HTN_FALSE):
            return f"{self.value}"
        return f"{self.value} - {self.tpe}"

    def __eq__(self, __o: object) -> bool:
        if not isinstance(__o, HtnTypedObject):
            return False
        if __o.value != self.value:
            return False
        if __o.tpe != self.tpe:
            return False
        return True


@dataclass(frozen=True)
class HtnVariable(HtnTypedObject):
    """
    Represents a variable of the planning problem.
    e.g. `?l - location`
    """

    value: str

    def __eq__(self, __o: object) -> bool:
        """Necessary to call HtnTypedObject eq method"""
        return super().__eq__(__o)


@dataclass(frozen=True)
class HtnConstant(HtnTypedObject):
    """
    Represents a constant of the planning problem.
    e.g. `L0 - location`
    """

    def __eq__(self, __o: object) -> bool:
        """Necessary to call HtnTypedObject eq method"""
        return super().__eq__(__o)


HTN_TRUE = HtnConstant(True, HTN_BOOLEAN)
HTN_FALSE = HtnConstant(False, HTN_BOOLEAN)

# Allow usage of float delay in HtnTimepoint.
# The delay will be multiplied by HTN_TIME_SCALE and
# casted as an integer before be converted to chronicles.
HTN_TIME_SCALE = 10
HTN_EPSILON = 1 / HTN_TIME_SCALE


@dataclass(frozen=True)
class HtnTimepoint(HtnTypedObject):
    """
    Represents a timepoint of the planning problem.

    It is an abstract class, it must **not be instantiated**.
    """

    value: str | int
    tpe: HtnType = HTN_TIMEPOINT
    delay: float = 0

    def __add__(self, other: Any) -> HtnTimepoint:
        try:
            other = float(other)
            return self.__class__(
                delay=self.delay + other, value=self.value, tpe=self.tpe
            )
        except (TypeError, ValueError) as err:
            raise err.__class__(
                f"Expected a number to be added to a HtnTimepoint but got {other}."
            ) from err

    def __sub__(self, other: Any) -> HtnTimepoint:
        return self + (-other)

    def __str__(self) -> str:
        if self.delay == 0:
            return f"{self.value}"
        if isinstance(self.value, int):
            return f"{self.value + self.delay}"
        return f"{self.value} + {self.delay}"

    def __eq__(self, __o: object) -> bool:
        if not super().__eq__(__o):
            return False
        if not isinstance(__o, HtnTimepoint):
            return False
        return __o.delay == self.delay


@dataclass(frozen=True)
class HtnVariableTimepoint(HtnTimepoint, HtnVariable):
    """
    Represents a variable timepoint.
    e.g. `?t_s`
    """

    value: str


@dataclass(frozen=True)
class HtnConstantTimepoint(HtnTimepoint, HtnConstant):
    """
    Represents a constant timepoint.
    In that case, the value has to be an integer.
    e.g. `5`
    """

    value: int


# When a constant time `cts` is needed, use `HTN_ZERO + cts`.
HTN_ZERO = HtnConstantTimepoint(0)


@dataclass(frozen=True)
class HtnTemporalInterval(HtnEntity):
    """
    Represents a temporal interval.
    e.g. `[2, 5]`
    """

    start: HtnTimepoint
    end: HtnTimepoint

    def __add__(self, other) -> HtnTemporalInterval:
        return HtnTemporalInterval(self.start + other, self.end + other)

    def __sub__(self, other) -> HtnTemporalInterval:
        return HtnTemporalInterval(self.start - other, self.end - other)

    def __str__(self) -> str:
        default = f"[{self.start}, {self.end}] "
        if isinstance(self.start.value, int) or isinstance(self.end.value, int):
            return default
        if self.start.value[:5] == "__d__" and self.end.value[:5] == "__d__":
            return ""
        if self.start.value[:5] == "__s__" and self.end.value[:5] == "__s__":
            return "at-start "
        if self.start.value[:5] == "__e__" and self.end.value[:5] == "__e__":
            return "at-end "
        if self.start.value[:5] == "__s__" and self.end.value[:5] == "__e__":
            return "over-all "
        return default

    def __eq__(self, __o: object) -> bool:
        if not isinstance(__o, HtnTemporalInterval):
            return False
        if __o.start != self.start:
            return False
        return __o.end == self.end


class HtnTemporalIntervalFactory:
    """
    Factory of common temporal intervals.
    Used in order to have distinct timepoints with unique identifiers.
    """

    counter = 0

    @classmethod
    def _make(cls, start_id: str, end_id: str):
        """
        Creates and returns a temporal interval.
        Generic function for all other methods.
        """
        start = f"__{start_id}__{cls.counter}"
        cls.counter += 1
        end = f"__{end_id}__{cls.counter}"
        cls.counter += 1
        return HtnTemporalInterval(HtnTimepoint(start), HtnTimepoint(end))

    @classmethod
    def default(cls) -> HtnTemporalInterval:
        """
        Creates and returns a default temporal interval.
        Typically used for sequential problems.
        """
        return cls._make("d", "d")

    @classmethod
    def at_start(cls) -> HtnTemporalInterval:
        """
        Creates and returns the temporal interval equivalent to 'at-start' in PDDL.
        """
        return cls._make("s", "s")

    @classmethod
    def at_end(cls) -> HtnTemporalInterval:
        """
        Creates and returns the temporal interval equivalent to 'at-end' in PDDL.
        """
        return cls._make("e", "e")

    @classmethod
    def over_all(cls) -> HtnTemporalInterval:
        """
        Creates and returns the temporal interval equivalent to 'over-all' in PDDL.
        """
        return cls._make("s", "e")


@dataclass(frozen=True)
class HtnSymbol(HtnEntity):
    """
    Represents a symbol of the planning problem.

    It is an abstract class, it must **not be instantiated**.
    """

    name: str

    def __eq__(self, __o: object) -> bool:
        if not isinstance(__o, HtnSymbol):
            return False
        return self.name == __o.name

    def __str__(self) -> str:
        return self.name


@dataclass(frozen=True, eq=False)
class HtnStateVariableSymbol(HtnSymbol):
    """
    Represents the symbol of a state variable.
    e.g. `loc`
    """


@dataclass(frozen=True, eq=False)
class HtnTaskSymbol(HtnSymbol):
    """
    Represents the symbol of a primitive or a compound task.

    It is an abstract class, it must **not be instantiated**.
    """


@dataclass(frozen=True, eq=False)
class HtnPrimitiveTaskSymbol(HtnTaskSymbol):
    """
    Represents the symbol of a primitive task.
    e.g. `pick`
    """


@dataclass(frozen=True, eq=False)
class HtnCompoundTaskSymbol(HtnTaskSymbol):
    """
    Represents the symbol of a compound task.
    e.g. `transfer`
    """


@dataclass(frozen=True, eq=False)
class HtnMethodSymbol(HtnSymbol):
    """
    Represents the symbol of a method.
    """


@dataclass(frozen=True)
class HtnLabel(HtnEntity):
    """
    Represents a label of the HTN language.
    e.g. `l_1`
    """

    value: str

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class HtnParametricSymbol(HtnEntity):
    """
    Represents a symbols associated with parameters.
    e.g. a state variable or a task.
    """

    symbol: HtnSymbol
    params: tuple[HtnTypedObject, ...]

    def __str__(self) -> str:
        return f"{self.symbol}({', '.join(map(str,self.params))})"

    @property
    def all_params(self) -> tuple[HtnTypedObject, ...]:
        """Return all parameters, even the hidden ones."""
        return self.params

    @property
    def constants(self) -> tuple[HtnConstant, ...]:
        """Return only the constant parameters."""
        return tuple(param for param in self.params if isinstance(param, HtnConstant))

    @property
    def variables(self) -> tuple[HtnVariable, ...]:
        """Return only the variable parameters."""
        return tuple(param for param in self.params if isinstance(param, HtnVariable))

    @property
    def timepoints(self) -> tuple[HtnTimepoint, ...]:
        """Return only the timepoint parameters."""
        return tuple(param for param in self.params if isinstance(param, HtnTimepoint))

    def __eq__(self, __o) -> bool:
        if not isinstance(__o, HtnParametricSymbol):
            return False
        if self.symbol != __o.symbol:
            return False
        if len(self.params) != len(__o.params):
            return False
        for param in self.params:
            match: bool = False
            for __o_param in __o.params:
                if param == __o_param:
                    match = True
                    break
            if not match:
                return False
        return True


@dataclass(frozen=True)
class HtnStateVariable(HtnParametricSymbol):
    """
    Represents a state variable of the planning problem.
    e.g. `loc(?r)`
    """

    symbol: HtnStateVariableSymbol
    tpe: HtnType = HTN_BOOLEAN


@dataclass(frozen=True)
class HtnCondition(HtnEntity):
    """
    Represents a condition on a state variable over a temporal interval.
    e.g. `[0,5] loc(?r) = L_0`
    """

    sv: HtnStateVariable
    value: HtnTypedObject = HTN_TRUE
    interval: HtnTemporalInterval = field(
        default_factory=HtnTemporalIntervalFactory.default
    )

    def __str__(self) -> str:
        return f"{self.interval}{self.sv} = {self.value}"


@dataclass(frozen=True)
class HtnEffect(HtnEntity):
    """
    Represents an effect on a state variable over a temporal interval.
    e.g. `[0,5] loc(?r) <-- L_1`
    """

    sv: HtnStateVariable
    value: HtnTypedObject
    interval: HtnTemporalInterval = field(
        default_factory=HtnTemporalIntervalFactory.default
    )

    def __str__(self) -> str:
        return f"{self.interval}{self.sv} <-- {self.value}"


class HtnEffectFactory:
    """Factory of common effects."""

    @classmethod
    def dirac_at_start(
        cls,
        sv: HtnStateVariable,
        value: HtnTypedObject,
    ) -> tuple[HtnEffect, HtnEffect]:
        """
        Create an effect with the given parameters at the start of the task.
        Create an other effect cancelling the previous one immediately.

        /!\\ **Predicates** only.
        """
        return cls.dirac(sv, value, HtnTemporalIntervalFactory.at_start())

    @classmethod
    def dirac_at_end(
        cls,
        sv: HtnStateVariable,
        value: HtnTypedObject,
    ) -> tuple[HtnEffect, HtnEffect]:
        """
        Create an effect with the given parameters at the end of the task.
        Create an other effect cancelling the previous one immediately.

        /!\\ **Predicates** only.
        """
        return cls.dirac(sv, value, HtnTemporalIntervalFactory.at_end() + HTN_EPSILON)

    @classmethod
    def dirac(
        cls,
        sv: HtnStateVariable,
        value: HtnTypedObject,
        interval: HtnTemporalInterval,
    ) -> tuple[HtnEffect, HtnEffect]:
        """
        Create an effect on a predicate with the given parameters.
        Create an other effect cancelling the previous one immediately.

        /!\\ **Predicates** only.
        """
        if sv.tpe != HTN_BOOLEAN:
            raise TypeError(
                f"Dirac are allowed for predicates only. Received a {sv.tpe}"
            )
        opposition_value = HTN_TRUE if value == HTN_FALSE else HTN_FALSE
        return (
            HtnEffect(
                sv=sv,
                value=value,
                interval=interval - HTN_EPSILON,
            ),
            HtnEffect(
                sv=sv,
                value=opposition_value,
                interval=interval,
            ),
        )


@dataclass(frozen=True)
class HtnConstraint(HtnEntity):
    """
    Represents a constraint between two typed objects.
    e.g. `?l_s != ?l_e`
    """

    left: HtnTypedObject
    right: HtnTypedObject
    relation: Literal["==", "!=", "<", "<=", ">", ">="]

    def __str__(self) -> str:
        return f"{self.left.value} {self.relation} {self.right.value}"


@dataclass(frozen=True)
class HtnTemporalConstraint(HtnConstraint):
    """
    Represents a temporal constraint between two timepoints.
    e.g. `?t_e == ?t_s + 10`
    """

    left: HtnTimepoint
    right: HtnTimepoint
    left_label: HtnLabel | None = None
    right_label: HtnLabel | None = None

    def __str__(self) -> str:
        left = (
            f"{self.left_label}_" if self.left_label is not None else ""
        ) + f"{self.left}"
        right = (
            f"{self.right_label}_" if self.right_label is not None else ""
        ) + f"{self.right}"
        return f"{left} {self.relation} {right}"


class ConstraintArgumentError(Exception):
    """Raise when the arguments of a constraint are wrong."""

    def __init__(self, message: str, *args):
        super().__init__(*args)
        self.message = message

    def __str__(self) -> str:
        return f"[ERROR] Constraint Argument\n--> {self.message}"


class HtnConstraintFactory:
    """Factory of common constraints."""

    @classmethod
    def _make(
        cls,
        left: HtnTypedObject,
        right: HtnTypedObject,
        relation: Literal["==", "!=", "<", "<=", ">", ">="],
        lab_left: HtnLabel | None = None,
        lab_right: HtnLabel | None = None,
    ) -> HtnConstraint | HtnTemporalConstraint:
        """Create a constraint."""
        if isinstance(left, HtnTimepoint):
            if not isinstance(right, HtnTimepoint):
                raise ConstraintArgumentError("left is a timepoint but right is not.")
            return HtnTemporalConstraint(left, right, relation, lab_left, lab_right)
        if isinstance(right, HtnTimepoint):
            raise ConstraintArgumentError("right is a timepoint but left is not.")
        if lab_left is not None:
            raise ConstraintArgumentError(
                "lab_left is not necessary for a no-temporal constraint."
            )
        if lab_right is not None:
            raise ConstraintArgumentError(
                "lab_right is not necessary for a no-temporal constraint."
            )
        return HtnConstraint(left, right, relation)

    @classmethod
    def duration(
        cls,
        task_or_interval: HtnTask | HtnTemporalInterval,
        duration: float,
        label: HtnLabel | None = None,
    ) -> HtnTemporalConstraint:
        """Create a temporal constraint specifying the duration for a task."""
        return cls.eq(  # type: ignore
            task_or_interval.end,
            task_or_interval.start + duration,
            label,
            label,
        )

    @classmethod
    def duration_eps(
        cls,
        task_or_interval: HtnTask | HtnTemporalInterval,
        label: HtnLabel | None = None,
    ) -> HtnTemporalConstraint:
        """Create a temporal constraint specifying a very short duration for a task."""
        return cls.duration(
            task_or_interval=task_or_interval,
            duration=HTN_EPSILON,
            label=label,
        )

    @classmethod
    def min_duration(
        cls,
        task_or_interval: HtnTask | HtnTemporalInterval,
        duration: float,
        label: HtnLabel | None = None,
    ) -> HtnTemporalConstraint:
        """Create a temporal constraint specifying a minimal duration for a task."""
        return cls.ge(  # type: ignore
            task_or_interval.end,
            task_or_interval.start + duration,
            label,
            label,
        )

    @classmethod
    def min_duration_eps(
        cls,
        task_or_interval: HtnTask | HtnTemporalInterval,
        label: HtnLabel | None = None,
    ) -> HtnTemporalConstraint:
        """
        Create a temporal constraint specifying a minimal epsilon duration for a task.
        """
        return cls.min_duration(
            task_or_interval=task_or_interval,
            duration=HTN_EPSILON,
            label=label,
        )

    @classmethod
    def eq(
        cls,
        left: HtnTypedObject,
        right: HtnTypedObject,
        lab_left: HtnLabel | None = None,
        lab_right: HtnLabel | None = None,
    ) -> HtnConstraint | HtnTemporalConstraint:
        """Create an equality constraint."""
        return cls._make(left, right, "==", lab_left, lab_right)

    @classmethod
    def neq(
        cls,
        left: HtnTypedObject,
        right: HtnTypedObject,
        lab_left: HtnLabel | None = None,
        lab_right: HtnLabel | None = None,
    ) -> HtnConstraint | HtnTemporalConstraint:
        """Create an different constraint."""
        return cls._make(left, right, "!=", lab_left, lab_right)

    @classmethod
    def gt(
        cls,
        left: HtnTypedObject,
        right: HtnTypedObject,
        lab_left: HtnLabel | None = None,
        lab_right: HtnLabel | None = None,
    ) -> HtnConstraint | HtnTemporalConstraint:
        """Create a greater constraint."""
        return cls._make(left, right, ">", lab_left, lab_right)

    @classmethod
    def ge(
        cls,
        left: HtnTypedObject,
        right: HtnTypedObject,
        lab_left: HtnLabel | None = None,
        lab_right: HtnLabel | None = None,
    ) -> HtnConstraint | HtnTemporalConstraint:
        """Create a greater or equal constraint."""
        return cls._make(left, right, ">=", lab_left, lab_right)

    @classmethod
    def lt(
        cls,
        left: HtnTypedObject,
        right: HtnTypedObject,
        lab_left: HtnLabel | None = None,
        lab_right: HtnLabel | None = None,
    ) -> HtnConstraint | HtnTemporalConstraint:
        """Create a less constraint."""
        return cls._make(left, right, "<", lab_left, lab_right)

    @classmethod
    def le(
        cls,
        left: HtnTypedObject,
        right: HtnTypedObject,
        lab_left: HtnLabel | None = None,
        lab_right: HtnLabel | None = None,
    ) -> HtnConstraint | HtnTemporalConstraint:
        """Create a less or equal constraint."""
        return cls._make(left, right, "<=", lab_left, lab_right)


@dataclass(frozen=True)
class HtnTask(HtnParametricSymbol):
    """
    Represents a primitive or a compound task of the planning problem.
    """

    symbol: HtnTaskSymbol
    interval: HtnTemporalInterval = field(
        default_factory=HtnTemporalIntervalFactory.default
    )

    @property
    def start(self) -> HtnTimepoint:
        """
        Returns
        -------
        HtnTimepoint
            The start timepoint of its interval.
        """
        return self.interval.start

    @property
    def end(self) -> HtnTimepoint:
        """
        Returns
        -------
        HtnTimepoint
            The end timepoint of its interval.
        """
        return self.interval.end

    def __str__(self) -> str:
        return f"{self.interval}{super().__str__()}"

    def __eq__(self, __o: object) -> bool:
        if not super().__eq__(__o):
            return False
        if not isinstance(__o, HtnTask):
            return False
        if self.symbol != __o.symbol:
            return False
        if self.interval != __o.interval:
            return False
        return True


@dataclass(frozen=True)
class HtnPrimitiveTask(HtnTask):
    """
    Represents a primitive task of the planning problem.
    e.g. `[2,5] pick(?p, ?r)`
    """

    symbol: HtnPrimitiveTaskSymbol
    constraints: tuple[HtnConstraint, ...] = ()
    conditions: tuple[HtnCondition, ...] = ()
    effects: tuple[HtnEffect, ...] = ()

    @property
    def all_params(self) -> tuple[HtnTypedObject, ...]:
        all_params = list(self.params)
        sv_params = [param for sv in self.state_variables for param in sv.params]
        for param in sv_params:
            if param not in all_params:
                all_params.append(param)
        return tuple(all_params)

    @property
    def state_variables(self) -> set[HtnStateVariable]:
        """
        Returns
        -------
        set[HtnStateVariable]
            All the state variables which are present in this primitive task.
        """
        return {cont.sv for cont in self.conditions + self.effects}

    def __eq__(self, __o: object) -> bool:
        if not super().__eq__(__o):
            return False
        if not isinstance(__o, HtnPrimitiveTask):
            return False
        if self.constraints != __o.constraints:
            return False
        if self.conditions != __o.conditions:
            return False
        if self.effects != __o.effects:
            return False
        return True


@dataclass(frozen=True)
class HtnCompoundTask(HtnTask):
    """
    Represents a compound task of the planning problem.
    e.g. `[0, 10] transfer(?p, L_2)`
    """

    symbol: HtnCompoundTaskSymbol

    def __eq__(self, __o) -> bool:
        if not super().__eq__(__o):
            return False
        if not isinstance(__o, HtnCompoundTask):
            return False
        return True


@dataclass(frozen=True)
class HtnLabelMappingPair(HtnEntity):
    """Pair of a HTN label and a HTN task."""

    label: HtnLabel
    task: HtnTask

    def __post_init__(self):
        """Check that label is a HTN label."""
        if not isinstance(self.label, HtnLabel):
            raise TypeError(
                f"'label' has to be a HtnLabel instance, received {type(self.label)}."
            )


@dataclass(frozen=True)
class HtnTaskNetwork(HtnEntity):
    """
    Represents a task network of the planning problem.
    """

    label_mapping: tuple[HtnLabelMappingPair, ...] = ()
    constraints: tuple[HtnTemporalConstraint, ...] = ()

    @property
    def tasks(self) -> tuple[HtnTask, ...]:
        """
        Returns
        -------
        tuple[HtnTask, ...]
            The set of tasks contained by `label_mapping`.
        """
        result = [mapping.task for mapping in self.label_mapping]
        return tuple(result)

    def __str__(self) -> str:
        return f"{', '.join(map(str, self.tasks))}"

    def __post_init__(self):
        """Check HtnTaskNetwork attributes."""
        for lmp in self.label_mapping:
            if not isinstance(lmp, HtnLabelMappingPair):
                raise TypeError(
                    f"'label_mapping' has to contain only HtnLabelMappingPair instances, received a {type(lmp)}."  # noqa: E501
                )


# Cannot inherits from `HtnParametricSymbol` because we don't want to
# define the parameters during the initialisation.
@dataclass(frozen=True)
class HtnMethod(HtnEntity):
    """
    Represents a method for the decomposition of a compound task.
    e.g. `transfer ==> {go, pick, go, drop}`
    """

    task: HtnCompoundTask
    task_network: HtnTaskNetwork
    constraints: tuple[HtnConstraint, ...] = ()
    conditions: tuple[HtnCondition, ...] = ()
    symbol: HtnMethodSymbol = field(
        default_factory=lambda: HtnMethodSymbol(f"method_{uuid4()}")
    )

    @property
    def all_params(self) -> tuple[HtnTypedObject, ...]:
        """Return all parameters, even the hidden ones."""
        all_params = set(self.task.all_params)
        for task in self.task_network.tasks:
            all_params.update(task.all_params)
        all_params.update(param for sv in self.state_variables for param in sv.params)
        return tuple(all_params)

    @property
    def state_variables(self) -> set[HtnStateVariable]:
        """
        Returns
        -------
        set[HtnStateVariable]
            All the state variables which are present in this method.
        """
        return {cont.sv for cont in self.conditions}

    @property
    def interval(self) -> HtnTemporalInterval:
        """
        Returns
        -------
        HtnTemporalInterval
            The temporal interval of the achieved task.
        """
        return self.task.interval

    @property
    def params(self) -> tuple[HtnTypedObject, ...]:
        """
        Returns
        -------
        tuple[HtnTypedObject, ...]
            The concatenation of params contained in the task
            and the subtasks of the task network.
        """
        result = set(self.task.params)
        for task in self.task_network.tasks:
            result.update(task.params)
        return tuple(result)

    def __str__(self) -> str:
        return f"{self.interval}{self.symbol}({', '.join(map(str,self.params))})"

    def __repr__(self) -> str:
        return f"{str(self)}\n\t--> {self.task}\n\t==> {{{self.task_network}}}"

    def __post_init__(self):
        """Check Method attributes."""
        if not isinstance(self.task, HtnCompoundTask):
            raise TypeError(
                f"'task' has to be a HtnCompoundTask, received {type(self.task)}."
            )


@dataclass
class HtnLanguage(HtnEntity):
    """
    Represents the language of the planning problem.
    """

    # pylint: disable=invalid-name

    Vars: set[HtnVariable] = field(default_factory=set)
    Csts: set[HtnConstant] = field(default_factory=set)
    StVars: set[HtnStateVariableSymbol] = field(default_factory=set)
    Prims: set[HtnPrimitiveTaskSymbol] = field(default_factory=set)
    Comps: set[HtnCompoundTaskSymbol] = field(default_factory=set)
    Labs: set[HtnLabel] = field(default_factory=set)

    def merge(self, language: HtnLanguage) -> None:
        """
        Merge another language into this one.
        """
        self.Vars.update(language.Vars)
        self.Csts.update(language.Csts)
        self.StVars.update(language.StVars)
        self.Prims.update(language.Prims)
        self.Comps.update(language.Comps)
        self.Labs.update(language.Labs)

    def __str__(self) -> str:
        nl_tab = "\n\t"
        return f"""---- HtnLanguage ----
Vars: \n\t{nl_tab.join(map(str, self.Vars))}
Csts:  \n\t{nl_tab.join(map(str, self.Csts))}
StVars: \n\t{nl_tab.join(map(str, self.StVars))}
Prims: \n\t{nl_tab.join(map(str, self.Prims))}
Comps: \n\t{nl_tab.join(map(str, self.Comps))}
Labs: \n\t{nl_tab.join(map(str, self.Labs))}
--------
"""

    def add_typed_object(self, typed_object: HtnTypedObject):
        """Add task elements to this language"""
        if isinstance(typed_object, HtnConstant):
            return self.Csts.add(typed_object)
        elif isinstance(typed_object, HtnVariable):
            return self.Vars.add(typed_object)
        else:
            raise TypeError(
                f"Cannot add typed object to language. Received a {typed_object.tpe}"
            )

    def add_task(self, task: HtnTask):
        """Add task elements to this language"""
        self.Vars.update(task.variables)
        self.Csts.update(task.constants)
        if isinstance(task, HtnPrimitiveTask):
            self.Prims.add(task.symbol)
            self.StVars.update(sv.symbol for sv in task.state_variables)
        else:
            self.Comps.add(task.symbol)  # type: ignore

    def add_method(self, method: HtnMethod):
        """Add method elements to this language"""
        self.add_task(method.task)
        # conditions
        self.StVars.update(sv.symbol for sv in method.state_variables)
        for lmp in method.task_network.label_mapping:
            self.Labs.add(lmp.label)
            self.add_task(lmp.task)


@dataclass
class HtnDomain(HtnEntity):
    """
    Represents the domain of the planning problem.
    """

    # pylint: disable=invalid-name

    L: HtnLanguage = field(default_factory=HtnLanguage)
    Tp: set[HtnPrimitiveTask] = field(default_factory=set)
    Tc: set[HtnCompoundTask] = field(default_factory=set)
    M: set[HtnMethod] = field(default_factory=set)
    name: str = field(default_factory=lambda: f"domain_{uuid4()}")

    @property
    def state_variables(self) -> set[HtnStateVariable]:
        """
        Returns
        -------
        set[HtnStateVariable]
            All the state variables which are present in this domain.
        """
        result = set()
        for prim in self.Tp:
            result.update(prim.state_variables)
        for method in self.M:
            result.update(method.state_variables)
        return result

    def merge(self, domain: HtnDomain) -> None:
        """
        Merge another domain into this one.
        """
        self.L.merge(domain.L)
        self.Tp.update(domain.Tp)
        self.Tc.update(domain.Tc)
        self.M.update(domain.M)

    def __str__(self) -> str:
        nl_tab = "\n\t"
        return f"""---- HtnDomain ----
L: \n\t{self.L}
Tp: \n\t{nl_tab.join(map(str, self.Tp))}
Tc: \n\t{nl_tab.join(map(str, self.Tc))}
M: \n\t{nl_tab.join(map(repr, self.M))}
name: \n\t{self.name}
--------
"""

    def add_task(self, task: HtnTask):
        """Add task (and its elements) to this domain"""
        self.L.add_task(task)
        if isinstance(task, HtnPrimitiveTask):
            self.Tp.add(task)
        else:
            self.Tc.add(task)  # type: ignore

    def add_method(self, method: HtnMethod):
        """Add task (and its elements) to this domain"""
        self.L.add_method(method)
        self.M.add(method)
        for lmp in method.task_network.label_mapping:
            self.add_task(lmp.task)


@dataclass
class HtnProblem(HtnEntity):
    """
    Represents the planning problem.
    """

    # pylint: disable=invalid-name

    D: HtnDomain = field(default_factory=HtnDomain)
    s_I: set[HtnEffect] = field(default_factory=set)
    tn_I: HtnTaskNetwork | None = None
    name: str = field(default_factory=lambda: f"problem_{uuid4()}")

    @property
    def state_variables(self) -> set[HtnStateVariable]:
        """
        Returns
        -------
        set[HtnStateVariable]
            All the state variables which are present in this problem.
        """
        result = self.D.state_variables
        result.update([effect.sv for effect in self.s_I])
        return result

    def __str__(self) -> str:
        nl_tab = "\n\t"
        return f"""---- HtnProblem ----
D: \n\t{self.D}
s_I: \n\t{nl_tab.join(map(str, self.s_I))}
tn_I: \n\t{self.tn_I}
name: \n\t{self.name}
--------
"""
