def evaluate_exam(candidate_name, candidate_id, questions, responses):
    total_questions = len(questions)
    correct_answers = 0
    wrong_answers = 0
    marks_per_question = 1
    negative_mark = 0

    for question in questions:
        question_id = question["id"]
        correct_answer = question["answer"]

        if responses[question_id] == correct_answer:
            correct_answers += 1
        else:
            wrong_answers += 1

    obtained_marks = (correct_answers * marks_per_question) - (wrong_answers * negative_mark)
    maximum_marks = total_questions * marks_per_question
    percentage = (obtained_marks / maximum_marks) * 100

    if percentage >= 40:
        status = "Pass"
    else:
        status = "Fail"

    result = {
        "candidate_name": candidate_name,
        "candidate_id": candidate_id,
        "correct_answers": correct_answers,
        "wrong_answers": wrong_answers,
        "obtained_marks": obtained_marks,
        "maximum_marks": maximum_marks,
        "percentage": round(percentage, 2),
        "status": status
    }

    return result