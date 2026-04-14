from multi_agent_analyst.eval.loader import load_gold_set, load_question_set


def test_eval_assets_load_successfully():
    question_set = load_question_set("dataset/questions.json")
    gold_set = load_gold_set("dataset/eval_gold.json")

    assert len(question_set.questions) == 10
    assert len(gold_set.expectations) == 10
    assert gold_set.expectations[0].question_id == 1
