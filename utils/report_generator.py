def generate_console_report(analysis_data):
    """
    Generates a human-readable console report from the aggregated analysis data.
    """
    report_lines = []
    
    milestone_title = analysis_data.get("milestone_title", "N/A Milestone")
    report_lines.append(f"--- Release Readiness Report for Milestone: {milestone_title} ---")
    report_lines.append("-" * (len(milestone_title) + 40))

    # Add Milestone-level LLM Analysis at the top of the report
    milestone_llm_analysis = analysis_data.get("llm_milestone_analysis", {})
    if milestone_llm_analysis:
        report_lines.append("\n## Overall Milestone Release Confidence")
        report_lines.append(f"   Release Confidence Score: {milestone_llm_analysis.get('release_confidence_score', 'N/A')}/100")
        report_lines.append("   Justification:")
        # Indent the justification properly
        justification_lines = milestone_llm_analysis.get('justification', 'No justification provided.').splitlines()
        for line in justification_lines:
            report_lines.append(f"     {line.strip()}")
        
        recommendations = milestone_llm_analysis.get("actionable_improvements", [])
        if recommendations:
            report_lines.append("    Actionable Improvements:")
            for rec in recommendations:
                report_lines.append(f"     - {rec}")
        report_lines.append("\n" + "=" * 50 + "\n") # Separator after milestone summary
    else:
        report_lines.append("\nNo overall milestone LLM analysis available.")

    issues = analysis_data.get("issues", {})
    if not issues:
        report_lines.append("\nNo issues found for this milestone.")
        return "\n".join(report_lines)

    for issue_number, issue_data in issues.items():
        report_lines.append(f"\n## Issue #{issue_data.get('number')}: {issue_data.get('title')}")
        report_lines.append(f"   Status: {issue_data.get('state').capitalize()}")
        report_lines.append(f"   URL: {issue_data.get('url')}")
        
        comments = issue_data.get("comments", [])
        if comments:
            report_lines.append("   Issue Comments:")
            for comment in comments:
                report_lines.append(f"     - {comment.get('user')}: {comment.get('body', '')[:100]}{'...' if len(comment.get('body', '')) > 100 else ''}") # Truncate long comments
        
        associated_prs = issue_data.get("associated_prs", {})
        if not associated_prs:
            report_lines.append("   No associated Pull Requests.")
        else:
            report_lines.append("\n   Associated Pull Requests:")
            for pr_number, pr_data in associated_prs.items():
                report_lines.append(f"   --- PR #{pr_data.get('number')}: {pr_data.get('title')} ---")
                report_lines.append(f"     URL: {pr_data.get('url')}")
                report_lines.append(f"     Status: {pr_data.get('state').capitalize()}")
                report_lines.append(f"     Author: {pr_data.get('user')}")
                # Properly truncate description and handle missing description
                description = pr_data.get('description', 'No description provided.')
                report_lines.append(f"     Description: {description.splitlines()[0][:100]}{'...' if len(description.splitlines()[0]) > 100 else ''}")


                # PR-Level LLM Analysis
                pr_llm_analysis = pr_data.get("llm_pr_analysis", {})
                if pr_llm_analysis:
                    report_lines.append("\n     --- PR LLM Analysis ---")
                    score = pr_llm_analysis.get("release_readiness_score")
                    report_lines.append(f"     Release Readiness Score: {score}/100")
                    report_lines.append(f"     Justification:\n       {pr_llm_analysis.get('justification', '').replace('\n', '\n       ')}")
                    
                    improvements = pr_llm_analysis.get("actionable_improvements", [])
                    if improvements:
                        report_lines.append("     Actionable Improvements:")
                        for imp in improvements:
                            report_lines.append(f"       - {imp}")
                else:
                    report_lines.append("\n     No PR-level LLM analysis available.")

                # Commit-Level LLM Analysis (summarized)
                commits = pr_data.get("commits", [])
                if commits:
                    report_lines.append("\n     --- Commit-Level Analysis Summary ---")
                    for commit in commits:
                        report_lines.append(f"     Commit: {commit.get('sha', '')[:7]} - {commit.get('message', '').splitlines()[0]}")
                        commit_llm_analysis = commit.get("llm_analysis", {})
                        if commit_llm_analysis:
                            report_lines.append(f"       Confidence Score: {commit_llm_analysis.get('confidence_score', 'N/A')}")
                            
                            # Clean and truncate justification
                            justification = commit_llm_analysis.get('justification', 'No justification.').replace('\n', ' ').strip()
                            report_lines.append(f"       Justification Summary: {justification[:150]}{'...' if len(justification) > 150 else ''}")
                            
                            suggestions = commit_llm_analysis.get("actionable_improvements", [])
                            if suggestions:
                                # Join and truncate suggestions more robustly
                                joined_suggestions = "; ".join(suggestions)
                                report_lines.append(f"       Actionable Improvements: {joined_suggestions[:150]}{'...' if len(joined_suggestions) > 150 else ''}")
                        else:
                            report_lines.append("       No commit-level LLM analysis.")
                else:
                    report_lines.append("\n     No commits found for this PR.")
                
                reviews = pr_data.get("reviews", [])
                if reviews:
                    report_lines.append("\n     Reviews:")
                    for review in reviews:
                        report_lines.append(f"       - {review.get('user')} ({review.get('state')}): {review.get('body', '')[:100]}{'...' if len(review.get('body', '')) > 100 else ''}")
                
                general_comments = pr_data.get("comments", [])
                if general_comments:
                    report_lines.append("\n     General PR Comments:")
                    for comment in general_comments:
                        report_lines.append(f"       - {comment.get('user')}: {comment.get('body', '')[:100]}{'...' if len(comment.get('body', '')) > 100 else ''}")
                
                report_lines.append("\n" + "-" * 50 + "\n") # Separator for PRs
    
    report_lines.append("\n--- End of Report ---")
    return "\n".join(report_lines)