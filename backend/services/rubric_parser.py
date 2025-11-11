import mysql.connector
import json

def fetch_rubric(rubric_name="Situated_Learning_rubric", as_text=False):
    """
    Fetches rubric from dissertation_data.rubrics and returns either:
    - Parsed Python list of dimensions (if as_text=False)
    - A flattened text representation for prompts (if as_text=True)
    """

    # Connect to MySQL (edit credentials accordingly)
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="your_password",
        database="dissertation_data"
    )
    cursor = conn.cursor()

    # Fetch the rubric row
    cursor.execute("SELECT dimensions FROM rubrics WHERE name = %s", (rubric_name,))
    result = cursor.fetchone()

    if not result:
        return None  # Rubric not found

    dimensions_json = json.loads(result[0])  # Parse JSON array

    if not as_text:
        return dimensions_json  # Return raw structured data

    # Otherwise, format it nicely for inclusion in a prompt
    formatted_text = []
    for dim in dimensions_json:
        formatted_text.append(f"### {dim['name']}")
        formatted_text.append(f"Description: {dim.get('criteria_explanation', '')}")
        formatted_text.append("Criteria:")
        for crit, desc in dim["criteria_output"].items():
            formatted_text.append(f"  - {crit}: {desc}")
        formatted_text.append("Score Descriptors:")
        for score, info in dim["score_explanation"].items():
            formatted_text.append(f"  - {score}: {info['Description']}")
        formatted_text.append("")  # New line spacing

    return "\n".join(formatted_text)

# Example usage:
if __name__ == "__main__":
    rubric_text = fetch_rubric(as_text=True)
    print(rubric_text)
