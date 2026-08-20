from data_handler import load_questions, save_result, is_unique_id
from validation import validate_responses
from evaluator import evaluate_exam

def main():
    questions = load_questions()
    if not questions:
        return

    print("\n========== ONLINE EXAMINATION ==========\n")

    while True:
        candidate_name = input("Enter Candidate Name: ").strip()

        if candidate_name == "":
            print(" Name cannot be empty.")
        elif candidate_name.replace(" ", "").isalpha():
            break
        else:
            print(" Enter a valid name (letters only).")

    while True:
        candidate_id = input("Enter Candidate ID: ").strip()

        if candidate_id == "":
            print("Candidate ID cannot be empty.")
        elif not candidate_id.isdigit():
            print(" Candidate ID must contain only numbers.")
        elif not is_unique_id(candidate_id):
            print(" Candidate ID already exists. Please enter a unique ID.")
        else:
            break

    responses = {}

    print("\nAnswer using A, B, C or D\n")

    for question in questions:
        print(f"\nQuestion {question['id']}")
        print(question["question"])

        for option, value in question["options"].items():
            print(f"{option}. {value}")

        while True:
            answer = input("Enter Your Answer (A/B/C/D): ").strip().upper()

            if answer in ["A", "B", "C", "D"]:
                responses[question["id"]] = answer
                break
            else:
                print(" Please enter a valid option (A, B, C, or D).")

    if not validate_responses(questions, responses):
        return

    result = evaluate_exam(
        candidate_name,
        candidate_id,
        questions,
        responses
    )

    save_result(result)

    print("\n========== RESULT ==========")
    print(f"Candidate Name   : {result['candidate_name']}")
    print(f"Candidate ID     : {result['candidate_id']}")
    print(f"Correct Answers  : {result['correct_answers']}")
    print(f"Wrong Answers    : {result['wrong_answers']}")
    print(f"Obtained Marks   : {result['obtained_marks']}")
    print(f"Maximum Marks    : {result['maximum_marks']}")
    print(f"Percentage       : {result['percentage']}%")
    print(f"Status           : {result['status']}")
    print("============================")


if __name__ == "__main__":
    main()