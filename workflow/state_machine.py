"""Base State Machine for Workflow Management"""
from typing import Dict, Any, Optional, Callable, List
from enum import Enum
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class StepType(str, Enum):
    """Types of workflow steps"""
    QUESTION = "question"           # Multiple choice
    TEXT_INPUT = "text_input"       # Free text
    FILE_UPLOAD = "file_upload"     # Document upload
    PROCESSING = "processing"       # Background processing


class TransitionCondition(str, Enum):
    """Conditions for step transitions"""
    ALWAYS = "always"
    IF_YES = "if_yes"
    IF_NO = "if_no"
    IF_FISICA = "if_fisica"
    IF_JURIDICA = "if_juridica"
    CUSTOM = "custom"


class StepHandler(ABC):
    """Abstract base class for step handlers"""

    def __init__(self, step_name: str, step_type: StepType):
        self.step_name = step_name
        self.step_type = step_type

    @abstractmethod
    async def get_question(self, session: Dict[str, Any]) -> Dict[str, Any]:
        """Get the question/prompt for this step"""
        pass

    @abstractmethod
    async def process_response(
        self,
        session: Dict[str, Any],
        response: Optional[str] = None,
        file_data: Optional[bytes] = None,
        filename: Optional[str] = None,
        **kwargs
    ) -> None:
        """Process user response and update session"""
        pass

    async def validate_response(
        self,
        response: Optional[str] = None,
        file_data: Optional[bytes] = None
    ) -> tuple[bool, Optional[str]]:
        """Validate user response. Returns (is_valid, error_message)"""
        return True, None

    def get_next_step(self, session: Dict[str, Any], response: Optional[str] = None) -> Optional[str]:
        """Determine next step based on response"""
        return None  # Override in subclass or use step_definition


class StepDefinition:
    """Declarative step definition"""

    def __init__(
        self,
        name: str,
        step_type: StepType,
        handler: StepHandler,
        next_step: Optional[str] = None,
        transitions: Optional[List[tuple[TransitionCondition, str]]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.name = name
        self.step_type = step_type
        self.handler = handler
        self.next_step = next_step
        self.transitions = transitions or []
        self.metadata = metadata or {}

    def get_next_step_name(self, session: Dict[str, Any], response: Optional[str] = None) -> Optional[str]:
        """Resolve next step based on transitions"""
        # Try transitions first
        for condition, next_step in self.transitions:
            if self._evaluate_condition(condition, session, response):
                return next_step

        # Fallback to default next_step
        return self.next_step

    def _evaluate_condition(
        self,
        condition: TransitionCondition,
        session: Dict[str, Any],
        response: Optional[str]
    ) -> bool:
        """Evaluate transition condition"""
        if condition == TransitionCondition.ALWAYS:
            return True
        elif condition == TransitionCondition.IF_YES:
            return response == "Sim"
        elif condition == TransitionCondition.IF_NO:
            return response == "Não"
        elif condition == TransitionCondition.IF_FISICA:
            return response == "Pessoa Física"
        elif condition == TransitionCondition.IF_JURIDICA:
            return response == "Pessoa Jurídica"
        return False


class WorkflowStateMachine:
    """State machine for managing workflow"""

    def __init__(self):
        self.steps: Dict[str, StepDefinition] = {}
        self.initial_step: Optional[str] = None

    def register_step(self, step_def: StepDefinition):
        """Register a step definition"""
        self.steps[step_def.name] = step_def
        logger.debug(f"Registered step: {step_def.name}")

    def set_initial_step(self, step_name: str):
        """Set the initial step"""
        self.initial_step = step_name

    async def get_step_question(self, session: Dict[str, Any]) -> Dict[str, Any]:
        """Get question for current step"""
        current_step = session.get("current_step")

        if not current_step or current_step not in self.steps:
            raise ValueError(f"Invalid step: {current_step}")

        step_def = self.steps[current_step]
        question = await step_def.handler.get_question(session)

        # Add metadata
        question.update({
            "session_id": session["id"],
            "current_step": current_step,
            "progress": self._calculate_progress(session)
        })

        return question

    async def process_step(
        self,
        session: Dict[str, Any],
        response: Optional[str] = None,
        file_data: Optional[bytes] = None,
        filename: Optional[str] = None,
        **kwargs
    ) -> None:
        """Process current step and transition to next"""
        current_step = session.get("current_step")

        if not current_step or current_step not in self.steps:
            raise ValueError(f"Invalid step: {current_step}")

        step_def = self.steps[current_step]

        # Validate response
        is_valid, error_msg = await step_def.handler.validate_response(response, file_data)
        if not is_valid:
            raise ValueError(error_msg)

        # Process response
        await step_def.handler.process_response(
            session,
            response=response,
            file_data=file_data,
            filename=filename,
            **kwargs
        )

        # Transition to next step
        next_step = step_def.get_next_step_name(session, response)

        if next_step:
            self._validate_transition(current_step, next_step)
            session["current_step"] = next_step
            session["step_number"] = session.get("step_number", 0) + 1
            logger.info(f"Transitioned: {current_step} -> {next_step}")
        else:
            logger.warning(f"No next step defined for: {current_step}")

    def _validate_transition(self, from_step: str, to_step: str):
        """Validate that transition is allowed"""
        # Check if destination step exists
        if to_step not in self.steps:
            raise ValueError(f"Invalid transition: {from_step} -> {to_step} (step not found)")

        # Check if source step exists
        if from_step not in self.steps:
            raise ValueError(f"Invalid transition source: {from_step} (step not found)")

        # Get source step definition
        source_step = self.steps[from_step]

        # Build list of valid destinations from this step
        valid_destinations = set()

        # Add default next_step
        if source_step.next_step:
            valid_destinations.add(source_step.next_step)

        # Add conditional transition destinations
        for _, dest in source_step.transitions:
            valid_destinations.add(dest)

        # Validate transition is in allowed list
        if to_step not in valid_destinations:
            raise ValueError(
                f"Invalid transition: {from_step} -> {to_step}. "
                f"Allowed destinations: {', '.join(sorted(valid_destinations))}"
            )

        logger.debug(f"Validated transition: {from_step} -> {to_step}")
        return True

    def _calculate_progress(self, session: Dict[str, Any]) -> str:
        """Calculate workflow progress"""
        step_num = session.get("step_number", 1)
        total_steps = 20  # Approximate
        return f"Step {step_num} of approximately {total_steps}"

    def get_workflow_map(self) -> Dict[str, List[str]]:
        """Generate a complete workflow map (for debugging/documentation)"""
        workflow_map = {}

        for step_name, step_def in self.steps.items():
            transitions = []

            # Add default next_step
            if step_def.next_step:
                transitions.append(f"default -> {step_def.next_step}")

            # Add conditional transitions
            for condition, next_step in step_def.transitions:
                transitions.append(f"{condition.value} -> {next_step}")

            workflow_map[step_name] = transitions

        return workflow_map

    def visualize_workflow(self) -> str:
        """Generate ASCII visualization of workflow"""
        lines = ["# Workflow Map", ""]

        for step_name, transitions in self.get_workflow_map().items():
            lines.append(f"## {step_name}")
            for transition in transitions:
                lines.append(f"  - {transition}")
            lines.append("")

        return "\n".join(lines)
