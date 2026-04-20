# Constraints

This skill treats hard constraints and style constraints separately.

When the user supplies explicit constraints before the PDF, treat those constraints as the highest-priority written specification.

Unless the statement explicitly allows STL, default to non-STL implementations. In ambiguous cases, prefer arrays, character arrays, plain loops, and straightforward control flow.

## Common hard bans

Infer or enforce these when the statement says they are forbidden:

- STL containers or algorithms
- recursion
- `string`
- classes or structs
- templates

Do not rely on a perfect parser. String-based checks are acceptable for quick local validation.

## STL default

- If the statement explicitly says STL is allowed, use it only when it materially simplifies the solution.
- If the statement is silent, default to not using STL.
- If the statement forbids STL, treat any STL usage as a hard violation.

## Common style warnings

These are not immediate blockers unless the user explicitly asks for them or unless the current skill configuration promotes them to final-output requirements:

- advanced template-heavy code
- lambda-heavy code
- custom namespaces
- overly polished abstractions
- meaningless single-letter core variable names
- non-`snake_case` identifiers
- non-Allman opening braces

## Priority

1. correctness
2. hard constraint compliance
3. style fit

Never downgrade style in a way that weakens correctness validation.

For this skill's default final-output policy:

- prefer non-STL implementations unless explicitly allowed
- prefer `snake_case` for identifiers
- prefer Allman braces
- allow deviations only when the assignment explicitly requires them
