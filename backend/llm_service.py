import json
import requests
from config.settings import MODEL, MAX_RETRIES
from backend.pdf_handler import chunk_text
import streamlit as st
from groq import Groq
# import google.generativeai as genai
from prompts.loader import (
    build_summary_prompt,
    build_fusion_prompt,
    build_qcm_prompt,
    build_explain_prompt
)

# genai.configure(api_key=st.secrets["MODEL_API_KEY"])
# model = genai.GenerativeModel(MODEL)

client = Groq(api_key=st.secrets["MODEL_API_KEY"])
model = MODEL
import time

def call_llm(prompt: str) -> str:

    for attempt in range(MAX_RETRIES):
        try:
            # response = model.generate_content(prompt)
            # return response.text.strip()
            response = client.chat.completions.create(
                            model=model,
                            messages=[
                                {"role": "user", "content": prompt}
                            ],
                            max_tokens=4000
                        )
            return response.choices[0].message.content.strip()
        except Exception as e:
            error_msg = str(e)

            if "429" in error_msg:
                if "daily" in error_msg.lower():
                    raise RuntimeError(
                        "Groq rate limit reached after several retries. "
                        "Please wait a moment and try again."
                    )

                if attempt < MAX_RETRIES - 1:
                    wait_seconds = 60 * (attempt + 1)  # 60s, 120s, 180s...
                    print(f"Rate limit hit. Waiting {wait_seconds}s before retry {attempt + 2}/{MAX_RETRIES}...")
                    time.sleep(wait_seconds)
                    continue
                else:
                    raise RuntimeError(
                        f"LLM rate limit reached. Original error: {error_msg}"
                    )

            elif attempt == MAX_RETRIES - 1:
                raise TimeoutError(
                    f"LLM service unavailable after {MAX_RETRIES} attempts. ({error_msg})"
                )

    return ""

@st.cache_data
# def generate_summary(text: str, langue: str) -> str:
#     """
#     Full pipeline : chunk → summarize each chunk → fuse all summaries.
#     """
#     chunks = chunk_text(text)
#     nb_chunks = len(chunks)

#     # Step 1 : Summarize each chunk
#     partial_summaries = []
#     for i, chunk in enumerate(chunks):
#         time.sleep(15)
#         prompt  = build_summary_prompt(chunk, langue)
#         summary = call_llm(prompt)
#         if summary:
#             partial_summaries.append(summary) , nb_chunks

#     if not partial_summaries:
#         raise ValueError("No summary could be generated from this document.")

#     # Step 2 : Fuse all partial summaries
#     if len(partial_summaries) == 1:
#         return partial_summaries[0]
    
#     time.sleep(5)

#     fusion_prompt = build_fusion_prompt(partial_summaries, langue)
#     return call_llm(fusion_prompt) , nb_chunks

def generate_summary(text: str, langue: str):

    chunks = chunk_text(text)
    partial_summaries = []

    for i, chunk in enumerate(chunks):
        prompt  = build_summary_prompt(chunk, langue)
        summary = call_llm(prompt)
        if summary:
            partial_summaries.append(summary)

        if i < len(chunks) - 1:
            time.sleep(5)

    if not partial_summaries:
        raise ValueError("No summary could be generated.")

    if len(partial_summaries) == 1:
        print("here")
        return partial_summaries[0]  , []

    fusion_prompt = build_fusion_prompt(partial_summaries, langue)
    time.sleep(5)
    raw_output = call_llm(fusion_prompt)

    final_summary, key_concepts = parse_summary_and_concepts(raw_output)
    return final_summary , key_concepts

def parse_summary_and_concepts(raw_output: str):
    import re

    key_concepts  = []
    final_summary = raw_output.strip()


    # Normalisation : remove the asterisks around KEY_CONCEPTS
    normalized = re.sub(r"\*{1,2}(KEY_CONCEPTS)\*{1,2}", r"\1", raw_output, flags=re.IGNORECASE)


    # Strategy 1 : KEY_CONCEPTS = { ... }
    pattern = r"KEY_CONCEPTS\s*[\n\s]*=\s*\{([^}]*)\}"
    match   = re.search(pattern, normalized, re.DOTALL | re.IGNORECASE)

    if match:
        concepts_block = match.group(1)
        raw_concepts   = re.split(r"[,\n]", concepts_block)
        key_concepts   = [
            c.strip().lstrip("-•* ").rstrip(",").strip()
            for c in raw_concepts
            if c.strip().lstrip("-•* ").rstrip(",").strip()
            and len(c.strip().lstrip("-•* ").rstrip(",").strip()) > 1
        ]

        orig_match = re.search(r"\*{0,2}KEY_CONCEPTS\*{0,2}", raw_output, re.IGNORECASE)
        if orig_match:
            final_summary = raw_output[:orig_match.start()].strip()

        return final_summary, key_concepts


    # Strategy 2 : **KEY_CONCEPTS** followed by bullet points

    pattern2 = r"KEY_CONCEPTS\s*[=:\n]*([\s\S]*?)(?=\n[A-Z#*]|\Z)"
    match2   = re.search(pattern2, normalized, re.DOTALL | re.IGNORECASE)

    if match2:
        concepts_block = match2.group(1)
        raw_concepts   = re.split(r"[,\n]", concepts_block)
        key_concepts   = [
            c.strip().lstrip("-•* ").rstrip(",").strip()
            for c in raw_concepts
            if c.strip().lstrip("-•* ").rstrip(",").strip()
            and len(c.strip().lstrip("-•* ").rstrip(",").strip()) > 1
        ]

        orig_match = re.search(r"\*{0,2}KEY_CONCEPTS\*{0,2}", raw_output, re.IGNORECASE)
        if orig_match:
            final_summary = raw_output[:orig_match.start()].strip()

        return final_summary, key_concepts


    # Strategy 4 : Nothing found

    print("WARNING : KEY_CONCEPTS not found in LLM output.")
    return final_summary, []

def generate_explanation(concept: str, langue: str) -> str:
    #Re-explains a concept the student did not understand.
    prompt = build_explain_prompt(concept, langue)
    return call_llm(prompt)

def generate_qcm(resume_final: str, n_questions: int , key_concepts , langue: str):
    prompt = build_qcm_prompt(resume_final, n_questions , key_concepts , langue)

    raw_response = call_llm(prompt)

    questions = parse_qcm_response(raw_response)

    return questions

def parse_qcm_response(raw_response: str) -> list:


    # Clean common LLM artifacts before parsing
    cleaned = raw_response.strip()
    cleaned = cleaned.replace("```json", "").replace("```", "")
    cleaned = cleaned.strip()

    try:
        questions = json.loads(cleaned)

        # Validate structure : must be a list
        if not isinstance(questions, list):
            raise ValueError("Response is not a JSON array.")

        # Validate each question has required fields
        validated = []
        for q in questions:
            if all(k in q for k in ["question", "options", "correct_answer", "explanation"]):
                validated.append(q)

        if not validated:
            raise ValueError("No valid questions found in response.")

        return validated

    except (json.JSONDecodeError, ValueError) as e:
        # Erreur 4 : malformed JSON → retry once
        raise ValueError(
            f"Could not parse QCM response from LLM. ({e})\n"
            f"Raw response was: {raw_response[:200]}..."
        )