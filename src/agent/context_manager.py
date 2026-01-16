"""
Context Manager for Hermes Agent.

Handles context size tracking and rolling summaries to prevent
token overflow in long-running investigations.
"""

import logging
from typing import List, Optional, TYPE_CHECKING
from dataclasses import dataclass

if TYPE_CHECKING:
    from src.agent.agent_loop import AgentMessage

logger = logging.getLogger(__name__)


@dataclass
class ContextStats:
    """Statistics about current context usage."""
    total_chars: int
    message_count: int
    user_messages: int
    tool_messages: int
    percentage_used: float  # 0.0 - 1.0


class ContextManager:
    """
    Manages context window size for the agent.
    
    Tracks usage, triggers summarization when needed, and compresses
    history to keep the agent within token limits.
    """
    
    # Approximate limits for 8B models with ~8k token context
    # Using chars as proxy (~4 chars per token)
    MAX_CONTEXT_CHARS = 24000  # ~6k tokens, leaving room for response
    SUMMARY_THRESHOLD = 18000  # ~4.5k tokens, trigger summarization
    MIN_RECENT_MESSAGES = 4    # Always keep last N messages uncompressed
    
    SUMMARY_PROMPT = """Summarize the following OSINT investigation conversation.
Focus on:
1. What targets were investigated
2. What tools were run and their key findings
3. Any entities discovered (usernames, emails, accounts, etc.)

Keep the summary concise but include all important findings.

Conversation to summarize:
{conversation}

Summary:"""

    def __init__(
        self,
        max_chars: int = MAX_CONTEXT_CHARS,
        summary_threshold: int = SUMMARY_THRESHOLD
    ):
        """
        Initialize the context manager.
        
        Args:
            max_chars: Maximum context size in characters
            summary_threshold: Threshold to trigger summarization
        """
        self.max_chars = max_chars
        self.summary_threshold = summary_threshold
        self._summary_cache: Optional[str] = None
    
    def get_stats(self, messages: List["AgentMessage"]) -> ContextStats:
        """
        Calculate context statistics.
        
        Args:
            messages: List of conversation messages
            
        Returns:
            ContextStats with usage information
        """
        total_chars = sum(len(msg.content) for msg in messages)
        user_msgs = sum(1 for msg in messages if msg.role == "user")
        tool_msgs = sum(1 for msg in messages if msg.role == "tool")
        
        return ContextStats(
            total_chars=total_chars,
            message_count=len(messages),
            user_messages=user_msgs,
            tool_messages=tool_msgs,
            percentage_used=min(1.0, total_chars / self.max_chars)
        )
    
    def should_summarize(self, messages: List["AgentMessage"]) -> bool:
        """
        Check if context should be summarized.
        
        Args:
            messages: Current message history
            
        Returns:
            True if summarization is recommended
        """
        stats = self.get_stats(messages)
        return stats.total_chars > self.summary_threshold
    
    async def summarize_history(
        self,
        messages: List["AgentMessage"],
        ollama_client
    ) -> Optional[str]:
        """
        Use LLM to summarize conversation history.
        
        Args:
            messages: Messages to summarize
            ollama_client: Ollama client for LLM calls
            
        Returns:
            Summary string or None if failed
        """
        if not messages:
            return None
        
        # Build conversation text
        conversation_parts = []
        for msg in messages:
            role = msg.role.upper()
            conversation_parts.append(f"[{role}]: {msg.content}")
        
        conversation_text = "\n\n".join(conversation_parts)
        
        # Truncate if too long for summarization
        if len(conversation_text) > 10000:
            conversation_text = conversation_text[:10000] + "\n[...truncated...]"
        
        prompt = self.SUMMARY_PROMPT.format(conversation=conversation_text)
        
        try:
            summary = await ollama_client.generate(prompt)
            if summary:
                self._summary_cache = summary
                logger.info(f"Generated context summary: {len(summary)} chars")
            return summary
        except Exception as e:
            logger.error(f"Failed to generate summary: {e}")
            return None
    
    def compress_context(
        self,
        messages: List["AgentMessage"],
        summary: str
    ) -> List["AgentMessage"]:
        """
        Replace old messages with a summary message.
        
        Keeps the most recent messages and replaces older ones
        with a single summary message.
        
        Args:
            messages: Current message list
            summary: Summary of older messages
            
        Returns:
            New compressed message list
        """
        from src.agent.agent_loop import AgentMessage
        
        if len(messages) <= self.MIN_RECENT_MESSAGES:
            return messages
        
        # Keep recent messages
        recent = messages[-self.MIN_RECENT_MESSAGES:]
        
        # Create summary message
        summary_msg = AgentMessage(
            role="system",
            content=f"[CONTEXT SUMMARY - Previous conversation summarized]\n\n{summary}"
        )
        
        logger.info(
            f"Compressed context: {len(messages)} messages → "
            f"1 summary + {len(recent)} recent"
        )
        
        return [summary_msg] + recent
    
    async def maybe_compress(
        self,
        messages: List["AgentMessage"],
        ollama_client
    ) -> List["AgentMessage"]:
        """
        Check and compress context if needed.
        
        Args:
            messages: Current messages
            ollama_client: For LLM summarization
            
        Returns:
            Possibly compressed message list
        """
        if not self.should_summarize(messages):
            return messages
        
        # Determine how many messages to summarize
        # Keep MIN_RECENT_MESSAGES, summarize the rest
        if len(messages) <= self.MIN_RECENT_MESSAGES:
            return messages
        
        to_summarize = messages[:-self.MIN_RECENT_MESSAGES]
        
        summary = await self.summarize_history(to_summarize, ollama_client)
        if summary:
            return self.compress_context(messages, summary)
        
        # Failed to summarize - return original
        return messages
    
    def get_cached_summary(self) -> Optional[str]:
        """Get the last generated summary."""
        return self._summary_cache
