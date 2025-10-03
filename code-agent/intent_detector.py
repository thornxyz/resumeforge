"""Intent detection for user messages"""

from typing import Dict, Any, List


class IntentDetector:
    """Detects user intent and determines which tools to use"""

    @staticmethod
    def detect(message: str) -> Dict[str, Any]:
        """
        Determine user intent and needed tools from the message

        Returns:
            dict with action, tools_needed, and confidence
        """
        ml = message.lower()

        # Template generation
        if any(w in ml for w in ["template", "start", "create resume", "new resume"]):
            return {
                "action": "generate_template",
                "tools_needed": ["template_generator"],
                "confidence": 0.9,
            }

        # Compilation
        if any(w in ml for w in ["compile", "build", "pdf", "generate pdf"]):
            return {
                "action": "compile",
                "tools_needed": ["validator", "compiler"],
                "confidence": 0.9,
            }

        # Validation
        if any(w in ml for w in ["validate", "check", "errors", "syntax"]):
            return {
                "action": "validate",
                "tools_needed": ["validator"],
                "confidence": 0.8,
            }

        # Enhancement
        if any(w in ml for w in ["improve", "enhance", "better", "suggestions"]):
            return {
                "action": "enhance",
                "tools_needed": ["enhancer"],
                "confidence": 0.8,
            }

        # Formatting
        if any(w in ml for w in ["format", "clean", "organize"]):
            return {
                "action": "format",
                "tools_needed": ["formatter"],
                "confidence": 0.8,
            }

        # Section extraction
        if any(w in ml for w in ["section", "extract", "show me"]):
            return {
                "action": "extract",
                "tools_needed": ["extractor"],
                "confidence": 0.7,
            }

        # Modification
        if any(w in ml for w in ["change", "modify", "update", "add", "remove"]):
            return {
                "action": "modify",
                "tools_needed": ["validator", "enhancer"],
                "confidence": 0.7,
            }

        # Default to chat
        return {
            "action": "chat",
            "tools_needed": [],
            "confidence": 0.5,
        }
