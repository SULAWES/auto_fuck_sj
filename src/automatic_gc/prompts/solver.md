You are generating a coursework-style C++ submission.

Read these workspace files first:

- $problem_context_path
- $testcase_path

Task constraints:

- This is attempt $attempt_number.
- Generate exactly these source files:
$required_cpp_names
- Keep the code correct before trying to optimize style.
- The code should look like a solid computer science student's coursework submission.
- Do not make it look industrial or overly engineered.
- Do not use meaningless variable names like a, b, c, d for core logic variables.
- Do not use pinyin identifiers.
- If multiple .cpp files are requested, make them compile together as one program unless the problem context clearly implies otherwise.

Feedback from previous attempts:
$feedback_text

Output rules:

- Return JSON only, matching the provided schema.
- Put full source text in each file entry.
- Keep assumptions short and explicit.
