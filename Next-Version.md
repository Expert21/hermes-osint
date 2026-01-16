Hermes v3.0: The Agentic OSINT Analyst

Architectural Vision & Design Philosophy
1. The Core Concept

Hermes is no longer just a tool runner; Hermes is an Analyst. The previous version was a pipeline (A → B → C). The new version is a loop (Observe → Reason → Act).

The goal is to invert the control relationship:

    Old Way: The Python code dictates the flow, and the LLM is just a summarizer at the end.

    New Way: The LLM dictates the flow (reasoning), and the Python code serves as the "Scaffolding"—the hands and eyes that safely interact with the world.

2. The Architecture: "The Scaffolding Pattern"

We are treating the existing Python application not as the "Main Program," but as the Runtime Environment for the AI Agent.
The Components

    The Mind (The Agent): A local LLM (via Ollama) that maintains a conversation loop. It has no direct access to the OS; it only has access to "Functions."

    The Hands (The Scaffolding): Your existing, battle-tested Python logic.

        DockerManager: The "glove box" that handles dangerous tools.

        InputValidator: The "reflex" that stops the Agent from hallucinating dangerous commands.

        SecretsManager: The "keychain" the Agent cannot see but can use.

    The Protocol (The Schema): The strict JSON contract between The Mind and The Hands. The Agent cannot just "chat" with tools; it must fill out a specific Schema to invoke them.

3. The Execution Loop (ReAct Pattern)

Instead of a linear script, the main entry point is now a State Machine:

    1. USER_INPUT: "Find out if user 'chloe_77' has a GitHub."

    2. REASONING: The Agent parses the request. Thought: I need to check usernames. I have a tool called sherlock.

    3. TOOL_CALL: The Agent emits a structured signal:
    ``{ "tool": "sherlock", "args": { "username": "chloe_77" } }``
    
    4. SCAFFOLDING (Python):

        Intercepts the call.

        Validates: Is "chloe_77" safe? Is sherlock installed?

        Executes: Spins up the Docker container.

        Parses: Takes the raw tool output and forces it into the Entity schema.

    5. OBSERVATION: The Scaffolding feeds the structured data back to the Agent.
    ``[ { "type": "account", "platform": "github", "url": "..." } ]``

    6. SYNTHESIS: The Agent reads the observation. Thought: I found it. I should tell the user.

    RESPONSE: "I found a GitHub account for chloe_77 at [url]."

4. Key Directives

    A. Interaction First: 
    Hermes lives in a TUI (Terminal User Interface). The user does not pass flags (--target); the user converses. Hermes asks clarifying questions ("I found 3 emails, which one should I investigate?").

    B. Forced Structure: 
    The LLM is smart but chaotic. The Python layer acts as the Strict Parent:

        The LLM never sees raw stdout.

        The LLM only sees Typed Objects (e.g., Entity(type='email', value='...')).

    This prevents "hallucinated findings" because the data source is grounded in code execution.

    C. Security as a Capability:
        Your existing security features (Plugin AST scanning, Container isolation) are now Safety Guarantees.

        The Agent is "sandboxed" by design. Even if prompt-injected to "delete everything," the Python Scaffolding layer lacks the delete_system tool, so the action fails safely.

5. Technical Stack Transition

    | Feature | Old Hermes (v2.1) | New Hermes (v3.0) |
    | :--- | :--- | :--- |
    | **Control Flow** | WorkflowManager (Linear) | AgentLoop (Recursive) |
    | **Input** | `argparse` (CLI Flags) | `prompt_toolkit` (Chat REPL) |
    | **Tool Execution** | Hardcoded Sequence | LLM Function Calling |
    | **Data Flow** | Tool → Text → Report | Tool → Schema → Context Window |
    | **User Role** | Operator (Starts script, waits) | Partner (Collaborates during scan) |