def validate_responses(questions, responses):
    valid_options = ["A", "B", "C", "D"]

    if len(questions) != len(responses):
        print("Error: Question count does not match the responses.")
        return False

    for question in questions:
        question_id = question["id"]

        if question_id not in responses:
            print(f"Error: Missing response for Question {question_id}.")
            return False

        answer = responses[question_id]

        if not isinstance(answer, str):
            print(f"Error: Invalid data type for Question {question_id}.")
            return False

        answer = answer.upper()

        if answer == "":
            print(f"Error: Question {question_id} is unanswered.")
            return False

        if answer not in valid_options:
            print(f"Error: Invalid answer '{answer}' for Question {question_id}.")
            return False

        responses[question_id] = answer

    return True