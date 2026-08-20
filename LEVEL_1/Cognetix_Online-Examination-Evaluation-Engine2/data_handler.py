import json


def load_questions():
    try:
        with open("questions.json", "r") as file:
            data = json.load(file)
            return data["questions"]

    except FileNotFoundError:
        print("Error: questions.json not found.")
        return []

    except json.JSONDecodeError:
        print("Error: Invalid JSON format in questions.json.")
        return []


def load_results():
    try:
        with open("results.json", "r") as file:
            return json.load(file)

    except FileNotFoundError:
        return []

    except json.JSONDecodeError:
        return []


def is_unique_id(candidate_id):
    results = load_results()

    for result in results:
        if result["candidate_id"] == candidate_id:
            return False

    return True


def save_result(result):
    results = load_results()

    results.append(result)

    with open("results.json", "w") as file:
        json.dump(results, file, indent=4)