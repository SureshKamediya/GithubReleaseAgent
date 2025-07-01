import re
import json
import os


def parse_llm_commit_analysis(llm_output_text):
    """
    Parses the markdown output from the LLM's commit analysis into a structured dictionary.
    """
    parsed_data = {
        "confidence_score": None,
        "justification": "",
        "suggestions_for_improvement": []
    }

    # Extract Confidence Score
    score_match = re.search(r"Confidence Score: (\d+)", llm_output_text)
    if score_match:
        parsed_data["confidence_score"] = int(score_match.group(1))

    # Extract Justification
    # This assumes Justification is a single block of text after "Justification:"
    # and before "Suggestions for Improvement:" or the end of the string.
    justification_match = re.search(r"Justification: (.*?)(?=Suggestions for Improvement:|\Z)", llm_output_text, re.DOTALL)
    if justification_match:
        parsed_data["justification"] = justification_match.group(1).strip()

    # Extract Suggestions for Improvement
    suggestions_match = re.search(r"Suggestions for Improvement:\s*(- .*)", llm_output_text, re.DOTALL)
    if suggestions_match:
        suggestions_raw = suggestions_match.group(1)
        # Split by lines and filter for non-empty lines that start with '- '
        suggestions_list = [
            line.strip()[2:].strip() # Remove '- ' prefix and trim whitespace
            for line in suggestions_raw.split('\n')
            if line.strip().startswith('- ')
        ]
        parsed_data["suggestions_for_improvement"] = suggestions_list

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