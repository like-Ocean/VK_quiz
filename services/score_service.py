from models.question import Question


def check_answer(question: Question, selected_option_ids: list[str]) -> bool:
    correct_ids = {str(o.id) for o in question.answer_options if o.is_correct}
    return set(selected_option_ids) == correct_ids


def calculate_score(question: Question, is_correct: bool) -> int:
    return question.points if is_correct else 0
