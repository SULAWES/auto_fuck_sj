# Constraints

This skill treats hard constraints and style constraints separately.

When the user supplies explicit constraints before the PDF, treat those constraints as the highest-priority written specification.

Unless the statement explicitly allows STL, default to non-STL implementations. In ambiguous cases, prefer arrays, character arrays, plain loops, and straightforward control flow.

## Course knowledge model

Treat these as the course knowledge categories:

- comparison, logical, and conditional operators
- branch statements
- loops
- pointers
- references
- functions
- arrays
- structs
- classes

When the PDF has a whitelist near the start, use that whitelist to decide what can be used. When the PDF says a later-topic group is forbidden, infer the remaining earlier categories as available only if they are consistent with the task.

Example: if the PDF says `本次作业不允许使用包括但不限于指针、引用、结构体、类等相关概念`, then use comparison/logical/conditional operators, branches, loops, functions, and arrays, while avoiding pointers, references, structs, and classes.

If there is no clear whitelist, be conservative with pointers, references, structs, and classes. Global variables are allowed only when the PDF supports them or the task strongly requires them.

## Common hard bans

Infer or enforce these when the statement says they are forbidden:

- STL containers or algorithms
- pointer and reference usage
- recursion
- `string`
- classes or structs
- templates

Do not rely on a perfect parser. String-based checks are acceptable for quick local validation.

## STL default

- If the statement explicitly says STL is allowed, use it only when it materially simplifies the solution.
- If the statement is silent, default to not using STL.
- If the statement forbids STL, treat any STL usage as a hard violation.

## Previous-assignment references

Previous assignments may be used to clarify conventions, such as prompt wording, error handling, input shapes, and likely knowledge boundaries. They are not a source of code to copy. If a previous assignment conflicts with the current PDF or explicit user constraints, follow the current PDF and explicit constraints.

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
