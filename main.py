from github_client.client import GitHubClient
from llm_agent.analysis import analyze_commit_with_llm, analyze_pr_with_llm, analyze_milestone_with_llm
from utils.data_parser import parse_llm_commit_analysis, parse_llm_pr_analysis, parse_llm_milestone_analysis, save_analysis_to_json
from utils.report_generator import generate_console_report # Will use this after milestone analysis is done
import os
import re
from datetime import datetime

def main():
    print("Starting GitHub Release Agent...")
    try:
        github_client = GitHubClient()
        
        milestone_to_test = os.getenv("TEST_MILESTONE_TITLE", "Sprint-1") 
        # Check if the milestone exists. If not, don't proceed with fetching issues
        milestone = None
        for m in github_client.repo.get_milestones(state='open'):
            if m.title == milestone_to_test:
                milestone = m
                break
        
        if not milestone:
            print(f"Milestone '{milestone_to_test}' not found or is closed. Exiting.")
            return # Exit if milestone not found

        issues = github_client.get_issues_for_milestone(milestone_to_test)
        
        milestone_analysis_results = {
            "milestone_title": milestone_to_test,
            "issues": {},
            "llm_milestone_analysis": {}
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
                    "comments": [],
                    "associated_prs": {}
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
                            "description": pr.body,
                            "commits": [],
                            "reviews": [],
                            "comments": [],
                            "llm_pr_analysis": {}
                        }
                        
                        print(f"  --- Processing Associated PR: #{pr.number}: {pr.title} ---")
                        print(f"    PR URL: {pr.html_url}")

                        # `get_commits_for_pull_request` now returns a list of dictionaries
                        commits = github_client.get_commits_for_pull_request(pr) 
                        current_pr_reviews_added = set() 
                        
                        # Loop through the dictionaries directly
                        for commit_dict in commits: # Renamed variable to avoid confusion
                            # Access commit data using dictionary keys
                            commit_info = {
                                "sha": commit_dict["sha"],
                                "message": commit_dict["message"],
                                "author": commit_dict["author"],
                                "date": commit_dict["date"],
                                "diff": commit_dict["diff"], # This now correctly holds the diff
                                "llm_analysis": {}
                            }
                            
                            print(f"      Commit: {commit_info['sha'][:7]} - {commit_info['message'].splitlines()[0]}")
                            
                            pr_reviews = github_client.get_reviews_for_pull_request(pr)
                            commit_review_comments = []
                            for review in pr_reviews:
                                if review.body:
                                    commit_review_comments.append(f"Review by {review.user.login} ({review.state}): {review.body}")
                                    review_tuple = (review.user.login, review.state, review.body)
                                    if review_tuple not in current_pr_reviews_added:
                                        pr_data["reviews"].append({
                                            "user": review.user.login,
                                            "state": review.state,
                                            "body": review.body
                                        })
                                        current_pr_reviews_added.add(review_tuple)

                            relevant_review_text = "\n".join(commit_review_comments) if commit_review_comments else "No specific review comments provided for this commit."

                            print(f"      Calling LLM for commit {commit_info['sha'][:7]} analysis...")
                            llm_output_raw_commit = analyze_commit_with_llm(
                                commit_info["message"],
                                commit_info["diff"],
                                relevant_review_text
                            )
                            parsed_llm_data_commit = parse_llm_commit_analysis(llm_output_raw_commit)
                            # Standardize key here:
                            if "actionable_improvements" in parsed_llm_data_commit:
                                parsed_llm_data_commit["actionable_improvements"] = parsed_llm_data_commit.pop("actionable_improvements")
                            commit_info["llm_analysis"] = parsed_llm_data_commit
                            
                            pr_data["commits"].append(commit_info)

                        pr_general_comments = github_client.get_comments_for_pull_request(pr)
                        for comment in pr_general_comments:
                            print(f"      PR Comment by {comment.user.login}: {comment.body[:50]}...")
                            pr_data["comments"].append({
                                "user": comment.user.login,
                                "body": comment.body
                            })

                        print(f"  Calling LLM for PR #{pr.number} overall analysis...")
                        llm_output_raw_pr = analyze_pr_with_llm(
                            pr.title,
                            pr.body,
                            pr_data["commits"],
                            pr_data["reviews"],
                            pr_data["comments"]
                        )
                        parsed_llm_data_pr = parse_llm_pr_analysis(llm_output_raw_pr)
                        pr_data["llm_pr_analysis"] = parsed_llm_data_pr
                        
                        issue_data["associated_prs"][pr.number] = pr_data

                else:
                    print(f"  No explicit Pull Requests found linked to Issue #{issue.number} via search or comments.")
                
                milestone_analysis_results["issues"][issue.number] = issue_data
            
            print(f"\nCalling LLM for Milestone '{milestone_to_test}' overall analysis...")
            llm_output_raw_milestone = analyze_milestone_with_llm(
                milestone_to_test,
                milestone_analysis_results["issues"]
            )
            print(f"LLM Milestone Analysis Result:\n{llm_output_raw_milestone}")

            parsed_llm_data_milestone = parse_llm_milestone_analysis(llm_output_raw_milestone)
            # Standardize key here:
            if "actionable_improvements" in parsed_llm_data_milestone:
                parsed_llm_data_milestone["actionable_improvements"] = parsed_llm_data_milestone.pop("actionable_improvements")
            milestone_analysis_results["llm_milestone_analysis"] = parsed_llm_data_milestone


            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_filename = f"milestone_{milestone_to_test.replace(' ', '_')}_analysis_{timestamp}.json"
            save_analysis_to_json(milestone_analysis_results, report_filename)

            # --- Generate and print console report ---
            console_report = generate_console_report(milestone_analysis_results)
            print("\n" + "="*80)
            print("                GENERATED RELEASE READINESS REPORT")
            print("="*80)
            print(console_report)
            print("="*80)


        else:
            print("No issues found for the specified milestone.")

    except ValueError as e:
        print(f"Configuration Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()