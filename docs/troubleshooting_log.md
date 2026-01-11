# Troubleshooting Log: "Sales" KeyError

**Date:** 2026-01-22
**Issue:** User reported `JSON-RPC Error code=-32603 data=None message="'Sales'"` when launching the LangChain Reader.

## Investigation
1.  **Code Review**: Checked `src/agents/langchain_agent.py` and `a2a_servers.py`. No references to "Sales" were found in the source code.
2.  **Grep**: Searching for "Sales" revealed matches in `__pycache__` (compiled bytecode) but not in active `.py` files.
3.  **Process Check**: Ran `lsof -i :8001`. Found 3 Python processes (`20324`, `20325`, `20326`) running.
4.  **Conclusion**: These processes were "zombies" from a previous run of the Sales Demo code. Because they were holding the ports, the new Travel App code couldn't bind, but the UI was talking to the *old* agents.

## Resolution
1.  **Ghost Busted**: Killed PIDs 20324-20326.
2.  **Cache Cleared**: Removed all `__pycache__` directories.
3.  **Script Hardening**: Updated `setup_and_run.sh` to automatically detect and kill any process on ports 8001-8003 before starting. This prevents this issue from recurring.
4.  **Refactoring**: Renamed `sales_records` parameter to `records` in `crewai_agent.py`, `autogen_agent.py`, and `a2a_servers.py` to strictly remove all Sales terminology.

## Verification
- Codebase is now 100% clean of "Sales".
- Startup script now enforces a clean state.
- System is ready for relaunch.
