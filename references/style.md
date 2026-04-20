# Style

Use this style for the final candidate unless the assignment explicitly requires something else.

Treat the assignment text as higher priority than this style guide.

Aim for coursework code that looks like it was written by a careful student: direct, readable, and task-focused.

## Naming

- Use `snake_case` for variables, functions, helper arrays, constants, and local state.
- Allow short local names such as `i`, `j`, `k`, and `ch` when they are the clearest choice.
- Keep题目指定名、既有接口名、类名和外部常量名 exactly as requested.
- Keep题目指定的源文件名和扩展名 exactly as requested.
- Avoid pinyin names.
- Avoid meaningless core names such as `a`, `b`, `c`, `d`.

Examples:

- `line_count`
- `upper_count`
- `read_input_lines`
- `student_score`
- `i`
- `j`
- `k`
- `ch`

## Structure

- Prefer procedural decomposition over heavy abstraction.
- For small and medium assignments, keep most logic in `main()` plus a few helper functions.
- Extract helper functions when they remove repetition or clarify a distinct subtask.
- Keep helper functions concrete and task-specific; do not build reusable mini-frameworks.
- When the assignment already provides class names, interfaces, or file boundaries, preserve them exactly.
- Avoid introducing extra wrapper layers, generic utilities, or architecture that the task does not need.

## Control Flow And Data

- Prefer arrays, character arrays, plain loops, counters, and straightforward conditionals.
- Prefer explicit state variables over clever condensed expressions.
- Write the solution in the same order the task is naturally explained whenever practical.
- When validation is required, handle invalid input explicitly and locally.
- Use STL only when the statement explicitly allows it and it materially simplifies the solution.
- Avoid template-heavy, meta-programming-heavy, or library-driven designs.

## Input And Output

- Match the statement and `demo.exe` exactly for prompts, labels, spaces, punctuation, and line breaks.
- Do not beautify or normalize the output beyond what the task requires.
- Prefer explicit `cout` sequences over fancy formatting abstractions unless the task clearly benefits from them.
- When interactive-style prompts are required, print them in the same visible order as the reference behavior.

## Comments

- Use comments sparingly.
- Add comments when they help preserve a task rule, a tricky branch, or a required limitation.
- Avoid industrial comments like "utility layer", "core pipeline", or "orchestration".
- Do not add personal signatures or author headers by default.
- If the assignment provides a required comment block, preserve it exactly.

## Complexity Limits

- Avoid making the code look like production infrastructure.
- Avoid unnecessary classes, deep inheritance, advanced polymorphism, or generic helper systems.
- Avoid lambda-heavy code, custom namespaces, and over-engineered abstractions unless the task explicitly calls for them.
- Prefer a solution that is slightly repetitive but obvious over one that is elegant but unusually abstract for coursework.

## Braces

Use Allman braces.

Example:

```cpp
int main()
{
    if (condition)
    {
        run_task();
    }
    return 0;
}
```

Do not place the opening brace on the same line as a function, loop, conditional, or class definition unless the assignment explicitly requires a different format.

## Exceptions

Override these defaults only when one of the following is true:

- the assignment explicitly requires a different naming scheme
- the assignment explicitly requires a different brace style
- a fixed interface name must be preserved exactly
- the provided starter code already defines a structure that must be preserved
