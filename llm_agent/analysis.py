import google.generativeai as genai
import os
from dotenv import load_dotenv
from llm_agent.prompts import COMMIT_ANALYSIS_PROMPT
from llm_agent.prompts import PR_ANALYSIS_PROMPT
from llm_agent.prompts import MILESTONE_ANALYSIS_PROMPT

# Load environment variables
load_dotenv()

# Configure the Gemini API key
GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in .env file. Please set it.")

genai.configure(api_key=GEMINI_API_KEY)

# Initialize the Generative Model
model = genai.GenerativeModel('gemini-1.5-flash-latest') # Or 'gemini-1.5-flash-latest' if you prefer a faster/cheaper option

def analyze_commit_with_llm(commit_message, commit_diff, review_comments=""):
    """
    Sends commit details to the LLM for analysis and confidence scoring.
    """
    # Format the imported prompt with the actual data
    prompt = COMMIT_ANALYSIS_PROMPT.format(
        commit_message=commit_message,
        commit_diff=commit_diff,
        review_comments=review_comments
    )
    
    # Make the API call
    try:
        response = model.generate_content(prompt)
        # Ensure the response has text content
        if response.candidates and response.candidates[0].content.parts:
            return response.candidates[0].content.parts[0].text
        else:
            print("Warning: LLM response had no text content.")
            return "Confidence Score: 50\nJustification: LLM could not generate a proper response.\nActionable Improvements: Re-evaluate input or prompt."
    except Exception as e:
        print(f"Error calling LLM for commit analysis: {e}")
        return f"Confidence Score: 0\nJustification: LLM API call failed due to error: {e}\nActionable Improvements: Check API key, network, or rate limits."
    


def analyze_pr_with_llm(pr_title, pr_body, commits_data, reviews_data, comments_data):
    """
    Sends aggregated PR details to the LLM for overall PR analysis and release readiness scoring.
    """
    # Aggregate commit information
    aggregated_commits_info = ""
    for commit in commits_data:
        aggregated_commits_info += f"Commit SHA: {commit['sha'][:7]}\n"
        aggregated_commits_info += f"Message: {commit['message'].splitlines()[0]}\n" # First line of message
        # Only include diff if it's not the placeholder "No diff available."
        if commit['diff'] and commit['diff'] != 'No diff available.':
            # For brevity, consider truncating long diffs for PR-level analysis if context window becomes an issue
            aggregated_commits_info += f"Diff Snippet (first 200 chars):\n```\n{commit['diff'][:200]}\n```\n"
        aggregated_commits_info += f"LLM Confidence Score: {commit['llm_analysis'].get('confidence_score', 'N/A')}\n"
        aggregated_commits_info += "---\n"
    if not aggregated_commits_info:
        aggregated_commits_info = "No commits found or processed for this PR."

    # Aggregate review comments
    all_pr_review_comments = ""
    for review in reviews_data:
        all_pr_review_comments += f"Review by {review['user']} ({review['state']}): {review['body']}\n"
    if not all_pr_review_comments:
        all_pr_review_comments = "No review comments."

    # Aggregate general PR comments
    all_pr_general_comments = ""
    for comment in comments_data:
        all_pr_general_comments += f"Comment by {comment['user']}: {comment['body']}\n"
    if not all_pr_general_comments:
        all_pr_general_comments = "No general comments."

    prompt = PR_ANALYSIS_PROMPT.format(
        pr_title=pr_title,
        pr_description=pr_body if pr_body else "No description provided.",
        aggregated_commits_info=aggregated_commits_info,
        all_pr_review_comments=all_pr_review_comments,
        all_pr_general_comments=all_pr_general_comments
    )

    try:
        response = model.generate_content(prompt)
        if response.candidates and response.candidates[0].content.parts:
            return response.candidates[0].content.parts[0].text
        else:
            print("Warning: LLM (PR) response had no text content.")
            return "Release Readiness Score: 50\nJustification: LLM could not generate a proper response.\nActionable Improvements: Re-evaluate input or prompt."
    except Exception as e:
        print(f"Error calling LLM for PR analysis: {e}")
        return f"Release Readiness Score: 0\nJustification: LLM API call failed due to error: {e}\nActionable Improvements: Check API key, network, or rate limits."



def analyze_milestone_with_llm(milestone_title, issues_data):
    """
    Sends aggregated milestone data (issues, PRs, and their analyses) to the LLM
    for overall milestone release confidence scoring.
    """
    aggregated_milestone_data = f"Milestone: {milestone_title}\n\n"
    
    if not issues_data:
        aggregated_milestone_data += "No issues or associated PRs found for this milestone."
    else:
        for issue_number, issue in issues_data.items():
            aggregated_milestone_data += f"Issue #{issue['number']}: {issue['title']} (Status: {issue['state']})\n"
            if issue['comments']:
                aggregated_milestone_data += "  Issue Comments:\n"
                for comment in issue['comments']:
                    aggregated_milestone_data += f"    - {comment['user']}: {comment['body'][:100]}...\n" # Truncate for brevity
            
            prs = issue.get('associated_prs', {})
            if prs:
                aggregated_milestone_data += "  Associated Pull Requests:\n"
                for pr_number, pr in prs.items():
                    aggregated_milestone_data += f"    PR #{pr['number']}: {pr['title']} (Status: {pr['state']})\n"
                    aggregated_milestone_data += f"      PR Description: {pr['description'][:100]}...\n" # Truncate
                    
                    if pr.get('llm_pr_analysis'):
                        pr_score = pr['llm_pr_analysis'].get('release_readiness_score', 'N/A')
                        pr_justification = pr['llm_pr_analysis'].get('justification', '')
                        aggregated_milestone_data += f"      Overall PR Readiness Score: {pr_score}\n"
                        aggregated_milestone_data += f"      PR Justification: {pr_justification[:150]}...\n" # Truncate
                        if pr['llm_pr_analysis'].get('actionable_improvements'):
                             aggregated_milestone_data += f"      PR Improvements: {'; '.join(pr['llm_pr_analysis']['actionable_improvements'][:2])}...\n"
                    
                    if pr.get('commits'):
                        aggregated_milestone_data += "      Commits:\n"
                        for commit in pr['commits']:
                            commit_score = commit['llm_analysis'].get('confidence_score', 'N/A')
                            aggregated_milestone_data += f"        Commit {commit['sha'][:7]}: {commit['message'].splitlines()[0]} (Score: {commit_score})\n"
                    
                    if pr.get('reviews'):
                        aggregated_milestone_data += "      Reviews:\n"
                        for review in pr['reviews']:
                            aggregated_milestone_data += f"        - {review['user']} ({review['state']}): {review['body'][:100]}...\n"
                    
                    aggregated_milestone_data += "\n" # Blank line for PR separation
            else:
                aggregated_milestone_data += "  No PRs linked.\n\n"

    prompt = MILESTONE_ANALYSIS_PROMPT.format(
        milestone_title=milestone_title,
        aggregated_milestone_data=aggregated_milestone_data
    )

    try:
        response = model.generate_content(prompt)
        if response.candidates and response.candidates[0].content.parts:
            return response.candidates[0].content.parts[0].text
        else:
            print("Warning: LLM (Milestone) response had no text content.")
            return "Release Confidence Score: 50\nJustification: LLM could not generate a proper response.\nActionable Improvements: Re-evaluate input or prompt."
    except Exception as e:
        print(f"Error calling LLM for milestone analysis: {e}")
        return f"Release Confidence Score: 0\nJustification: LLM API call failed due to error: {e}\nActionable Improvements: Check API key, network, or rate limits."
