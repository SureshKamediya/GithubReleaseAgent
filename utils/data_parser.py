import re
import json
import os

def parse_llm_commit_analysis(llm_output_text):
    # ... (Keep this function as it is) ...
    """
    Parses the markdown output from the LLM's commit analysis into a structured dictionary.
    """
    parsed_data = {
        "confidence_score": None,
        "justification": "",
        "actionable_improvements": []
    }

    # Extract Confidence Score
    score_match = re.search(r"Confidence Score: (\d+)", llm_output_text)
    if score_match:
        parsed_data["confidence_score"] = int(score_match.group(1))

    # Extract Justification
    justification_match = re.search(r"Justification: (.*?)(?=Actionable Improvements:|\Z)", llm_output_text, re.DOTALL)
    if justification_match:
        parsed_data["justification"] = justification_match.group(1).strip()

    # Extract Suggestions for Improvement
    suggestions_match = re.search(r"Actionable Improvements:\s*(- .*)", llm_output_text, re.DOTALL)
    if suggestions_match:
        suggestions_raw = suggestions_match.group(1)
        suggestions_list = [
            line.strip()[2:].strip()
            for line in suggestions_raw.split('\n')
            if line.strip().startswith('- ')
        ]
        parsed_data["actionable_improvements"] = suggestions_list

    return parsed_data


def parse_llm_pr_analysis(llm_output_text):
    """
    Parses the markdown output from the LLM's PR analysis into a structured dictionary.
    """
    parsed_data = {
        "release_readiness_score": None,
        "justification": "",
        "actionable_improvements": []
    }

    # Extract Release Readiness Score
    score_match = re.search(r"Release Readiness Score: (\d+)", llm_output_text)
    if score_match:
        parsed_data["release_readiness_score"] = int(score_match.group(1))

    # Extract Justification
    justification_match = re.search(r"Justification: (.*?)(?=Actionable Improvements:|\Z)", llm_output_text, re.DOTALL)
    if justification_match:
        parsed_data["justification"] = justification_match.group(1).strip()

    # Extract Actionable Improvements
    improvements_match = re.search(r"Actionable Improvements:\s*(- .*)", llm_output_text, re.DOTALL)
    if improvements_match:
        improvements_raw = improvements_match.group(1)
        improvements_list = [
            line.strip()[2:].strip() # Remove '- ' prefix and trim whitespace
            for line in improvements_raw.split('\n')
            if line.strip().startswith('- ')
        ]
        parsed_data["actionable_improvements"] = improvements_list

    return parsed_data


def parse_llm_milestone_analysis(llm_output_text):
    """
    Parses the markdown output from the LLM's milestone analysis into a structured dictionary.
    """
    parsed_data = {
        "release_confidence_score": None,
        "justification": "",
        "actionable_improvements": []
    }

    # Extract Release Confidence Score
    score_match = re.search(r"Release Confidence Score: (\d+)", llm_output_text)
    if score_match:
        parsed_data["release_confidence_score"] = int(score_match.group(1))

    # Extract Justification: Match everything from "Justification:" up to "Actionable Improvements:" or end of string
    # This regex is non-greedy (.*?) and uses a positive lookahead to stop before "Actionable Improvements:"
    justification_match = re.search(r"Justification: (.*?)(?=\n\s*Actionable Improvements:|\Z)", llm_output_text, re.DOTALL)
    if justification_match:
        parsed_data["justification"] = justification_match.group(1).strip()
    else:
        # Fallback if "Actionable Improvements" section is missing, take everything after "Justification:"
        justification_match_fallback = re.search(r"Justification: (.*)", llm_output_text, re.DOTALL)
        if justification_match_fallback:
            parsed_data["justification"] = justification_match_fallback.group(1).strip()


    # Extract Actionable Improvements: Ensure it explicitly looks for the header
    improvements_match = re.search(r"Actionable Improvements:\s*(.*?)(?=\n[A-Z]|\Z)", llm_output_text, re.DOTALL) # Match until next section starting with a capital letter or end
    if improvements_match:
        improvements_raw = improvements_match.group(1)
        improvements_list = [
            line.strip()[2:].strip() # Remove '- ' prefix and trim whitespace
            for line in improvements_raw.split('\n')
            if line.strip().startswith('- ')
        ]
        parsed_data["actionable_improvements"] = improvements_list
    else:
        # Fallback for when the LLM embeds improvements in justification (less likely with new prompt)
        # We need to *remove* them from justification if they were included.
        justification_text = parsed_data["justification"]
        temp_improvements_match = re.search(r"Actionable Improvements:\s*(.*)", justification_text, re.DOTALL)
        if temp_improvements_match:
            temp_improvements_raw = temp_improvements_match.group(1)
            temp_improvements_list = [
                line.strip()[2:].strip()
                for line in temp_improvements_raw.split('\n')
                if line.strip().startswith('- ')
            ]
            parsed_data["actionable_improvements"].extend(temp_improvements_list)
            # Remove the improvements from the justification string itself
            parsed_data["justification"] = justification_text.replace(f"Actionable Improvements:\n{temp_improvements_raw}", "").strip()


    return parsed_data


def save_analysis_to_json(data, filename="analysis_report.json", output_dir="reports"):
    """
    Saves the aggregated analysis data to a JSON file.
    Ensures the output directory exists.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    filepath = os.path.join(output_dir, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    print(f"Analysis report saved to {filepath}")