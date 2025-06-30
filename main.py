from github_client.client import GitHubClient
from llm_agent.analysis import analyze_commit_with_llm # Import the analysis function
import os
import re

def main():
    print("Starting GitHub Release Agent...")
    try:
        github_client = GitHubClient()

        milestone_to_test = os.getenv("TEST_MILESTONE_TITLE", "Sprint-1") 
        issues = github_client.get_issues_for_milestone(milestone_to_test)

        if issues:
            print("\nProcessing fetched issues:")
            for issue in issues:
                print(f"\n--- Processing Issue #{issue.number}: {issue.title} ---")

                issue_comments = github_client.get_issue_comments(issue.number)
                for comment in issue_comments:
                    print(f"    Issue Comment by {comment.user.login}: {comment.body[:50]}...")

                issue_associated_prs = []
                processed_pr_numbers = set()

                # ... (Existing logic for finding associated PRs from comments)
                for comment in issue_comments:
                    pr_url_match = re.search(r'https://github\.com/[^/]+/[^/]+/pull/(\d+)', comment.body)
                    if pr_url_match:
                        pr_number_from_comment = int(pr_url_match.group(1))
                        if pr_number_from_comment not in processed_pr_numbers:
                            pr_from_comment = github_client.get_pull_request_details(pr_number_from_comment)
                            if pr_from_comment:
                                issue_associated_prs.append(pr_from_comment)
                                processed_pr_numbers.add(pr_number_from_comment)

                search_found_prs = github_client.get_pull_requests_referencing_issue(issue.number)
                for pr in search_found_prs:
                    if pr.number not in processed_pr_numbers:
                        issue_associated_prs.append(pr)
                        processed_pr_numbers.add(pr.number)

                if issue_associated_prs:
                    for pr in issue_associated_prs:
                        print(f"  --- Processing Associated PR: #{pr.number} - {pr.title} ---")
                        print(f"    PR URL: {pr.html_url}")

                        # Fetch Commits for the PR and send to LLM
                        commits = github_client.get_commits_for_pull_request(pr)
                        for commit in commits:
                            print(f"      Commit: {commit.sha[:7]} - {commit.commit.message.splitlines()[0]}")

                            # Fetch the actual diff for the commit
                            # For PyGithub, commit.patch provides the diff, but raw_data also contains 'patch'
                            commit_diff = commit.raw_data.get('patch', 'No diff available.')

                            # Gather relevant review comments for THIS specific commit (this part needs refinement later)
                            # For now, we'll just pass a placeholder. Realistically, linking review comments to specific commits is complex.
                            # A simpler approach for V1: pass ALL review comments for the PR to the commit analysis.
                            pr_reviews = github_client.get_reviews_for_pull_request(pr)
                            commit_review_comments = []
                            for review in pr_reviews:
                                # This will get *all* comments from a review. You'd need more logic to filter by commit.
                                # For simplicity, let's just collect review bodies for now.
                                if review.body:
                                    commit_review_comments.append(f"Review by {review.user.login} ({review.state}): {review.body}")
                            # Join all review comments relevant to the PR (not just specific to the commit)
                            relevant_review_text = "\n".join(commit_review_comments) if commit_review_comments else "No specific review comments provided for this commit."

                            print(f"      Calling LLM for commit {commit.sha[:7]} analysis...")
                            llm_output = analyze_commit_with_llm(
                                commit.commit.message, 
                                commit_diff, 
                                relevant_review_text
                            )
                            print(f"      LLM Analysis Result:\n{llm_output}")

                        # (Reviews and General Comments for PR are still fetched but not yet used in LLM analysis)
                        reviews = github_client.get_reviews_for_pull_request(pr)
                        # ... (print reviews)
                        pr_comments = github_client.get_comments_for_pull_request(pr)
                        # ... (print comments)
                else:
                    print(f"  No explicit Pull Requests found linked to Issue #{issue.number} via search or comments.")
        else:
            print("No issues found for the specified milestone.")

    except ValueError as e:
        print(f"Configuration Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()