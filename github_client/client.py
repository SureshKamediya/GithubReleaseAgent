import os
from dotenv import load_dotenv
from github import Github
import re

# Load environment variables from .env file
load_dotenv()

class GitHubClient:
    def __init__(self):
        self.token = os.getenv("GITHUB_TOKEN")
        self.repo_owner = os.getenv("GITHUB_REPO_OWNER")
        self.repo_name = os.getenv("GITHUB_REPO_NAME")

        if not self.token or not self.repo_owner or not self.repo_name:
            raise ValueError("GITHUB_TOKEN, GITHUB_REPO_OWNER, and GITHUB_REPO_NAME must be set in the .env file.")

        self.g = Github(self.token)
        self.repo = self.g.get_user(self.repo_owner).get_repo(self.repo_name)
        print(f"Successfully connected to GitHub repository: {self.repo.full_name}")

    def get_issues_for_milestone(self, milestone_title):
        print(f"Fetching issues for milestone: {milestone_title}...")
        milestone = None
        for m in self.repo.get_milestones(state='open'):
            if m.title == milestone_title:
                milestone = m
                break
        
        if not milestone:
            print(f"Milestone '{milestone_title}' not found or is closed.")
            return []

        github_issues_paginated = self.repo.get_issues(state='all', milestone=milestone)
        issues = list(github_issues_paginated) 
        print(f"Found {len(issues)} issues for milestone '{milestone_title}'.")
        return issues

    def get_pull_request_details(self, pr_number):
        """Fetches a full Pull Request object by its number."""
        try:
            return self.repo.get_pull(pr_number)
        except Exception as e:
            print(f"  Error fetching PR #{pr_number}: {e}")
            return None

    def get_pull_requests_referencing_issue(self, issue_number, state='all'):
        """
        Searches for Pull Requests that reference a specific issue in their body or title.
        This is a more robust way to find associated PRs than issue.pull_request attribute.
        """
        print(f"  Searching for PRs referencing Issue #{issue_number}...")
        found_prs = []
        # Search for PRs that explicitly mention the issue number
        # GitHub search syntax: `type:pr repo:owner/repo #issue_number`
        query = f"type:pr repo:{self.repo_owner}/{self.repo_name} #{issue_number}"
        
        # Use search_issues to search for pull requests (PRs are a type of issue in the search API)
        # Note: This uses the search API, which has stricter rate limits.
        search_results = self.g.search_issues(query=query, state=state) # state can be 'open', 'closed', 'all'

        for result in search_results:
            # Ensure it's actually a PR and not just an issue with that number mentioned
            if result.pull_request: # This check is to confirm it's a PR object from search
                # We need to get the full PR object from the simple one returned by search
                full_pr = self.repo.get_pull(result.number)
                found_prs.append(full_pr)
        
        print(f"  Found {len(found_prs)} PRs referencing Issue #{issue_number}.")
        return found_prs


    def get_commits_for_pull_request(self, pr):
        """
        Fetches all commits associated with a given Pull Request object.
        """
        print(f"  Fetching commits for PR #{pr.number}...")
        commits = list(pr.get_commits())
        print(f"  Found {len(commits)} commits for PR #{pr.number}.")
        return commits

    def get_reviews_for_pull_request(self, pr):
        """
        Fetches all reviews and their comments for a given Pull Request object.
        """
        print(f"  Fetching reviews for PR #{pr.number}...")
        reviews = list(pr.get_reviews())
        print(f"  Found {len(reviews)} reviews for PR #{pr.number}.")
        return reviews

    def get_comments_for_pull_request(self, pr):
        """
        Fetches all general comments (not review comments) on a Pull Request object.
        """
        print(f"  Fetching general comments for PR #{pr.number}...")
        comments = list(pr.get_comments()) # These are comments on the PR itself
        print(f"  Found {len(comments)} general comments for PR #{pr.number}.")
        return comments

    def get_issue_comments(self, issue_number):
        """
        Fetches all comments on a specific issue.
        """
        issue = self.repo.get_issue(issue_number)
        print(f"  Fetching comments for Issue #{issue_number}...")
        comments = list(issue.get_comments())
        print(f"  Found {len(comments)} comments for Issue #{issue_number}.")
        return comments

# ... (existing if __name__ == "__main__": block - we will modify this next)
if __name__ == "__main__":
    # This block is for testing the client directly
    try:
        client = GitHubClient()
        # It's better to get the milestone title from environment variable or argument
        milestone_title = os.getenv("TEST_MILESTONE_TITLE", "Your Milestone Title") 
        issues = client.get_issues_for_milestone(milestone_title) 

        if issues:
            for issue in issues:
                print(f"- Issue #{issue.number}: {issue.title} (State: {issue.state})")
                if issue.pull_request:
                    print(f"  Associated PR: {issue.pull_request.url}")
        else:
            print(f"No issues found for milestone '{milestone_title}'.")

    except ValueError as e:
        print(f"Configuration Error: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")
