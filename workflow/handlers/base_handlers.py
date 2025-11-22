"""Base handlers that eliminate code repetition"""
from typing import Dict, Any, Optional, List
from workflow.state_machine import StepHandler, StepType
import logging

logger = logging.getLogger(__name__)


class QuestionHandler(StepHandler):
    """Handler for simple question steps with options"""

    def __init__(
        self,
        step_name: str,
        question: str,
        options: List[str],
        save_to: Optional[str] = None
    ):
        super().__init__(step_name, StepType.QUESTION)
        self.question = question
        self.options = options
        self.save_to = save_to

    async def get_question(self, session: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "question": self.question,
            "options": self.options,
            "requires_file": False
        }

    async def validate_response(
        self,
        response: Optional[str] = None,
        file_data: Optional[bytes] = None
    ) -> tuple[bool, Optional[str]]:
        if not response:
            return False, "Response is required"
        if response not in self.options:
            return False, f"Invalid option. Must be one of: {', '.join(self.options)}"
        return True, None

    async def process_response(
        self,
        session: Dict[str, Any],
        response: Optional[str] = None,
        **kwargs
    ) -> None:
        """Save response to session"""
        if self.save_to:
            # Support nested path like "temp_data.tipo_pessoa"
            if "." in self.save_to:
                parts = self.save_to.split(".")
                target = session
                for part in parts[:-1]:
                    if part not in target:
                        target[part] = {}
                    target = target[part]
                target[parts[-1]] = response
            else:
                session[self.save_to] = response

        logger.debug(f"Saved response '{response}' to {self.save_to}")


class TextInputHandler(StepHandler):
    """Handler for text input steps"""

    def __init__(
        self,
        step_name: str,
        question: str,
        save_to: str,
        placeholder: Optional[str] = None,
        validation_regex: Optional[str] = None
    ):
        super().__init__(step_name, StepType.TEXT_INPUT)
        self.question = question
        self.save_to = save_to
        self.placeholder = placeholder
        self.validation_regex = validation_regex

    async def get_question(self, session: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "question": self.question,
            "requires_file": False,
            "placeholder": self.placeholder
        }

    async def validate_response(
        self,
        response: Optional[str] = None,
        file_data: Optional[bytes] = None
    ) -> tuple[bool, Optional[str]]:
        if not response or not response.strip():
            return False, "Text input is required"

        if self.validation_regex:
            import re
            if not re.match(self.validation_regex, response):
                return False, f"Invalid format"

        return True, None

    async def process_response(
        self,
        session: Dict[str, Any],
        response: Optional[str] = None,
        **kwargs
    ) -> None:
        """Save text input to session"""
        session[self.save_to] = response.strip()
        logger.debug(f"Saved text input to {self.save_to}")


class FileUploadHandler(StepHandler):
    """Handler for file upload steps with OCR/AI processing"""

    def __init__(
        self,
        step_name: str,
        question: str,
        file_description: str,
        processor: Optional[callable] = None,
        save_to: Optional[str] = None
    ):
        super().__init__(step_name, StepType.FILE_UPLOAD)
        self.question = question
        self.file_description = file_description
        self.processor = processor  # Async function to process file
        self.save_to = save_to

    async def get_question(self, session: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "question": self.question,
            "requires_file": True,
            "file_description": self.file_description
        }

    async def validate_response(
        self,
        response: Optional[str] = None,
        file_data: Optional[bytes] = None
    ) -> tuple[bool, Optional[str]]:
        if not file_data:
            return False, "File is required"
        return True, None

    async def process_response(
        self,
        session: Dict[str, Any],
        response: Optional[str] = None,
        file_data: Optional[bytes] = None,
        filename: Optional[str] = None,
        **kwargs
    ) -> None:
        """Process uploaded file"""
        if self.processor:
            # Call the async processor function
            result = await self.processor(file_data, filename, session, **kwargs)

            if self.save_to and result:
                # Support nested paths
                if "." in self.save_to:
                    parts = self.save_to.split(".")
                    target = session
                    for part in parts[:-1]:
                        if part not in target:
                            target[part] = {}
                        target = target[part]
                    target[parts[-1]] = result
                else:
                    session[self.save_to] = result

                logger.debug(f"Saved processed file result to {self.save_to}")


class DynamicQuestionHandler(QuestionHandler):
    """Handler for questions that change based on session data"""

    def __init__(
        self,
        step_name: str,
        question_template: str,  # e.g. "Tipo do {count}º comprador:"
        options: List[str],
        count_from: str,  # e.g. "compradores" to count session["compradores"]
        save_to: Optional[str] = None
    ):
        super().__init__(step_name, question_template, options, save_to)
        self.question_template = question_template
        self.count_from = count_from

    async def get_question(self, session: Dict[str, Any]) -> Dict[str, Any]:
        # Calculate dynamic count
        count = len(session.get(self.count_from, [])) + 1

        # Format question
        formatted_question = self.question_template.format(count=count)

        return {
            "question": formatted_question,
            "options": self.options,
            "requires_file": False
        }


class CallbackQuestionHandler(QuestionHandler):
    """Handler with callback for custom logic after processing response"""

    def __init__(
        self,
        step_name: str,
        question: str,
        options: List[str],
        save_to: Optional[str] = None,
        on_yes: Optional[callable] = None,
        on_no: Optional[callable] = None
    ):
        super().__init__(step_name, question, options, save_to)
        self.on_yes = on_yes  # Async callback if "Sim"
        self.on_no = on_no    # Async callback if "Não"

    async def process_response(
        self,
        session: Dict[str, Any],
        response: Optional[str] = None,
        **kwargs
    ) -> None:
        """Save response and execute callbacks"""
        # Save response first
        await super().process_response(session, response, **kwargs)

        # Execute callback based on response
        if response == "Sim" and self.on_yes:
            await self.on_yes(session)
        elif response == "Não" and self.on_no:
            await self.on_no(session)


class PersonalizedCertidaoQuestionHandler(CallbackQuestionHandler):
    """Handler for certidão questions that include the person's name"""

    def __init__(
        self,
        step_name: str,
        question_template: str,  # e.g., "Deseja apresentar {certidao_name} para {person_name}?"
        options: List[str],
        certidao_display_name: str,
        person_type: str,  # "vendedor" or "conjuge"
        save_to: Optional[str] = None,
        on_yes: Optional[callable] = None,
        on_no: Optional[callable] = None
    ):
        super().__init__(step_name, question_template, options, save_to, on_yes, on_no)
        self.question_template = question_template
        self.certidao_display_name = certidao_display_name
        self.person_type = person_type

    async def get_question(self, session: Dict[str, Any]) -> Dict[str, Any]:
        """Generate question with person's name"""
        from models.session import ensure_temp_data

        person_name = "N/A"

        if self.person_type == "vendedor":
            # Get current vendedor name
            temp_data = ensure_temp_data(session)
            vendedor_index = temp_data.get("current_vendedor_index")

            if vendedor_index is not None:
                vendedores = session.get("vendedores", [])
                if vendedor_index < len(vendedores):
                    vendedor = vendedores[vendedor_index]
                    person_name = vendedor.get("nome_completo") or vendedor.get("razao_social", "N/A")
            else:
                # If no vendedor finalized yet, get from temp_data
                current_vendedor = temp_data.get("current_vendedor", {})
                person_name = current_vendedor.get("nome_completo") or current_vendedor.get("razao_social", "N/A")

        elif self.person_type == "conjuge":
            # Get current vendedor's cônjuge name
            temp_data = ensure_temp_data(session)
            vendedor_index = temp_data.get("current_vendedor_index")

            if vendedor_index is not None:
                vendedores = session.get("vendedores", [])
                if vendedor_index < len(vendedores):
                    vendedor = vendedores[vendedor_index]
                    conjuge = vendedor.get("conjuge", {})
                    person_name = conjuge.get("nome_completo", "N/A")
            else:
                # Get from temp_data
                current_vendedor = temp_data.get("current_vendedor", {})
                conjuge = current_vendedor.get("conjuge", {})
                person_name = conjuge.get("nome_completo", "N/A")

        formatted_question = self.question_template.format(
            certidao_name=self.certidao_display_name,
            person_name=person_name
        )

        return {
            "question": formatted_question,
            "options": self.options,
            "requires_file": False
        }


class PersonalizedCertidaoFileHandler(FileUploadHandler):
    """Handler for certidão file uploads that include the person's name"""

    def __init__(
        self,
        step_name: str,
        question_template: str,  # e.g., "Faça upload da {certidao_name} para {person_name}:"
        file_description: str,
        certidao_display_name: str,
        person_type: str,  # "vendedor" or "conjuge"
        processor: Optional[callable] = None,
        save_to: Optional[str] = None
    ):
        super().__init__(step_name, question_template, file_description, processor, save_to)
        self.question_template = question_template
        self.certidao_display_name = certidao_display_name
        self.person_type = person_type

    async def get_question(self, session: Dict[str, Any]) -> Dict[str, Any]:
        """Generate question with person's name"""
        from models.session import ensure_temp_data

        person_name = "N/A"

        if self.person_type == "vendedor":
            # Get current vendedor name
            temp_data = ensure_temp_data(session)
            vendedor_index = temp_data.get("current_vendedor_index")

            if vendedor_index is not None:
                vendedores = session.get("vendedores", [])
                if vendedor_index < len(vendedores):
                    vendedor = vendedores[vendedor_index]
                    person_name = vendedor.get("nome_completo") or vendedor.get("razao_social", "N/A")
            else:
                # If no vendedor finalized yet, get from temp_data
                current_vendedor = temp_data.get("current_vendedor", {})
                person_name = current_vendedor.get("nome_completo") or current_vendedor.get("razao_social", "N/A")

        elif self.person_type == "conjuge":
            # Get current vendedor's cônjuge name
            temp_data = ensure_temp_data(session)
            vendedor_index = temp_data.get("current_vendedor_index")

            if vendedor_index is not None:
                vendedores = session.get("vendedores", [])
                if vendedor_index < len(vendedores):
                    vendedor = vendedores[vendedor_index]
                    conjuge = vendedor.get("conjuge", {})
                    person_name = conjuge.get("nome_completo", "N/A")
            else:
                # Get from temp_data
                current_vendedor = temp_data.get("current_vendedor", {})
                conjuge = current_vendedor.get("conjuge", {})
                person_name = conjuge.get("nome_completo", "N/A")

        formatted_question = self.question_template.format(
            certidao_name=self.certidao_display_name,
            person_name=person_name
        )

        return {
            "question": formatted_question,
            "requires_file": True,
            "file_description": self.file_description
        }
