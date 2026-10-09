---
name: eval-subagent
description: >-
  Use this skill to execute behavioral evaluation tests, run the regression suite,
  or perform LLM-as-a-judge grading via run_evals.py. Trigger only when modifying core
  LangGraph nodes, graph routing edges, prompt engineering, or scoring algorithms.
---

# Eval Subagent Workflow

The **Eval Subagent** is responsible for test-driven verification, regression testing, and LLM-as-a-judge grading for the Job Hunter Agent.

## When to Activate This Skill
Activate this skill when:
- **Modifying Core Prompts:** Changes to Gemini or Ollama prompts in `agent_graph.py` (e.g., tailor, evaluator, or router prompts).
- **Altering Graph Architecture:** Adding or modifying LangGraph nodes, routing edges, or state fields in `state.py` / `agent_graph.py`.
- **Modifying Scoring Logic:** Changing the mathematical NLP algorithm, keyword extractors, or match thresholds.
- **Verifying Regressions:** When the user asks to run evals or test agent accuracy.

## Workflow Procedures

### 1. Behavioral Scenario Coverage
When a new agent capability is introduced:
- Check `run_evals.py` for corresponding mock scenarios (`PERFECT_MATCH_JOB`, `TERRIBLE_MATCH_JOB`).
- Add a new test function covering the behavioral edge cases if missing.

### 2. LLM-as-a-Judge Evaluation
- Use the local Ollama `judge_llm` instance in `run_evals.py` to audit model outputs for hallucinations, formatting fidelity, or prompt compliance.
- Keep the judge prompt strict (e.g., deterministic binary output like YES/NO).

### 3. Execution & Verification
Run the eval suite via terminal:
```powershell
venv\Scripts\python run_evals.py
```
Inspect the output to confirm all behavioral assertions pass before declaring the task complete.
