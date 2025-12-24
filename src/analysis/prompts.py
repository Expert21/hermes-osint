"""
OSINT-focused prompt templates for LLM analysis.
"""

SYSTEM_PROMPT = """You are an OSINT (Open Source Intelligence) analyst assistant. 
Your role is to analyze data gathered from various intelligence tools and provide 
actionable insights. Be concise, factual, and highlight the most significant findings.
Format your responses clearly with sections when appropriate."""


SUMMARIZE_FINDINGS = """Analyze the following OSINT data and provide a concise summary 
of the key findings. Focus on:
1. Most significant discoveries
2. Potential identity connections
3. Risk indicators or red flags
4. Recommended next steps for investigation

DATA:
{data}

Provide your analysis:"""


IDENTIFY_PATTERNS = """Review the following entities discovered during an OSINT investigation.
Identify any patterns, connections, or relationships that may not be immediately obvious.
Look for:
- Behavioral patterns (naming conventions, timing, platform choices)
- Hidden connections between seemingly unrelated entities
- Anomalies that warrant further investigation

ENTITIES:
{entities}

Provide your pattern analysis:"""


PRIORITIZE_LEADS = """Given the following OSINT findings, rank and prioritize the leads 
by investigative value. Consider:
- Uniqueness and specificity of the information
- Potential for further pivoting
- Confidence level of the data
- Relevance to the original target

FINDINGS:
{findings}

Provide a prioritized list with brief justifications:"""


GENERATE_NARRATIVE = """Create a professional intelligence report narrative based on 
the following OSINT data. The narrative should:
- Be written in a formal, analytical tone
- Present findings in logical order
- Highlight key discoveries and their significance
- Note any gaps or limitations in the data

TARGET: {target}
DATA:
{data}

Write the report narrative:"""


def format_prompt(template: str, **kwargs) -> str:
    """Format a prompt template with provided data."""
    return template.format(**kwargs)
