def calculate_score(matched_skills, required_skills, experience):
    """
    Calculate the candidate's score based on:
    - Skill match percentage (70%)
    - Experience bonus (30%)
    """

    # Avoid division by zero
    if len(required_skills) == 0:
        skill_score = 0
    else:
        skill_score = (len(matched_skills) / len(required_skills)) * 70

    # Experience Score (Maximum 30 Marks)
    if experience >= 5:
        experience_score = 30
    elif experience >= 3:
        experience_score = 20
    elif experience >= 1:
        experience_score = 10
    else:
        experience_score = 0

    # Total Score
    total_score = skill_score + experience_score

    return round(total_score, 2)


def rank_candidates(candidates):
    """
    Sort candidates based on score in descending order
    and assign ranking positions.
    """

    # Sort candidates by score (highest to lowest)
    candidates.sort(key=lambda candidate: candidate["Score"], reverse=True)

    # Assign ranks
    for index, candidate in enumerate(candidates, start=1):
        candidate["Rank"] = index

    return candidates

