from github_client.client import GitHubClient
from llm_agent.analysis import analyze_commit_with_llm
from utils.data_parser import parse_llm_commit_analysis, save_analysis_to_json # Import new functions
import os
import re
from datetime import datetime

def main():
    print("Starting GitHub Release Agent...")
    try:
        github_client = GitHubClient()
        
        milestone_to_test = os.getenv("TEST_MILESTONE_TITLE", "Sprint-1") 
        issues = github_client.get_issues_for_milestone(milestone_to_test)
        
        # Dictionary to store all aggregated analysis results
        # Structure: {milestone_title: {issue_number: {issue_details, pr_data: {pr_number: {pr_details, commits: [{commit_data, llm_analysis}]}}}}}
        milestone_analysis_results = {
            "milestone_title": milestone_to_test,
            "issues": {}
        }

        if issues:
            print("\nProcessing fetched issues:")
            for issue in issues:
                print(f"\n--- Processing Issue #{issue.number}: {issue.title} ---")
                
                issue_data = {
                    "number": issue.number,
                    "title": issue.title,
                    "url": issue.html_url,
                    "state": issue.state,
                    "comments": [], # Store actual comment bodies
                    "associated_prs": {} # Store PR data linked to this issue
                }
                
                issue_comments = github_client.get_issue_comments(issue.number)
                for comment in issue_comments:
                    print(f"    Issue Comment by {comment.user.login}: {comment.body[:50]}...")
                    issue_data["comments"].append({
                        "user": comment.user.login,
                        "body": comment.body
                    })

                issue_associated_prs = []
                processed_pr_numbers = set()

                # ... (Existing logic for finding associated PRs from comments and search)
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
                        pr_data = {
                            "number": pr.number,
                            "title": pr.title,
                            "url": pr.html_url,
                            "state": pr.state,
                            "user": pr.user.login,
                            "commits": [], # Store commit data with LLM analysis
                            "reviews": [], # Store review data
                            "comments": [] # Store general PR comments
                        }
                        
                        print(f"  --- Processing Associated PR: #{pr.number} - {pr.title} ---")
                        print(f"    PR URL: {pr.html_url}")

                        # Fetch Commits for the PR and send to LLM
                        commits = github_client.get_commits_for_pull_request(pr)
                        for commit in commits:
                            commit_info = {
                                "sha": commit.sha,
                                "message": commit.commit.message,
                                "author": commit.commit.author.name,
                                "date": commit.commit.author.date.isoformat(), # ISO format for datetime objects
                                "diff": None, # Will store the diff string
                                "llm_analysis": {} # Store parsed LLM results
                            }
                            
                            print(f"      Commit: {commit.sha[:7]} - {commit.commit.message.splitlines()[0]}")
                            
                            commit_diff = commit.raw_data.get('patch', 'No diff available.')
                            commit_info["diff"] = commit_diff # Store diff in data

                            pr_reviews = github_client.get_reviews_for_pull_request(pr)
                            commit_review_comments = []
                            for review in pr_reviews:
                                if review.body:
                                    commit_review_comments.append(f"Review by {review.user.login} ({review.state}): {review.body}")
                                    pr_data["reviews"].append({ # Store review data in PR
                                        "user": review.user.login,
                                        "state": review.state,
                                        "body": review.body
                                    })

                            relevant_review_text = "\n".join(commit_review_comments) if commit_review_comments else "No specific review comments provided for this commit."

                            print(f"      Calling LLM for commit {commit.sha[:7]} analysis...")
                            llm_output_raw = analyze_commit_with_llm(
                                commit.commit.message,
                                commit_diff,
                                relevant_review_text
                            )
                            print(f"      LLM Analysis Result:\n{llm_output_raw}")

                            # Parse the LLM output
                            parsed_llm_data = parse_llm_commit_analysis(llm_output_raw)
                            commit_info["llm_analysis"] = parsed_llm_data
                            
                            pr_data["commits"].append(commit_info)

                        # Fetch General Comments for the PR
                        pr_comments = github_client.get_comments_for_pull_request(pr)
                        for comment in pr_comments:
                            print(f"      PR Comment by {comment.user.login}: {comment.body[:50]}...")
                            pr_data["comments"].append({
                                "user": comment.user.login,
                                "body": comment.body
                            })
                        
                        issue_data["associated_prs"][pr.number] = pr_data

                else:
                    print(f"  No explicit Pull Requests found linked to Issue #{issue.number} via search or comments.")
                
                milestone_analysis_results["issues"][issue.number] = issue_data
            
            # Save the final aggregated results to a JSON file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S") # Import datetime first
            report_filename = f"milestone_{milestone_to_test.replace(' ', '_')}_analysis_{timestamp}.json"
            save_analysis_to_json(milestone_analysis_results, report_filename)


        else:
            print("No issues found for the specified milestone.")

    except ValueError as e:
        print(f"Configuration Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()