You are generating test inputs for a coursework C++ problem.

Read this file first:

- $problem_context_path

Task:

- Produce up to $generated_case_count input cases.
- Cases should be diverse and useful for catching boundary errors.
- Keep cases realistic for the described problem constraints.
- Do not invent impossible input formats.
- Prefer small and medium cases when the statement is unclear.

Output rules:

- Return JSON only, matching the provided schema.
- Each case must include a stable name, the exact input text, and a short purpose.
