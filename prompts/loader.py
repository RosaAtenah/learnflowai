import os

PROMPTS_DIR = os.path.dirname(__file__)

def load_prompt(filename: str) -> str:
    """
    Loads a prompt template from the prompts/ directory.
    """
    path = os.path.join(PROMPTS_DIR, filename)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def build_summary_prompt(chunk_text: str, langue: str) -> str:
    template = load_prompt("summary_prompt.txt")
    return template.replace("{chunk_text}", chunk_text)\
                   .replace("{langue}", langue)


def build_fusion_prompt(partial_summaries: list, langue: str) -> str:
    template = load_prompt("fusion_prompt.txt")
    summaries_text = "\n\n---\n\n".join(partial_summaries)
    return template.replace("{partial_summaries}", summaries_text)\
                   .replace("{langue}", langue)


def build_qcm_prompt(resume_final: str, n_questions: int, langue: str) -> str:
    template = load_prompt("qcm_prompt.txt")
    return template.replace("{resume_final}", resume_final)\
                   .replace("{n_questions}", str(n_questions))\
                   .replace("{langue}", langue)


def build_explain_prompt(concept: str, langue: str) -> str:
    template = load_prompt("explain_prompt.txt")
    return template.replace("{concept}", concept)\
                   .replace("{langue}", langue)