"""SSE event formatter for ag-ui protocol."""
import json
from typing import Dict, Any, Optional
from datetime import datetime


class SSEFormatter:
    """Formats events according to the ag-ui protocol for SSE streaming."""

    @staticmethod
    def format_thought(content: str, timestamp: Optional[datetime] = None) -> str:
        """
        Format a thought event.

        Args:
            content: Thought content
            timestamp: Optional timestamp

        Returns:
            Formatted SSE event string
        """
        event = {
            "type": "thought",
            "data": {
                "content": content
            },
            "timestamp": (timestamp or datetime.utcnow()).isoformat()
        }
        return f"data: {json.dumps(event)}\n\n"

    @staticmethod
    def format_tool_call(
        tool_name: str,
        arguments: Dict[str, Any],
        tool_call_id: Optional[str] = None,
        timestamp: Optional[datetime] = None
    ) -> str:
        """
        Format a tool call event.

        Args:
            tool_name: Name of the tool being called
            arguments: Tool arguments
            tool_call_id: Optional tool call identifier
            timestamp: Optional timestamp

        Returns:
            Formatted SSE event string
        """
        event = {
            "type": "tool_call",
            "data": {
                "tool_name": tool_name,
                "arguments": arguments,
                "tool_call_id": tool_call_id
            },
            "timestamp": (timestamp or datetime.utcnow()).isoformat()
        }
        return f"data: {json.dumps(event)}\n\n"

    @staticmethod
    def format_tool_call_result(
        tool_name: str,
        result: Any,
        success: bool = True,
        tool_call_id: Optional[str] = None,
        timestamp: Optional[datetime] = None
    ) -> str:
        """
        Format a tool call result event.

        Args:
            tool_name: Name of the tool that was called
            result: Tool execution result
            success: Whether the tool call was successful
            tool_call_id: Optional tool call identifier
            timestamp: Optional timestamp

        Returns:
            Formatted SSE event string
        """
        event = {
            "type": "tool_call_result",
            "data": {
                "tool_name": tool_name,
                "result": result,
                "success": success,
                "tool_call_id": tool_call_id
            },
            "timestamp": (timestamp or datetime.utcnow()).isoformat()
        }
        return f"data: {json.dumps(event)}\n\n"

    @staticmethod
    def format_text(content: str, timestamp: Optional[datetime] = None) -> str:
        """
        Format a text event.

        Args:
            content: Text content
            timestamp: Optional timestamp

        Returns:
            Formatted SSE event string
        """
        event = {
            "type": "text",
            "data": {
                "content": content
            },
            "timestamp": (timestamp or datetime.utcnow()).isoformat()
        }
        return f"data: {json.dumps(event)}\n\n"

    @staticmethod
    def format_error(
        error_message: str,
        error_code: Optional[str] = None,
        timestamp: Optional[datetime] = None
    ) -> str:
        """
        Format an error event.

        Args:
            error_message: Error message
            error_code: Optional error code
            timestamp: Optional timestamp

        Returns:
            Formatted SSE event string
        """
        event = {
            "type": "error",
            "data": {
                "message": error_message,
                "code": error_code
            },
            "timestamp": (timestamp or datetime.utcnow()).isoformat()
        }
        return f"data: {json.dumps(event)}\n\n"

    @staticmethod
    def format_done() -> str:
        """
        Format a completion event.

        Returns:
            Formatted SSE event string
        """
        return "data: [DONE]\n\n"

    @staticmethod
    def format_custom(event_type: str, data: Dict[str, Any], timestamp: Optional[datetime] = None) -> str:
        """
        Format a custom event.

        Args:
            event_type: Custom event type
            data: Event data
            timestamp: Optional timestamp

        Returns:
            Formatted SSE event string
        """
        event = {
            "type": event_type,
            "data": data,
            "timestamp": (timestamp or datetime.utcnow()).isoformat()
        }
        return f"data: {json.dumps(event)}\n\n"

    @staticmethod
    def format_event(event_dict: Dict[str, Any], timestamp: Optional[datetime] = None) -> str:
        """
        Format an event from a dictionary containing type and data.

        Args:
            event_dict: Dictionary with 'type' and 'data' keys
            timestamp: Optional timestamp

        Returns:
            Formatted SSE event string
        """
        event_type = event_dict.get("type")
        event_data = event_dict.get("data", {})
        return SSEFormatter.format_custom(event_type, event_data, timestamp)
