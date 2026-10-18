import streamlit as st
from groq import Groq
import json
import uuid
import hashlib

API_KEY = st.secrets["groqAPIKey"]

client = Groq(api_key=API_KEY)

def ask_groq(system_prompt, user_prompt, temperature=0.7):
    chat_completion = client.chat.completions.create(
        messages=[
            {"role": "system","content": system_prompt},
            {"role": "user","content": user_prompt}
        ],
        model="openai/gpt-oss-120b",
        temperature=temperature)

    response = chat_completion.choices[0].message.content
    return response

system_prompt = '''
You are a friendly language tutor.
Create beginner-friendly language learning content.
Keep the output clear and practical.
'''

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

if "user_credentials" not in st.session_state:
    st.session_state.user_credentials = {}

if not st.session_state.authenticated:
    st.title("🌏 Language Learning App")
    
    tab_login, tab_signup = st.tabs(["🔐 Log In", "📝 Sign Up"])

    # ---------------------------------------------------------
    # TAB 1: User Login
    # ---------------------------------------------------------
    with tab_login:
        st.subheader("Log In to Your Account")
        with st.form("login_form"):
            user_id_input = st.text_input("User ID", key="login_user_id")
            password_input = st.text_input("Password", type="password", key="login_password")
            login_btn = st.form_submit_button("Log In")

            if login_btn:
                uid = user_id_input.strip()
                pwd = password_input.strip()

                if not uid or not pwd:
                    st.warning("Please enter both User ID and Password.")
                elif uid not in st.session_state.user_credentials:
                    st.info("Account does not exist yet! Please switch to the 'Sign Up' tab to create an account.")
                elif st.session_state.user_credentials[uid] == hash_password(pwd):
                    st.session_state.authenticated = True
                    st.session_state.current_user_id = uid
                    st.success("Logged in successfully!")
                    st.rerun()
                else:
                    st.error("Incorrect password. Please try again.")

    # ---------------------------------------------------------
    # TAB 2: Sign Up
    # ---------------------------------------------------------
    with tab_signup:
        st.subheader("Create a New Account")
        with st.form("signup_form"):
            new_user_id = st.text_input("Choose User ID", key="signup_user_id")
            new_password = st.text_input("Choose Password", type="password", key="signup_password")
            confirm_password = st.text_input("Confirm Password", type="password", key="signup_confirm")
            signup_btn = st.form_submit_button("Sign Up")

            if signup_btn:
                uid = new_user_id.strip()
                pwd = new_password.strip()
                confirm_pwd = confirm_password.strip()

                if not uid or not pwd or not confirm_pwd:
                    st.warning("Please complete all fields.")
                elif pwd != confirm_pwd:
                    st.error("Passwords do not match. Please try again.")
                elif uid in st.session_state.user_credentials:
                    st.info("An account with this User ID already exists! Please switch to the 'Log In' tab.")
                else:
                    # Save hashed credentials
                    st.session_state.user_credentials[uid] = hash_password(pwd)
                    st.success("Account created successfully! You can now switch to the 'Log In' tab to log in.")

    st.stop()

st.set_page_config(
    page_title="Language Learning App", page_icon="🌏", layout="wide")

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "current_user_id" not in st.session_state:
    st.session_state.current_user_id = ""

if not st.session_state.authenticated:
    st.title("🔐 User Login")
    with st.form("login_form"):
        user_id_input = st.text_input("User ID")
        password_input = st.text_input("Password", type="password")
        login_btn = st.form_submit_button("Log In")
        
        if login_btn:
            if user_id_input.strip() and password_input.strip():
                st.session_state.authenticated = True
                st.session_state.current_user_id = user_id_input.strip()
                st.success("Logged in successfully!")
                st.rerun()
            else:
                st.warning("Please enter both User ID and Password.")
    st.stop()

if "learner_profile" not in st.session_state:
    st.session_state.learner_profile = {}

if "selected_topics" not in st.session_state:
    st.session_state.selected_topics = ""

if "saved_vocab" not in st.session_state:
    st.session_state.saved_vocab = []

if "saved_grammar" not in st.session_state:
    st.session_state.saved_grammar = []

if "vocab_items" not in st.session_state:
    st.session_state.vocab_items = []

if "grammar_outputs" not in st.session_state:
    st.session_state.grammar_outputs = {}

if "messages" not in st.session_state:
    st.session_state.messages = []

if "feedback_report" not in st.session_state:
    st.session_state.feedback_report = {}

if "learning_focus" not in st.session_state:
    st.session_state.learning_focus = []

def generate_vocabulary():
    profile = st.session_state.learner_profile
    topic = st.session_state.selected_topics

    if not profile or not topic:
        return

    target_lang = profile.get("target_language", "English")
    known_lang = profile.get("known_language", "English")
    level = profile.get("target_language_level", "Beginner")

    vocab_prompt = f"""
Generate 10 useful vocabulary words or phrases related to the topic: "{topic}"

The learner is studying {target_lang} at the {level} level.
The learner understands {known_lang}.

For each vocabulary item, provide:
- "word": the vocabulary word or phrase in {target_lang}
- "reading": a pronunciation/reading guide explained in or translated to {known_lang}
- "definition": a clear and simple definition in {known_lang}
- "example_sentence": a natural, beginner-friendly example sentence in {target_lang}

Requirements:
- Generate exactly 10 vocabulary items.
- All words must be relevant to the selected topic.
- Return ONLY valid JSON as an array.
- Do not include Markdown, ```json, or any text outside the JSON array.

JSON format:
[
    {{
        "word": "...",
        "reading": "...",
        "definition": "...",
        "example_sentence": "..."
    }}
]
"""
    response_text = ask_groq(
        system_prompt,
        vocab_prompt,
        temperature=0.4
    ).strip()

    try:
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
            
        vocab_items = json.loads(response_text.strip())
    
        if isinstance(vocab_items, list):
            st.session_state.vocab_items = vocab_items
        else:
            st.error("The AI response is not a list.")
    
    except json.JSONDecodeError:
        st.error("The AI response was not valid JSON.")
        st.code(response_text)
        
st.sidebar.header('NAVIGATION')
st.sidebar.write(f"User: **{st.session_state.current_user_id}**")

page = st.sidebar.radio(
    "Choose a page",
    ["Home",
    "Learner Profile",
    "Learner Dashboard",
    "Vocabulary Practice",
    "Grammar Practice",
    "Conversation Practice"])

if st.sidebar.button("Log Out"):
    st.session_state.authenticated = False
    st.session_state.current_user_id = ""
    st.rerun()

if page == "Home":
    st.title("🌏 Welcome to Language Learning App!")
    st.write("Your personal AI-powered tutor designed to help you master new languages through personalized practice, structured grammar, and interactive conversation.")

    st.divider()

    st.subheader("💡 About This App")
    st.markdown("""
    This app helps you build practical language skills tailored to your personal goals and experience level:
    
    * **Personalized Topics:** Recommended vocabulary and learning topics generated based on your real-world goals.
    * **Vocabulary Practice:** Generate relevant words, view pronunciation guides, and build your saved vocabulary list.
    * **Grammar Practice:** Focus on specific grammar concepts while generating contextual examples mapped to your interest topics.
    * **Conversation Practice:** Chat in real-time with an AI tutor and receive detailed feedback reports on your progress.
    """)

    st.divider()

    st.subheader("🚀 How to Use This App")
    
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        #### 1️⃣ Set Up Your Profile
        * Navigate to **Learner Profile** in the left sidebar.
        * Fill in your purpose for learning, known language, target language, and current level.
        * Click **Save Profile** to generate personalized topic recommendations.

        #### 2️⃣ Practice Vocabulary
        * Go to **Vocabulary Practice**.
        * Select a topic from your profile and click **Generate Vocabulary**.
        * Click **⭐ Save** on words you want to store in your **Saved Vocabulary** tab.
        """)

    with col2:
        st.markdown("""
        #### 3️⃣ Learn Grammar
        * Go to **Grammar Practice**.
        * Enter any grammar rule or concept you want explained.
        * Choose a profile topic for customized example sentences.
        * Save helpful explanations or example sentences to review later.

        #### 4️⃣ Practice Conversation & Track Progress
        * Open **Conversation Practice** to chat with your AI language tutor.
        * Click **Evaluate Dialogue** anytime to get structured feedback on your response strengths and growth areas.
        * Check your **Learner Dashboard** to view your overall progress and milestone achievements!
        """)

elif page == "Learner Profile":
    st.title("Learner Profile")
    st.write("Manage your personal learning settings and preferences.")

    with st.form("learner_profile_form"):
        st.subheader("Edit Profile Information")

        profile = st.session_state.learner_profile
        purpose = st.text_input(
        "Why do you want to learn new language?",)
    
        known_language = st.selectbox(
        "What language do you want to use for learning?",
        ["Japanese", "Spanish", "English", "French", "Korean"])
    
        level_known_language = st.slider(f"What is your current level for {known_language}?" , min_value=0, max_value=100, value=50, step=10)
        
        target_language = st.selectbox(
        "What language do you want to learn?",
        ["Japanese", "Spanish", "English", "French", "Korean"])
        
        level_target_language = st.selectbox(
        "What is your current level?",
        ["Beginner", "Elementary", "Intermediate","Advanced"])
      
        learning_focus = st.multiselect("What do you want to practice?",["Vocabulary","Grammar","Conversation"], ["Vocabulary","Grammar","Conversation"])
    
        submitted = st.form_submit_button("Save Profile")
    
        if submitted:
            if purpose and known_language and level_known_language and target_language and level_target_language:
                topic_generation_prompt = f'''
Generate up to 10 example topics based on the users purpose of learning language:{purpose}

Return in {known_language} within 5 words per example topic.

Rules:
- one topic per line
- no numbering
- no bullet points
- no meanings
- no extra explanation
'''
                raw_topic_list = ask_groq(system_prompt, topic_generation_prompt, temperature=0.2)
                topics = raw_topic_list.strip().split("\n")
                topics = [topic.strip() for topic in topics if topic.strip()]
                
                st.session_state.learner_profile = {
                    "purpose": purpose,
                    "known_language": known_language,
                    "known_language_level": level_known_language,
                    "target_language": target_language,
                    "target_language_level": level_target_language,
                    "learning_focus": learning_focus,
                    "topics": topics}
                
                st.success("Profile updated successfully!")
            else:
                st.warning("Complete your profile before you save")

        st.divider()
        st.subheader("📋 Profile Overview")

        profile_overview = st.session_state.learner_profile
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.metric("Base Language", profile_overview.get("known_language", "N/A"), f"{profile_overview.get('known_language_level', 0)}% Proficiency")
        with col_b:
            st.metric("Target Language", profile_overview.get("target_language", "N/A"), profile_overview.get("target_language_level", "N/A"))
        with col_c:
            st.metric("Learning Focus", ", ".join(profile_overview.get("learning_focus",[])))

        st.markdown(f"**🎯 Learning Motivation:**")
        st.info(profile_overview.get("purpose", "No purpose specified yet."))

        st.markdown("**💡 Recommended Learning Topics:**")
        if profile_overview.get("topics"):
            cols = st.columns(2)
            for idx, topic in enumerate(profile_overview["topics"]):
                cols[idx % 2].markdown(f"- {topic}")

elif page == "Learner Dashboard":
    st.title("📊 Learner Dashboard & Progress")
    
    profile = st.session_state.learner_profile
    if not profile:
        st.warning("Please complete your Learner Profile first.")
        st.stop()

    target_language = profile.get("target_language", "English")
    
    # Vocabulary Count
    total_vocab_saved = len(st.session_state.get("saved_vocab", []))
    
    # Directly reference saved grammar items from Grammar Practice page
    saved_explanations = st.session_state.get("saved_grammar_explanations", [])
    saved_examples = st.session_state.get("saved_grammar_examples", [])
    total_grammar_saved = len(saved_explanations) + len(saved_examples)
    
    # Conversation Sessions Count
    total_conversations = len(st.session_state.get("chat_history_list", []))
    
    # 🎯 Learning Statistics Metrics
    st.subheader("🎯 Learning Statistics")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(label="Saved Vocabulary", value=total_vocab_saved, delta="Words Saved")
    with col2:
        st.metric(label="Saved Grammar Items", value=total_grammar_saved, delta="Concepts & Examples")
    with col3:
        st.metric(label="Chat Sessions", value=total_conversations, delta="Sessions Practiced")

    st.divider()

    # 📈 Progress Overview
    st.subheader("📈 Progress Overview")
    st.write(f"User ID: **{st.session_state.current_user_id}**")
    st.write(f"Studying **{target_language}** at the **{profile.get('target_language_level', 'Beginner')}** level.")

    st.markdown("---")
    st.subheader("📚 Vocabulary Progress")
    
    vocab_target = 50
    progress_percentage = min(total_vocab_saved / vocab_target, 1.0)
    
    st.write(f"**Milestone Goal:** {total_vocab_saved} / {vocab_target} words saved ({int(progress_percentage * 100)}% completed)")
    st.progress(progress_percentage)

    if total_vocab_saved == 0:
        st.info("Start generating and saving vocabulary words to see your progress update here!")
    elif total_vocab_saved >= vocab_target:
        st.success("🎉 Outstanding job! You have reached your initial vocabulary milestone goal!")
    else:
        st.caption(f"Keep practicing! Save {vocab_target - total_vocab_saved} more words to hit your next milestone.")

elif page == "Vocabulary Practice":
    st.title("📚 Vocabulary Practice")

    profile = st.session_state.learner_profile

    if not profile:
        st.warning("Please complete your Learner Profile first.")
        st.stop()

    topics = profile.get("topics", [])

    if not topics:
        st.warning("No topics available. Please update your Learner Profile.")
        st.stop()

    target_language = profile.get("target_language", "English")
    known_language = profile.get("known_language", "English")

    # Create Tabs for New Vocab and Saved Vocab
    tab_new, tab_saved = st.tabs(["✨ Generate New", "⭐ Saved Vocabulary"])

    # ---------------------------------------------------------
    # TAB 1: Generate & Practice New Vocabulary
    # ---------------------------------------------------------
    with tab_new:
        selected_topic = st.selectbox(
            "Choose a topic",
            topics,
            key="vocab_topic_selector"
        )

        st.session_state.selected_topics = selected_topic

        if st.button("✨ Generate Vocabulary"):
            with st.spinner("Generating vocabulary..."):
                generate_vocabulary()

        st.divider()

        if st.session_state.vocab_items:
            st.subheader(f"Vocabulary: {st.session_state.selected_topics}")
            
            # Extract saved word names
            saved_words = [v.get("word") for v in st.session_state.saved_vocab if isinstance(v, dict)]

            # Filter out saved words so they are not shown on this tab
            unsaved_vocab_items = [
                item for item in st.session_state.vocab_items 
                if item.get("word") not in saved_words
            ]

            if not unsaved_vocab_items:
                st.info("All vocabulary words from this batch have been saved! Check the ⭐ **Saved Vocabulary** tab to view them, or click **Generate Vocabulary** again.")
            else:
                for index, item in enumerate(unsaved_vocab_items, start=1):
                    word = item.get("word", "")
                    reading = item.get("reading", "")
                    definition = item.get("definition", "")
                    example = item.get("example_sentence", "")

                    with st.container(border=True):
                        if reading:
                            st.markdown(f"### {index}. {word} <small style='color: gray;'>({known_language} Reading: {reading})</small>", unsafe_allow_html=True)
                        else:
                            st.markdown(f"### {index}. {word}")

                        st.write(f"**Definition:** {definition}")
                        st.write(f"**Example:** {example}")

                        saved = st.checkbox(
                            f"⭐ Save {word}",
                            value=False,
                            key=f"save_vocab_{word}_{index}"
                        )

                        if saved:
                            if item not in st.session_state.saved_vocab:
                                st.session_state.saved_vocab.append(item)
                                st.rerun()
        else:
            st.info("Click **Generate Vocabulary** to create your vocabulary cards.")

    # ---------------------------------------------------------
    # TAB 2: Review Saved Vocabulary
    # ---------------------------------------------------------
    with tab_saved:
        st.subheader(f"⭐ Saved Vocabulary Words ({len(st.session_state.saved_vocab)})")

        if not st.session_state.saved_vocab:
            st.info("You haven't saved any vocabulary items yet! Generate words in the other tab and check the star box to save them.")
        else:
            # Iterate through a copy so items can be safely removed
            for idx, item in enumerate(list(st.session_state.saved_vocab), start=1):
                word = item.get("word", "")
                reading = item.get("reading", "")
                definition = item.get("definition", "")
                example = item.get("example_sentence", "")

                with st.container(border=True):
                    col_info, col_action = st.columns([0.85, 0.15])
                    
                    with col_info:
                        if reading:
                            st.markdown(f"### {idx}. {word} <small style='color: gray;'>({known_language} Reading: {reading})</small>", unsafe_allow_html=True)
                        else:
                            st.markdown(f"### {idx}. {word}")

                        st.write(f"**Definition:** {definition}")
                        st.write(f"**Example:** {example}")

                    with col_action:
                        if st.button("🗑️ Remove", key=f"remove_saved_tab_{word}_{idx}"):
                            st.session_state.saved_vocab.remove(item)
                            st.rerun()

elif page == "Grammar Practice":
    st.title("📖 Grammar Practice")
    
    profile = st.session_state.learner_profile

    if not profile:
        st.warning("Please complete your Learner Profile first.")
        st.stop()

    topics = profile.get("topics", [])

    if not topics:
        st.warning("No topics available in your profile. Please update your Learner Profile first.")
        st.stop()

    target_language = profile.get("target_language", "English")
    known_language = profile.get("known_language", "English")
    level = profile.get("target_language_level", "Beginner")

    # Initialize separate saved lists in session_state if not present
    if "saved_grammar_explanations" not in st.session_state:
        st.session_state.saved_grammar_explanations = []
    if "saved_grammar_examples" not in st.session_state:
        st.session_state.saved_grammar_examples = []

    # Navigation Tabs
    tab_practice, tab_saved_exp, tab_saved_ex = st.tabs([
        "✨ Practice", 
        "⭐ Saved Explanations", 
        "⭐ Saved Examples"
    ])

    # ---------------------------------------------------------
    # TAB 1: Practice & Generation
    # ---------------------------------------------------------
    with tab_practice:
        st.write(f"**Target Language:** {target_language} | **Level:** {level}")
        st.divider()

        # Text input as the basis for concept explanation
        previous_topic = st.session_state.get("current_grammar_input", "")
        grammar_concept = st.text_input(
            "Enter exact grammar concept to learn (e.g., Past Tense, Conditional, Articles):",
            value=previous_topic,
            key="grammar_concept_text_input"
        )

        if grammar_concept != previous_topic:
            st.session_state["current_grammar_input"] = grammar_concept
            st.session_state.pop("current_explanation", None)
            st.session_state.pop("current_examples", None)

        # Situational topic selected from Learner Profile for examples only
        situational_topic = st.selectbox(
            "Select situational topic for examples (derived from your Profile):",
            topics,
            key="situational_topic_selector"
        )

        st.divider()

        col_btn1, col_btn2, col_btn3 = st.columns(3)
        with col_btn1:
            explain_clicked = st.button("✨ Explain Concept")
        with col_btn2:
            examples_clicked = st.button("📝 Generate Examples")
        with col_btn3:
            reset_clicked = st.button("🔄 Reset / Clear")

        if reset_clicked:
            st.session_state.pop("current_explanation", None)
            st.session_state.pop("current_examples", None)
            st.rerun()

        # Explain Concept based on Text Input
        if explain_clicked:
            if not grammar_concept.strip():
                st.warning("Please enter a grammar concept above first.")
            else:
                with st.spinner("Generating grammar explanation..."):
                    explanation_prompt = f"""
Explain the grammar concept: "{grammar_concept}" for a {level} student learning {target_language}.
The explanation must be written in {known_language}.

Return ONLY valid JSON with no markdown formatting or backticks:
{{
    "explanation": "Clear, step-by-step explanation of the concept..."
}}
"""
                    response_text = ask_groq(system_prompt, explanation_prompt, temperature=0.5).strip()

                    try:
                        if response_text.startswith("```json"):
                            response_text = response_text[7:]
                        if response_text.endswith("```"):
                            response_text = response_text[:-3]
                        
                        parsed_output = json.loads(response_text.strip())
                        st.session_state.current_explanation = parsed_output.get("explanation", "")
                    except json.JSONDecodeError:
                        st.error("The AI response was not valid JSON.")
                        st.code(response_text)

        # Generate Examples combining Grammar Concept + Selected Situational Topic
        if examples_clicked:
            if not grammar_concept.strip():
                st.warning("Please enter a grammar concept above first.")
            else:
                with st.spinner("Generating contextual examples..."):
                    examples_prompt = f"""
Generate 3 practical example sentences demonstrating the grammar concept "{grammar_concept}" for a {level} student learning {target_language}.
Incorporate the situation/theme: "{situational_topic}".
For each example sentence, include a reading or pronunciation guide written in/explained using {known_language} in a field named "furigana".

Return ONLY valid JSON with no markdown formatting or backticks:
{{
    "examples": [
        {{
            "sentence": "Example sentence in target language",
            "furigana": "Pronunciation guide explained in {known_language}",
            "translation": "Translation in known language"
        }}
    ]
}}
"""
                    response_text = ask_groq(system_prompt, examples_prompt, temperature=0.5).strip()

                    try:
                        if response_text.startswith("```json"):
                            response_text = response_text[7:]
                        if response_text.endswith("```"):
                            response_text = response_text[:-3]
                        
                        parsed_output = json.loads(response_text.strip())
                        st.session_state.current_examples = parsed_output.get("examples", [])
                    except json.JSONDecodeError:
                        st.error("The AI response was not valid JSON.")
                        st.code(response_text)

        # --- Display & Save Explanation ---
        if st.session_state.get("current_explanation"):
            st.subheader(f"💡 Concept Explanation: {grammar_concept}")
            with st.container(border=True):
                st.markdown(st.session_state.current_explanation)

            saved_concepts = [e.get("concept") for e in st.session_state.saved_grammar_explanations if isinstance(e, dict)]
            is_exp_saved = grammar_concept in saved_concepts

            save_exp_checkbox = st.checkbox(
                f"⭐ Save Explanation for: {grammar_concept}",
                value=is_exp_saved,
                key=f"save_exp_{grammar_concept}"
            )

            exp_item = {
                "concept": grammar_concept,
                "target_language": target_language,
                "explanation": st.session_state.current_explanation
            }

            if save_exp_checkbox and not is_exp_saved:
                st.session_state.saved_grammar_explanations.append(exp_item)
                st.rerun()
            elif not save_exp_checkbox and is_exp_saved:
                st.session_state.saved_grammar_explanations = [
                    e for e in st.session_state.saved_grammar_explanations 
                    if e.get("concept") != grammar_concept
                ]
                st.rerun()

        # --- Display & Save Examples ---
        if st.session_state.get("current_examples"):
            st.subheader(f"📝 Contextual Examples ({grammar_concept} — Topic: {situational_topic})")

            for idx, ex in enumerate(st.session_state.current_examples, start=1):
                sentence = ex.get('sentence', '')
                furigana = ex.get('furigana', '')
                translation = ex.get('translation', '')

                with st.container(border=True):
                    if furigana:
                        st.markdown(f"**Example {idx}:** {sentence} <small style='color: gray;'>(Pronunciation: {furigana})</small>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"**Example {idx}:** {sentence}")
                        
                    st.write(f"*Translation:* {translation}")

                    # Check if sentence is already saved
                    saved_sentences = [s.get("sentence") for s in st.session_state.saved_grammar_examples if isinstance(s, dict)]
                    is_ex_saved = sentence in saved_sentences

                    save_ex_cb = st.checkbox(
                        f"⭐ Save Example {idx}",
                        value=is_ex_saved,
                        key=f"save_ex_{grammar_concept}_{idx}"
                    )

                    ex_item = {
                        "concept": grammar_concept,
                        "topic": situational_topic,
                        "sentence": sentence,
                        "furigana": furigana,
                        "translation": translation
                    }

                    if save_ex_cb and not is_ex_saved:
                        st.session_state.saved_grammar_examples.append(ex_item)
                        st.rerun()
                    elif not save_ex_cb and is_ex_saved:
                        st.session_state.saved_grammar_examples = [
                            s for s in st.session_state.saved_grammar_examples 
                            if s.get("sentence") != sentence
                        ]
                        st.rerun()

    # ---------------------------------------------------------
    # TAB 2: Saved Grammar Explanations
    # ---------------------------------------------------------
    with tab_saved_exp:
        st.subheader(f"⭐ Saved Explanations ({len(st.session_state.saved_grammar_explanations)})")

        if not st.session_state.saved_grammar_explanations:
            st.info("No explanations saved yet. Generate an explanation in the Practice tab and check the star box to save it.")
        else:
            for idx, item in enumerate(list(st.session_state.saved_grammar_explanations), start=1):
                concept = item.get("concept", "")
                explanation = item.get("explanation", "")

                with st.container(border=True):
                    col_info, col_action = st.columns([0.85, 0.15])
                    with col_info:
                        st.markdown(f"### {idx}. {concept}")
                        st.markdown(explanation)
                    with col_action:
                        if st.button("🗑️ Remove", key=f"remove_exp_{concept}_{idx}"):
                            st.session_state.saved_grammar_explanations.remove(item)
                            st.rerun()

    # ---------------------------------------------------------
    # TAB 3: Saved Grammar Examples
    # ---------------------------------------------------------
    with tab_saved_ex:
        st.subheader(f"⭐ Saved Examples ({len(st.session_state.saved_grammar_examples)})")

        if not st.session_state.saved_grammar_examples:
            st.info("No examples saved yet. Generate examples in the Practice tab and check the star box to save them.")
        else:
            for idx, item in enumerate(list(st.session_state.saved_grammar_examples), start=1):
                concept = item.get("concept", "")
                topic = item.get("topic", "")
                sentence = item.get("sentence", "")
                furigana = item.get("furigana", "")
                translation = item.get("translation", "")

                with st.container(border=True):
                    col_info, col_action = st.columns([0.85, 0.15])
                    with col_info:
                        st.markdown(f"**Concept:** `{concept}` | **Topic:** `{topic}`")
                        if furigana:
                            st.markdown(f"### {idx}. {sentence} <small style='color: gray;'>(Pronunciation: {furigana})</small>", unsafe_allow_html=True)
                        else:
                            st.markdown(f"### {idx}. {sentence}")
                        st.write(f"*Translation:* {translation}")

                    with col_action:
                        if st.button("🗑️ Remove", key=f"remove_ex_{idx}"):
                            st.session_state.saved_grammar_examples.remove(item)
                            st.rerun()

elif page == "Conversation Practice":
    st.title("💬 Conversation Practice & Feedback")

    profile = st.session_state.learner_profile

    if not profile:
        st.warning("Please complete your Learner Profile first.")
        st.stop()

    target_language = profile.get("target_language", "English")
    known_language = profile.get("known_language", "English")
    level = profile.get("target_language_level", "Beginner")
    selected_topic = st.session_state.get("selected_topics", "General Conversation")

    if "chat_history_list" not in st.session_state:
        st.session_state.chat_history_list = []
    if "current_chat_id" not in st.session_state:
        st.session_state.current_chat_id = str(uuid.uuid4())
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "feedback_report" not in st.session_state:
        st.session_state.feedback_report = {}

    def save_current_chat():
        if not st.session_state.messages:
            return
            
        chat_id = st.session_state.get("current_chat_id")
        if not chat_id:
            chat_id = str(uuid.uuid4())
            st.session_state.current_chat_id = chat_id
            
        first_user_msg = next((msg["content"] for msg in st.session_state.messages if msg["role"] == "user"), None)
        
        if first_user_msg:
            truncated_topic = first_user_msg[:30] + ("..." if len(first_user_msg) > 30 else "")
            chat_title = f"{truncated_topic} ({target_language})"
        else:
            chat_title = f"{selected_topic} ({target_language})"
        
        found_index = -1
        for idx, item in enumerate(st.session_state.chat_history_list):
            if item.get("id") == chat_id:
                found_index = idx
                break
        
        chat_data = {
            "id": chat_id,
            "title": chat_title,
            "messages": st.session_state.messages.copy(),
            "report": st.session_state.get("feedback_report", {}).copy()
        }
        
        if found_index != -1:
            st.session_state.chat_history_list[found_index] = chat_data
        else:
            st.session_state.chat_history_list.append(chat_data)

    with st.sidebar:
        st.markdown("### 🗂️ Chat History")
        if st.button("➕ New Chat Session"):
            save_current_chat()
            st.session_state.messages = []
            st.session_state.feedback_report = {}
            st.session_state.current_chat_id = str(uuid.uuid4())
            st.rerun()

        if st.session_state.chat_history_list:
            st.markdown("---")
            st.markdown("**Past Conversations:**")
            # Displaying reversed list so the most recent chat appears at the top
            for i, past_chat in enumerate(reversed(st.session_state.chat_history_list)):
                c_id = past_chat.get("id", f"chat_{i}")
                c_title = past_chat.get("title", f"Chat {i}")
                
                col_btn, col_del = st.columns([0.8, 0.2])
                with col_btn:
                    if st.button(c_title, key=f"history_{i}_{c_id}"):
                        save_current_chat()
                        st.session_state.messages = past_chat.get("messages", []).copy()
                        st.session_state.feedback_report = past_chat.get("report", {}).copy()
                        st.session_state.current_chat_id = c_id
                        st.rerun()
                with col_del:
                    if st.button("🗑️", key=f"delete_{i}_{c_id}"):
                        st.session_state.chat_history_list = [
                            item for item in st.session_state.chat_history_list if item.get("id") != c_id
                        ]
                        if st.session_state.current_chat_id == c_id:
                            st.session_state.messages = []
                            st.session_state.feedback_report = {}
                            st.session_state.current_chat_id = str(uuid.uuid4())
                        st.rerun()

    st.write(f"**Target Language:** {target_language} ({level}) | **Topic:** {selected_topic}")
    st.divider()

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input(f"Type a message in {target_language}..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                chat_system_prompt = f"""
You are a helpful language learning assistant practicing {target_language} with a {level} student whose base language is {known_language}. 
The current conversation topic is: "{selected_topic}".
Respond naturally in {target_language}, matching their proficiency level. Keep the conversation engaging and relevant to the topic.
"""
                api_messages = [{"role": "system", "content": chat_system_prompt}] + st.session_state.messages
                
                chat_completion = client.chat.completions.create(
                    messages=api_messages,
                    model="openai/gpt-oss-120b",
                    temperature=0.7
                )
                response_text = chat_completion.choices[0].message.content.strip()
                
                st.markdown(response_text)
                st.session_state.messages.append({"role": "assistant", "content": response_text})
                save_current_chat()

    st.divider()
    
    col_eval, col_clear = st.columns(2)
    with col_eval:
        evaluate_clicked = st.button("📊 Evaluate Dialogue")
    with col_clear:
        new_chat_clicked = st.button("🔄 Start a new chat")

    if new_chat_clicked:
        save_current_chat()
        st.session_state.messages = []
        st.session_state.feedback_report = {}
        st.session_state.current_chat_id = str(uuid.uuid4())
        st.rerun()

    if evaluate_clicked:
        if not st.session_state.messages:
            st.warning("No conversation history to evaluate yet. Start chatting above!")
        else:
            with st.spinner("Analyzing your conversation..."):
                transcript = "\n".join([f"{msg['role'].upper()}: {msg['content']}" for msg in st.session_state.messages])
                
                eval_system_prompt = "You are an expert language teacher providing structured JSON evaluation reports."
                feedback_prompt = f"""
Analyze the following conversation transcript between a language learner and an AI tutor.
Target Language: {target_language}
Learner Level: {level}
Base/Known Language: {known_language}

Transcript:
{transcript}

Provide a constructive feedback report in {known_language} covering:
1. Strengths
2. Areas for improvement
3. Overall summary.

Return ONLY valid JSON with no markdown formatting or backticks:
{{
    "strengths": "...",
    "improvements": "...",
    "summary": "..."
}}
"""
                eval_completion = client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": eval_system_prompt},
                        {"role": "user", "content": feedback_prompt}
                    ],
                    model="openai/gpt-oss-120b",
                    temperature=0.3
                )
                response_text = eval_completion.choices[0].message.content.strip()

                try:
                    if response_text.startswith("```json"):
                        response_text = response_text[7:]
                    if response_text.endswith("```"):
                        response_text = response_text[:-3]
                    
                    st.session_state.feedback_report = json.loads(response_text.strip())
                    save_current_chat()
                except json.JSONDecodeError:
                    st.error("The AI response was not valid JSON.")
                    st.code(response_text)

    if st.session_state.get("feedback_report"):
        report = st.session_state.feedback_report
        with st.expander("📝 View Detailed Feedback Report", expanded=True):
            st.markdown(f"**🌟 Strengths:**\n{report.get('strengths', '')}")
            st.markdown(f"**🔧 Areas for Improvement:**\n{report.get('improvements', '')}")
            st.markdown(f"**💡 Summary:**\n{report.get('summary', '')}")