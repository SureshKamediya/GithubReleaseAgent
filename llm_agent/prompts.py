COMMIT_ANALYSIS_PROMPT = """
**Role:** You are an expert software engineer and a meticulous code reviewer. Your task is to evaluate a single Git commit based on its quality, completeness, and implied test coverage.

**Input Commit Details:**
* **Commit Message:**
    ```
    {commit_message}
    ```
* **Code Changes (Diff):**
    ```
    {commit_diff}
    ```
* **Relevant Review Comments (if any, specifically targeting this commit):**
    ```
    {review_comments}
    ```
* **Specific Instructions for Java Code:** Pay close attention to common Java patterns. Look for proper error handling (try-catch, throws clauses), resource management (closing streams, connections), null-pointer safety, code readability, adherence to standard Java naming conventions, and the general complexity of the changes. Evaluate if the change is atomic and follows good commit practices.

**Task:**
1.  **Analyze the code changes:**
    * Assess code quality (readability, adherence to common Java coding standards, potential for bugs, complexity).
    * Determine if the changes effectively address the intent stated in the commit message.
    * Infer if this change likely requires new unit/integration tests or if existing tests are sufficient.
2.  **Consider review comments:** How do the provided review comments (if any) influence your assessment? Are there unresolved concerns?
3.  **Provide a Confidence Score:** Assign a confidence score between 0 and 100, where 0 is very low confidence (significant issues) and 100 is very high confidence (flawless, well-tested).
4.  **Justify the Score:** Briefly explain the reasoning behind the score, highlighting strengths and weaknesses.
5.  **Suggest Actionable Improvements (if score < 90):** If the confidence score is below 90, suggest concrete actions to improve the commit's quality or associated testing.

**Output Format:**
```markdown
Confidence Score: [0-100]
Justification: [Brief explanation of the score, referencing code quality, completeness, test implications, and review comments.]
Actionable Improvements:
- [Suggestion 1]
- [Suggestion 2]
- ... (Only if score is < 90, each suggestion on a new line prefixed with '- ')
"""


PR_ANALYSIS_PROMPT = """
**Role:** You are an expert software engineer, a meticulous code reviewer, and a release manager. Your task is to evaluate a GitHub Pull Request (PR) based on its overall quality, completeness, adherence to the stated goal, and release readiness.

**Input Pull Request Details:**
* **PR Title:** {pr_title}
* **PR Description:**
    ```
    {pr_description}
    ```
* **Aggregated Commit Information (Messages & Summarized Diffs):**
    ```
    {aggregated_commits_info}
    ```
* **All PR Review Comments:**
    ```
    {all_pr_review_comments}
    ```
* **All General PR Comments:**
    ```
    {all_pr_general_comments}
    ```
* **Specific Instructions for Java Code:** When assessing code quality within the aggregated diffs, pay close attention to common Java patterns. Look for proper error handling (try-catch, throws clauses), resource management (closing streams, connections), null-pointer safety, code readability, adherence to standard Java naming conventions, and the general complexity of the changes. Evaluate if the change is atomic and follows good commit practices.

**Task:**
1.  **Assess Overall Quality & Completeness:**
    * Does the PR's content (commits, diffs) align with and fulfill the PR's title and description?
    * Are the changes well-structured and easy to understand?
    * Are there any obvious omissions or areas needing further work based on the changes?
2.  **Address Review & General Comments:**
    * Have all critical review comments been addressed or acknowledged?
    * Do general comments indicate any outstanding issues or concerns?
3.  **Infer Test Coverage:**
    * Based on the changes, does this PR likely introduce new features or modify existing logic that would require new or updated unit/integration tests?
    * Does the PR or its comments mention testing efforts?
4.  **Provide a Release Readiness Score:** Assign a score between 0 and 100, where:
    * 0-29: Major issues, not ready for review or merge.
    * 30-59: Significant concerns, needs substantial rework.
    * 60-79: Minor issues, but generally acceptable with some refinement.
    * 80-94: High quality, likely ready for merge after minor tweaks or final review.
    * 95-100: Excellent, ready for immediate merge.
5.  **Justify the Score:** Explain your reasoning, referencing specific aspects of the PR, commits, or comments.
6.  **Suggest Actionable Improvements (if score < 90):** Provide concrete, actionable steps to improve the PR's quality or readiness.

**Output Format:**
```markdown
Release Readiness Score: [0-100]
Justification: [Brief explanation of the score, referencing PR goal alignment, code quality, test implications, and how comments were addressed.]
Actionable Improvements:
- [Suggestion 1]
- [Suggestion 2]
- ... (Only if score is < 90, each suggestion on a new line prefixed with '- ')
"""


MILESTONE_ANALYSIS_PROMPT = """
**Role:** You are a senior release manager and an experienced software quality assurance lead. Your primary responsibility is to assess the overall readiness of a software release based on the activity within a specific GitHub milestone.

**Input Milestone Details:**
* **Milestone Title:** {milestone_title}
* **Aggregated Issues and Pull Request Data:**
    ```
    {aggregated_milestone_data}
    ```

**Task:**
1.  **Evaluate Overall Release Readiness:**
    * Synthesize the information from all issues and their associated Pull Requests.
    * Identify any recurring patterns of low scores, unaddressed comments, or common issues across multiple PRs/commits.
    * Assess if all critical issues linked to the milestone appear to be resolved via associated PRs.
    * Note the overall quality trend indicated by the individual commit confidence scores and PR readiness scores.
2.  **Highlight Key Risks and Concerns:**
    * Are there any PRs with particularly low readiness scores that need urgent attention?
    * Are there any issues that seem unresolved or lack associated PRs?
    * Are there any significant gaps in testing based on the LLM's inferences from PRs?
3.  **Provide a Final Release Confidence Score:** Assign a single score between 0 and 100 for the entire milestone, indicating how confident you are in releasing the software at this point.
    * 0-29: Extremely high risk, release blocked.
    * 30-59: Significant risks, major blockers, needs substantial work.
    * 60-79: Moderate risks, some blockers, release possible with caveats or urgent fixes.
    * 80-94: Low risks, minor issues, likely ready for release after final checks.
    * 95-100: Very high confidence, release ready.
4.  **Justify the Score:** Explain your reasoning, providing a summary of the milestone's overall health and major contributing factors (positive and negative).
5.  **Provide Actionable Improvements:** List the most critical 3-5 actions required to improve the milestone's release readiness or to ensure a smooth release.

**Output Format:**
```markdown
Release Confidence Score: [0-100]
Justification: [Comprehensive justification for the overall milestone score. This section MUST NOT contain the Actionable Improvements list.]

Actionable Improvements:
- [Recommendation 1]
- [Recommendation 2]
- ... (Each recommendation on a new line prefixed with '- ')
"""