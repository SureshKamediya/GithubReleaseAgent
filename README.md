# GitHub Release Agent (AI-Powered Code Review and Release Assistant)

## Project Overview

The GitHub Release Agent is an intelligent assistant designed to streamline the software release process by leveraging Google's Gemini LLM. It automates the analysis of code changes, pull requests, and associated issues for a given GitHub milestone, providing valuable insights, quality scores, and potential improvements. This helps release managers and development teams ensure code quality and confidence before a release.

### Key Features:

* **GitHub Integration:** Connects to your GitHub repositories to fetch issues, pull requests, commits, and comments.
* **Milestone-Based Analysis:** Focuses on the scope of a specific GitHub milestone (e.g., a sprint, release candidate).
* **AI-Powered Commit Analysis:** Utilizes the Gemini LLM to analyze individual commit messages and code diffs, providing:
    * A **Confidence Score** (0-100) indicating the quality and completeness of the changes.
    * A **Justification** for the score, highlighting strengths and weaknesses.
    * **Suggestions for Improvement** (if the score is below 90).
* **Review Insights:** Incorporates GitHub Pull Request review comments into the LLM's analysis for a more holistic view.
* **Structured Output:** Generates machine-readable analysis results for further processing or reporting.

## Workflow

The agent follows these steps to generate its insights:

1.  **Connect to GitHub:** Authenticates using a Personal Access Token to access the specified repository.
2.  **Fetch Milestone Issues:** Retrieves all issues associated with a designated GitHub milestone.
3.  **Identify Linked Pull Requests (PRs):** For each issue, it attempts to find corresponding PRs by:
    * Parsing issue comments for direct PR links.
    * Searching PR descriptions/titles that reference the issue number.
4.  **Extract PR Details:** For each identified PR, it fetches:
    * All commits within the PR.
    * All code reviews and their comments.
    * General comments on the PR.
5.  **LLM Analysis:** For each commit found within the PRs:
    * The commit message, code diff, and relevant PR review comments are sent to the Gemini LLM.
    * The LLM generates a confidence score, justification, and improvement suggestions based on the provided prompt.
6.  **Future Steps (Planned):**
    * Aggregating commit scores into a PR-level or milestone-level quality report.
    * Generating summaries of issues, PRs, and overall release readiness.
    * Outputting reports into the `reports/` directory.

## Setup and Installation

Follow these steps to set up and run the project on your local machine.

### Prerequisites

* Python 3.9+
* [Git Bash](https://git-scm.com/downloads) (or any compatible terminal for Windows users)
* A GitHub Personal Access Token with `repo` scope.
* A Google Gemini API Key.

### 1. Clone the Repository

If you haven't already, clone this repository to your local machine:

```bash
git clone [https://github.com/SureshKamediya/GithubReleaseAgent.git](https://github.com/SureshKamediya/GithubReleaseAgent.git)
cd GithubReleaseAgent
```

### 2. Setup environment variables

It's highly recommended to use a virtual environment to manage project dependencies.

# Create the virtual environment

```bash
python -m venv .venv
```

# Activate the virtual environment
# On Windows (Git Bash):
```bash
source ./.venv/Scripts/activate
```
# On Linux/macOS:
# source ./.venv/bin/activate

### 3. Install Dependencies

Install the necessary Python libraries. First, ensure you have the requirements.txt file (it should be in the repository after cloning). If you need to regenerate it (e.g., after installing new packages manually), you can run pip freeze > requirements.txt while your virtual environment is active.

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a file named .env in the root directory of your project (where main.py is located). This file will store your sensitive API keys and configuration details.

.env file content:

```env
# GitHub Token: Generate a Personal Access Token from GitHub settings (Developer settings -> Personal access tokens (classic))
# Grant 'repo' scope for full repository access.
GITHUB_TOKEN="YOUR_GITHUB_PERSONAL_ACCESS_TOKEN"

# GitHub Repository Details
# Your GitHub Username or Organization Name (e.g., "SureshKamediya")
GITHUB_REPO_OWNER="SureshKamediya"
# The name of the repository you want to analyze (e.g., "wfa")
GITHUB_REPO_NAME="wfa"

# Google Gemini API Key: Obtain from Google AI Studio ([https://aistudio.google.com/](https://aistudio.google.com/))
GOOGLE_API_KEY="YOUR_GOOGLE_GEMINI_API_KEY"

# Specify a milestone title for testing purposes. Ensure this milestone exists in your GitHub repo.
TEST_MILESTONE_TITLE="Sprint-1"
```


### 4. Run the application

```bash
python main.py
```

### Project Structure

```bash
GithubReleaseAgent/
├── .venv/                         # Python Virtual Environment (Ignored by Git)
├── .env                           # Environment variables (Ignored by Git)
├── .gitignore                     # Specifies files/directories to ignore
├── requirements.txt               # Project dependencies
├── main.py                        # Main entry point of the application
├── github_client/                 # Package for GitHub API interactions
│   └── __init__.py                # Marks as a Python package
│   └── client.py                  # Handles GitHub API calls (issues, PRs, commits, comments)
├── llm_agent/                     # Package for LLM interactions and logic
│   └── __init__.py                # Marks as a Python package
│   └── analysis.py                # Contains logic for calling the LLM and processing responses
│   └── prompts.py                 # Stores LLM prompt templates
├── utils/                         # For common utility functions (e.g., data parsing, formatting)
│   └── __init__.py
│   └── data_parser.py             # (Placeholder for future data parsing logic)
├── reports/                       # Directory to store generated reports/output (Ignored by Git)
└── README.md                      # This file
```