# Worked maths solution — version 1

Solve the supplied problem exactly as written in the target language. Produce a clear mathematical solution suitable for SFT. The problem, its assumptions and requested outputs are fixed. A reference solution, if provided, may be wrong; its final answer is not a target to force.

Provide a complete derivation or proof: justify each substantive transformation, identify the conditions that make it valid, cover every required case and subquestion, and give the result in the requested form and units. For equations preserve domains and check extraneous solutions; for geometry rely only on supplied facts; for probability identify the relevant conditioning and sample space. These checks apply when relevant, not as boilerplate sections in every answer.

Use enough explanation for the derivation to be verifiable. Compress repetition, not necessary reasoning. Do not impose a word band, omit a hard step, pad with “understand the problem” scaffolding, or replace a proof with an unexplained final number. Output the mathematical explanation, not private deliberation or a narrative about your solving process.

Use natural target-language prose and consistent notation. In Greek prose use decimal commas where unambiguous, but leave code and structured mathematical notation valid. Preserve exact values unless approximation is asked for; explain any justified rounding. Unless the question specifies another format, finish Greek solutions with “Απάντηση:” followed by all required results and units. A proof-only question ends with its proved conclusion. The separate final_answers field lists one result per requested part.

If the premises do not determine a unique result, contradict each other, or require unavailable material, identify the precise issue. Do not introduce an unstated assumption to get a number. If the intended task is to establish impossibility or underdetermination, give that valid conclusion. Otherwise return needs_review and identify the missing condition. Preserve the problem text.

Return one JSON object with: row_id; status (candidate or needs_review); solution_text; final_answers (part, expression, unit, approximation); reference_corrections (empty when no reference is supplied or no discrepancy is found); issues; checks_needed. Record any correction to a supplied derivation, even when its final answer was right. A fresh verification call must receive the problem alone, without this solution or reference.
