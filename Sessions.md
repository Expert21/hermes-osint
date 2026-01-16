Session Breakdown for Hermes v3.0
Session 1: Core Agent Loop Foundation
Goal: Get a basic ReAct loop working with ONE tool

Deliverables:

AgentLoop class with think → act → observe cycle
Tool registry schema (just Sherlock to start)
Basic Ollama function calling integration
Entity passthrough from existing adapter
Exit Criteria: Can run "Check username test123" and get structured Sherlock results back through the loop

Session 2: TUI Shell
Goal: Replace argparse with conversational interface

Deliverables:

prompt_toolkit REPL with history
Status bar (model, context usage, active tool)
Ctrl+C graceful interrupt
Basic styling/colors
Exit Criteria: Can have a multi-turn conversation with the agent in the terminal

Session 3: Tool Expansion
Goal: Wire up remaining 6 tools to the agent

Deliverables:

Full tool registry with all adapters
Tool selection logic in agent prompts
Stealth mode awareness in tool metadata
Error handling when tools fail
Exit Criteria: Agent can reason about which tool fits a query and execute any of the 7

Session 4: Grounding & Safety Layer
Goal: Prevent hallucinations and enforce structure

Deliverables:

Tool call validator with schema enforcement
Entity-only output formatting
Citation requirement in prompts
Audit trail for claims → entities
Exit Criteria: Agent cannot report findings that don't exist in Entity data

Session 5: Context Management
Goal: Handle long investigations without blowing context

Deliverables:

Context token counter
Rolling summary trigger at 70% capacity
Investigation state object (InvestigationMemory)
Session save/restore to disk
Exit Criteria: Can run 20+ tool calls without context overflow

Session 6: CLI Fallback & Polish
Goal: Keep power users happy, polish UX

Deliverables:

--headless mode that bypasses TUI
Progress bars during tool execution
Investigation export to Markdown
--resume <session-id> flag
Exit Criteria: Both TUI and CLI modes work, can export a readable report

Visual Summary
Session 1 ─┬─ AgentLoop + 1 tool (foundation)
           │
Session 2 ─┼─ TUI shell (interface)
           │
Session 3 ─┼─ All 7 tools (horizontal expansion)
           │
Session 4 ─┼─ Safety/grounding (reliability)
           │
Session 5 ─┼─ Context management (scale)
           │
Session 6 ─┴─ CLI mode + polish (completeness)
Time Estimates
Session	Complexity	Est. Time
1	🟡 Medium	3-4 hours
2	🟢 Easy	2-3 hours
3	🟢 Easy	2-3 hours
4	🟡 Medium	3-4 hours
5	🔴 Hard	4-5 hours
6	🟢 Easy	2-3 hours
Total: ~18-22 hours of focused work

