# agentic-comm-automator/src/template_renderer.py
"""
Simple template renderer.

Two kinds of placeholders are supported:
  * ${ENV_VAR}      -> replaced with the value of an environment variable (UPPER_CASE names only),
                       e.g. "${SENDER_EMAIL}" in the JSON config.
  * {context_key}   -> Python str.format syntax filled from the agent context,
                       e.g. "{report_date}", "{sales_figure:,.2f}", "{attachments_meta[0][filename]}".

Note: "${sales_figure:.2f}" is NOT an env var (lower-case name) – it renders as a literal "$"
followed by the formatted number, e.g. "$12345.67".
"""
import os
import re
import string

from .utils import setup_logging

logger = setup_logging(__name__)

ENV_PATTERN = re.compile(r"\$\{([A-Z][A-Z0-9_]*)\}")


class TemplateRenderer:
    def __init__(self):
        self._formatter = string.Formatter()
        logger.debug("TemplateRenderer initialized.")

    @staticmethod
    def resolve_env(template_string):
        """Substitutes ${ENV_VAR} placeholders. Braces in values are escaped for the formatter."""

        def _replace(match):
            var = match.group(1)
            value = os.getenv(var)
            if value is None:
                raise ValueError(f"Environment variable '{var}' is referenced in the config but not set in .env")
            return value.replace("{", "{{").replace("}", "}}")

        return ENV_PATTERN.sub(_replace, template_string)

    def render(self, template_string, context):
        """Renders a template string using a dictionary context."""
        if template_string is None:
            return ""
        if not isinstance(template_string, str):
            return template_string
        resolved = self.resolve_env(template_string)
        try:
            return self._formatter.vformat(resolved, (), context)
        except KeyError as e:
            logger.error(f"Missing key in template context: {e}. Template: '{template_string}'")
            raise ValueError(f"Missing context key: {e}") from e
        except (IndexError, AttributeError, TypeError) as e:
            logger.error(f"Invalid placeholder in template '{template_string}': {e}")
            raise ValueError(f"Invalid placeholder in template '{template_string}': {e}") from e
