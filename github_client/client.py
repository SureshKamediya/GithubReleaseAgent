import os
from github import Github
from dotenv import load_dotenv

class GitHubClient:
    def __init__(self):
        load_dotenv()
        self.github_token = os.getenv("GITHUB_TOKEN")
        self.repo_name = os.getenv("GITHUB_REPO_NAME")
        self.owner_name = os.getenv("GITHUB_REPO_OWNER")

        if not self.github_token:
            raise ValueError("GITHUB_TOKEN not found in .env file. Please set it.")
        if not self.repo_name or not self.owner_name:
            raise ValueError("GITHUB_REPO_NAME or GITHUB_REPO_OWNER not found in .env file. Please set them.")
        
        self.g = Github(self.github_token)
        try:
            self.repo = self.g.get_user(self.owner_name).get_repo(self.repo_name)
            print(f"Successfully connected to GitHub repository: {self.owner_name}/{self.repo_name}")
        except Exception as e:
            raise Exception(f"Could not connect to repository: {e}")

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

    def get_issue_comments(self, issue_number):
        issue = self.repo.get_issue(issue_number)
        comments = issue.get_comments()
        print(f"  Fetching comments for Issue #{issue_number}...")
        print(f"  Found {comments.totalCount} comments for Issue #{issue_number}.")
        return list(comments)

    def get_pull_request_details(self, pr_number):
        try:
            pr = self.repo.get_pull(pr_number)
            return pr
        except Exception as e:
            print(f"Warning: Could not fetch PR #{pr_number}. Error: {e}")
            return None

    def get_pull_requests_referencing_issue(self, issue_number):
        # This searches pull requests where the issue number is mentioned in the title or body
        # or where the PR closes the issue.
        query = f"in:title,body {self.owner_name}/{self.repo_name} type:pr {issue_number}"
        # A more direct way for "closing" issues is not directly searchable on the PR level,
        # but mentioning the issue number is a common convention that works with this search.
        search_results = self.g.search_issues(query=query)
        
        prs = []
        for item in search_results:
            if item.pull_request: # Ensure it's actually a pull request
                # Fetch full PR details to get its state and other info
                pr = self.repo.get_pull(item.number)
                prs.append(pr)
        return prs

    def get_reviews_for_pull_request(self, pr):
        reviews = pr.get_reviews()
        print(f"  Fetching reviews for PR #{pr.number}...")
        print(f"  Found {reviews.totalCount} reviews for PR #{pr.number}.")
        return list(reviews)

    def get_commits_for_pull_request(self, pr):
        """
        Fetches commits for a pull request, ensuring the full diff (patch) is available.
        Returns a list of dictionaries, where each dict represents a detailed commit.
        """
        raw_commits = pr.get_commits()
        detailed_commits = []
        print(f"  Fetching commits for PR #{pr.number}...")

        for commit_summary in raw_commits:
            try:
                full_commit = self.repo.get_commit(commit_summary.sha)
                
                diff_content = ""
                # full_commit.files is a list of File objects, each having a .patch attribute
                if full_commit.files:
                    for file_change in full_commit.files:
                        if file_change.patch: # Directly access the .patch attribute
                            # Reconstruct diff header for each file for better readability
                            diff_content += f"--- a/{file_change.previous_filename or file_change.filename}\n"
                            diff_content += f"+++ b/{file_change.filename}\n"
                            diff_content += file_change.patch + "\n"
                
                if not diff_content:
                    diff_content = "No relevant diff available for this commit (e.g., merge commit or no file changes)."

                commit_data = {
                    "sha": full_commit.sha,
                    "message": full_commit.commit.message,
                    "author": full_commit.commit.author.name,
                    "date": full_commit.commit.author.date.isoformat(),
                    "diff": diff_content 
                }
                detailed_commits.append(commit_data)
            except Exception as e:
                print(f"Warning: Could not fetch detailed commit {commit_summary.sha} for PR #{pr.number}. Error: {e}")
                detailed_commits.append({
                    "sha": commit_summary.sha,
                    "message": commit_summary.commit.message,
                    "author": commit_summary.commit.author.name,
                    "date": commit_summary.commit.author.date.isoformat(),
                    "diff": "Error fetching detailed diff: " + str(e) # Include error message for debugging
                })
        print(f"  Found {len(detailed_commits)} commits for PR #{pr.number}.")
        return detailed_commits
    
    def get_comments_for_pull_request(self, pr):
        """
        Fetches all general comments (not review comments) on a Pull Request object.
        """
        print(f"  Fetching general comments for PR #{pr.number}...")
        comments = list(pr.get_comments()) # These are comments on the PR itself
        print(f"  Found {len(comments)} general comments for PR #{pr.number}.")
        return comments


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
