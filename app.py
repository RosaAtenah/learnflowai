import streamlit as st
from backend.llm_service import generate_explanation, generate_qcm, generate_summary
from backend.pdf_handler import verify_pdf_validity, extract_text_from_pdf
from config.settings import DEFAULT_EASINESS, ZONE1_PAGES , BASE_MIN_QUESTIONS, MAX_QUESTIONS
from backend.srs_engine import update_card

def show_results_dashboard():

    results  = st.session_state["qcm_results"]
    n_total  = len(results)
    n_correct = sum(1 for r in results if r["is_correct"])

    st.divider()
    st.subheader("📊 Session Results")

    # Score
    score_pct = round((n_correct / n_total) * 100)
    st.metric("Score", f"{n_correct} / {n_total}", f"{score_pct}%")

    # Results table
    st.markdown("### Review Table")

    for i, r in enumerate(results):

        # SRS label
        srs_labels = {
            0: "🔴 Again",
            2: "🟠 Hard",
            4: "🟢 Good",
            5: "🔵 Easy"
        }
        srs_label = srs_labels.get(r["srs_quality"], "?")

        # Next review label
        if r["interval"] == 1:
            next_review_label = "Tomorrow"
        else:
            next_review_label = f"In {r['interval']} days"

        st.markdown(
            f"**Q{i+1}** — {r['question'][:60]}...  \n"
            f"{'✅' if r['is_correct'] else '❌'} {srs_label} "
            f"→ Next review : {next_review_label}"
        )

    st.divider()

    # Tip based on results
    n_to_review = sum(1 for r in results if r["interval"] == 1)
    if n_to_review > 0:
        st.warning(
            f"💡 {n_to_review} concept(s) to review tomorrow. "
            f"Come back to consolidate your knowledge!"
        )
    else:
        st.success(
            "🎉 Great session! All concepts are well understood."
        )

    # Restart button
    if st.button("🔄 Start a new session"):
        keys_to_clear = [
            "questions", "qcm_results", "current_question_index",
            "answer_submitted", "generate_qcm", "final_summary",
            "extracted_text", "ready_for_qcm", "n_questions"
        ]
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()


st.title("AI Study Assistant")

uploaded_file = st.file_uploader("Upload your course (PDF)", type=["pdf"])

if uploaded_file is not None:

    # Step 1 : Validate the PDF
    with st.spinner("Checking your file..."):
        result = verify_pdf_validity(uploaded_file)

    # Step 2 : Handle blocking errors → stop immediately
    if not result["valid"]:
        st.error(f"{result['error']}")
        st.stop()

    # Step 3 : Show non-blocking warnings
    if result["warning"]:
        st.warning(f"{result['warning']}")

    if result["suggestion"]:
        st.info(f"{result['suggestion']}")

    # Step 4 : Page selection based on action zone
    nb_pages = result["nb_pages"]
    st.success(f"File accepted — {nb_pages} page(s) detected.")

    st.subheader("Page selection")

    # Build options list based on action zone
    if result["action"] == "normal":
        page_options = ["All pages", "First N pages", "Specific range"]
        default_index = 0
    else:
        page_options = ["First N pages", "Specific range"]
        default_index = 0    # pre-select "First N pages"

    mode = st.radio(
        "Which pages do you want to process?",
        page_options,
        index=default_index
    )

    page_range = None
    max_pages  = None

    if mode == "First N pages":
        max_pages = st.slider(
            "Number of pages to process",
            min_value=1,
            max_value=nb_pages,
            value=min(ZONE1_PAGES, nb_pages)
        )

    elif mode == "Specific range":
        col1, col2 = st.columns(2)
        with col1:
            start = st.number_input(
                "From page",
                min_value=1,
                max_value=nb_pages,
                value=1
            )
        with col2:
            end = st.number_input(
                "To page",
                min_value=int(start),
                max_value=nb_pages,
                value=min(int(start) + ZONE1_PAGES - 1, nb_pages)
            )
        page_range = (int(start), int(end))

    # Step 5 : Language selection
    st.subheader("Summary language")

    langue = st.selectbox(
        "Choose the language for the summary and questions",
        ["French", "English"],
        index=0
    )

    # Step 6 : Launch processing
    if st.button("Analyze the course"):

        with st.spinner("Extracting text from PDF..."):
            text = extract_text_from_pdf(
                uploaded_file,
                max_pages=max_pages,
                page_range=page_range
            )

        if not text.strip():
            st.error("No text could be extracted from the selected pages.")
            st.stop()

        st.success(f"Text extracted successfully ({len(text.split())} words).")

        st.session_state["extracted_text"] = text
        st.session_state["langue"]          = langue
        st.session_state["nb_pages"]        = nb_pages


    # Step 7 : Generate summary (after text extraction)

    if "extracted_text" in st.session_state:

        text   = st.session_state["extracted_text"]
        langue = st.session_state["langue"]

        if "final_summary" not in st.session_state:
            with st.spinner("Generating summary... this may take a moment."):
                try:
                    summary , nb_chunks = generate_summary(text, langue)
                    st.session_state["final_summary"] = summary
                    st.session_state["nb_chunks"] = nb_chunks

                except TimeoutError as e:
                    st.error(f"❌ {e}")
                    st.stop()
                except ValueError as e:
                    st.error(f"❌ {e}")
                    st.stop()

        
        # Step 8 : Display summary + student feedback
        
        st.subheader("📄 Course Summary")
        st.markdown(st.session_state["final_summary"])

        st.divider()
        st.subheader("💬 Did you understand this summary?")

        col1, col2 = st.columns(2)

        with col1:
            understood = st.button("✅ Yes, I understood")

        with col2:
            not_understood = st.button("❌ No, I need help")

        
        # Path A : Student understood → go to QCM
        
        if understood:
            st.session_state["ready_for_qcm"] = True
            st.success("Great! Let's test your knowledge.")
            st.rerun()

        
        # Path B : Student did not understand → ask which concept
        
        if not_understood:
            st.session_state["needs_explanation"] = True

        if st.session_state.get("needs_explanation"):

            st.subheader("🔍 Which concept is unclear?")

            concept = st.text_input(
                "Type the concept or sentence you did not understand"
            )

            if st.button("💡 Re-explain this concept"):
                if concept.strip():
                    with st.spinner("Generating explanation..."):
                        try:
                            explanation = generate_explanation(concept, langue)
                            st.session_state["last_explanation"] = explanation
                        except TimeoutError as e:
                            st.error(f"❌ {e}")

            if "last_explanation" in st.session_state:
                st.info(st.session_state["last_explanation"])

                st.divider()
                st.subheader("Is it clearer now?")

                col3, col4 = st.columns(2)

                with col3:
                    if st.button("✅ Yes, continue to QCM"):
                        st.session_state["ready_for_qcm"]      = True
                        st.session_state["needs_explanation"]   = False
                        st.rerun()

                with col4:
                    if st.button("🔄 Ask about another concept"):
                        del st.session_state["last_explanation"]
                        st.rerun()

    # Step 9 : Generate and display QCM
    if st.session_state.get("generate_qcm"):
        nb_chunks = st.session_state.get("nb_chunks", 3)

        default_questions = max(
            BASE_MIN_QUESTIONS,
            min(nb_chunks * 2, MAX_QUESTIONS)
        )

        n_questions = st.slider(
            "How many questions do you want?",
            min_value=1,
            max_value=MAX_QUESTIONS,
            value=default_questions
        )

        if "questions" not in st.session_state:
            with st.spinner("Generating quiz..."):
                try:
                    questions = generate_qcm(
                        st.session_state["final_summary"],
                        n_questions,
                        st.session_state["langue"]
                    )
                    st.session_state["questions"] = questions

                except ValueError as e:
                    st.error(f"❌ {e}")
                    st.stop()

    # ----------------------------------------------------------
    # Step 9 : Display QCM
    # ----------------------------------------------------------
    if "questions" in st.session_state and st.session_state.get("generate_qcm"):

        questions = st.session_state["questions"]

        st.divider()
        st.subheader("📝 Quiz")

        # Initialize session state for QCM tracking
        if "current_question_index" not in st.session_state:
            st.session_state["current_question_index"] = 0

        if "qcm_results" not in st.session_state:
            st.session_state["qcm_results"] = []

        if "answer_submitted" not in st.session_state:
            st.session_state["answer_submitted"] = False

        current_index = st.session_state["current_question_index"]

        # ----------------------------------------------------------
        # All questions answered → show results dashboard
        # ----------------------------------------------------------
        if current_index >= len(questions):
            show_results_dashboard()

        else:
            # ----------------------------------------------------------
            # Display current question
            # ----------------------------------------------------------
            q = questions[current_index]

            st.markdown(
                f"**Question {current_index + 1} / {len(questions)}**"
            )
            st.progress((current_index) / len(questions))

            st.markdown(f"### {q['question']}")

            # Radio button for answer selection
            options = q["options"]
            choices = [f"{k}) {v}" for k, v in options.items()]

            selected = st.radio(
                "Choose your answer:",
                choices,
                key=f"radio_{current_index}",
                index=None      # no pre-selection
            )

            # ----------------------------------------------------------
            # Submit answer button
            # ----------------------------------------------------------
            if not st.session_state["answer_submitted"]:
                if st.button("✅ Submit answer", key=f"submit_{current_index}"):
                    if selected is None:
                        st.warning("⚠️ Please select an answer before submitting.")
                    else:
                        selected_letter = selected[0]   # extract "A", "B", "C" or "D"
                        is_correct      = selected_letter == q["correct_answer"]

                        st.session_state["answer_submitted"]  = True
                        st.session_state["last_selected"]     = selected_letter
                        st.session_state["last_is_correct"]   = is_correct
                        st.rerun()

            # ----------------------------------------------------------
            # Show feedback after submission
            # ----------------------------------------------------------
            if st.session_state.get("answer_submitted"):

                selected_letter = st.session_state["last_selected"]
                is_correct      = st.session_state["last_is_correct"]

                if is_correct:
                    st.success("✅ Correct!")
                else:
                    st.error(
                        f"❌ Wrong answer. "
                        f"Correct answer: **{q['correct_answer']}**) "
                        f"{q['options'][q['correct_answer']]}"
                    )

                st.info(f"💬 **Explanation:** {q['explanation']}")

                # ----------------------------------------------------------
                # SRS buttons — only shown after answer submitted
                # ----------------------------------------------------------
                st.markdown("**How did you find this question?**")

                col1, col2, col3, col4 = st.columns(4)

                srs_choice = None

                with col1:
                    if st.button("🔴 Again\n\nForgotten", key=f"again_{current_index}"):
                        srs_choice = 0
                with col2:
                    if st.button("🟠 Hard\n\nHesitated", key=f"hard_{current_index}"):
                        srs_choice = 2
                with col3:
                    if st.button("🟢 Good\n\nKnew it", key=f"good_{current_index}"):
                        srs_choice = 4
                with col4:
                    if st.button("🔵 Easy\n\nObvious", key=f"easy_{current_index}"):
                        srs_choice = 5

                if srs_choice is not None:

                    # ----------------------------------------------------------
                    # Apply SM-2 algorithm
                    # ----------------------------------------------------------

                    # Get or initialize card state for this question
                    card_key = f"card_{current_index}"
                    if card_key not in st.session_state:
                        st.session_state[card_key] = {
                            "interval"   : 1,
                            "easiness"   : DEFAULT_EASINESS,
                            "repetitions": 0
                        }

                    updated_card = update_card(
                        st.session_state[card_key],
                        srs_choice
                    )
                    st.session_state[card_key] = updated_card

                    # Save result for dashboard
                    st.session_state["qcm_results"].append({
                        "question"    : q["question"],
                        "selected"    : selected_letter,
                        "correct"     : q["correct_answer"],
                        "is_correct"  : is_correct,
                        "srs_quality" : srs_choice,
                        "interval"    : updated_card["interval"],
                        "next_review" : updated_card["next_review"]
                    })

                    # Move to next question
                    st.session_state["current_question_index"] += 1
                    st.session_state["answer_submitted"]        = False
                    del st.session_state["last_selected"]
                    del st.session_state["last_is_correct"]
                    st.rerun()
