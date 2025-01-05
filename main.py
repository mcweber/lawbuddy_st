# ---------------------------------------------------
VERSION ="05.01.2025"
# Author: M. Weber
# ---------------------------------------------------
# 05.01.2024 added o1, o1-mini
# 05.01.2025 added model select
# ---------------------------------------------------

import streamlit as st
import ask_llm
# import ask_web
import ask_legal_web
import ask_mongo
# import manage_user as user
import manage_prompts as prompts

import os
from dotenv import load_dotenv
load_dotenv()

# Functions -------------------------------------------------------------
@st.dialog("Login")
def login_code_dialog() -> None:
    with st.form(key="login_code_form"):
        code = st.text_input(label="Code", type="password")
        if st.form_submit_button("Enter"):
            if code == os.environ.get('CODE'):
                st.success("Code is correct.")
                st.session_state.code = True
                st.rerun()
            else:
                st.error("Code is not correct.")

def write_history() -> None:
    for entry in st.session_state.history:
        with st.chat_message(entry["role"]):
            st.write(f"{entry['content']}")

# Main -----------------------------------------------------------------
def main() -> None:
    st.set_page_config(page_title='lawbuddy', initial_sidebar_state="collapsed")

    # Initialize Session State -----------------------------------------
    if 'init' not in st.session_state:
        # Check if System-Prompt exists
        if prompts.get_systemprompt() == {}:
            prompts.add_systemprompt("Du bist ein hilfreicher Assistent.")
        st.session_state.init: bool = True
        st.session_state.code: bool = False
        st.session_state.model: str = "gemini"
        st.session_state.system_prompt: str = prompts.get_systemprompt()
        st.session_state.search_status: bool = False
        st.session_state.search_db: bool = False
        st.session_state.search_web: bool = False
        st.session_state.history: list = []
        st.session_state.results_limit:int  = 10
        st.session_state.results_web: str = ""
        st.session_state.results_db: str = ""

    if st.session_state.code == False:
        login_code_dialog()

    # Define Sidebar ---------------------------------------------------
    with st.sidebar:
        st.header("LawBuddy")
        st.caption(f"Version: {VERSION} Status: POC")

        radio = st.radio("Model", ask_llm.MODELS, index=ask_llm.MODELS.index(st.session_state.model))
        if radio != st.session_state.model:
            st.session_state.model = radio
            st.rerun()

        checkbox = st.checkbox(label="LegalWeb-Suche", value=st.session_state.search_web)
        if checkbox != st.session_state.search_web:
            st.session_state.search_web = checkbox
            st.rerun()
        
        checkbox = st.checkbox(label="DB-Suche", value=st.session_state.search_db)
        if checkbox != st.session_state.search_db:
            st.session_state.search_db = checkbox
            st.rerun()
        
        slider = st.slider("Search Results", min_value=0, max_value=50, value=st.session_state.results_limit, step=10)
        if slider != st.session_state.results_limit:
            st.session_state.results_limit = slider
            st.rerun()
        
        switch_SystemPrompt = st.text_area("System-Prompt", st.session_state.system_prompt, height=200)
        if switch_SystemPrompt != st.session_state.system_prompt:
            st.session_state.system_prompt = switch_SystemPrompt
            prompts.update_systemprompt(switch_SystemPrompt)
            st.rerun()
        
        st.divider()
        
        st.text_area("Web Results", st.session_state.results_web, height=200)
        
        st.divider()
        
        st.text_area("History", st.session_state.history, height=200)
        if st.button("Clear History"):
            st.session_state.history = []
            st.session_state.results_web = ""
            st.session_state.results_db = ""
            st.rerun()

    # Define Search Form ----------------------------------------------
    question = st.chat_input("Frage oder test1, test2, test3 eingeben:")

    if question:
    
        if question == "test1":
            question = "Was sagt das BAG zur Abmahnung?"

        if question == "test2":
            question = "Kann man einen Mietvertrag per email kündigen?"

        if question == "test3":
            question = "Muß ein 14 Jähriger das erhöhte Beförderungsentgelt in der S-Bahn bezahlen?"
    
        if question == "reset":
            st.session_state.history = []
            st.session_state.web_results = ""
            st.rerun()
    
        st.session_state.search_status = True

    # Define Search & Search Results -------------------------------------------
    if st.session_state.search_status:

        # Web Search ------------------------------------------------
        web_results_str = ""
        if st.session_state.search_web and st.session_state.results_web == "":
            web_search_handler = ask_legal_web.LegalWebSearch()
            results_statutes = web_search_handler.search_statutes(query=question, score=0.5, limit=st.session_state.results_limit)
            results_jurisdiction = web_search_handler.search_jurisdiction(query=question, score=0.5, limit=st.session_state.results_limit)
            results_comments = web_search_handler.search_comments(query=question, score=0.5, limit=st.session_state.results_limit)
            web_results_str = results_statutes + results_jurisdiction + results_comments
            with st.expander("WEB Suchergebnisse"):
                st.write(results_statutes)
                st.divider()
                st.write(results_jurisdiction)
                st.divider()
                st.write(results_comments)
                # for result in results:
                #     st.write(f"[{round(result['score'], 3)}] {result['title']} [{result['url']}]")
                #     # web_results_str += f"Titel: {result['title']}\nURL: {result['url']}\n\n"
                #     web_results_str += f"Titel: {result['title']}\nURL: {result['url']}\nText: {result['content']}\n\n"
            st.session_state.results_web = web_results_str

        # Database Search ------------------------------------------------
        db_results_str = ""
        if st.session_state.search_db and st.session_state.results_db == "":
            results_list, suchworte = ask_mongo.text_search(search_text=question, gen_suchworte=True, limit=10)
            with st.expander("Entscheidungssuche"):
                st.write(f"Suchworte: {suchworte}")
                for result in results_list:
                    st.write(f"{result['gericht']}, {result['entsch_datum']}, {result['aktenzeichen']}")
                    db_results_str += f"Gericht: {result['gericht']}\nDatum: {result['entsch_datum']}\nAktenzeichen: {result['aktenzeichen']}\nText: {result['xml_text']}\n\n"
            st.session_state.results_db = db_results_str
            
        # LLM Search ------------------------------------------------
        llm_handler = ask_llm.LLMHandler()
        summary = llm_handler.ask_llm(
            temperature=0.2,
            question=question,
            history=st.session_state.history,
            system_prompt=st.session_state.system_prompt,
            db_results_str=st.session_state.results_db,
            web_results_str=st.session_state.results_web
            )
        # with st.chat_message("assistant"):
        #     # st.write(prompt)
        #     st.write(summary)
        st.session_state.history.append({"role": "user", "content": question})
        st.session_state.history.append({"role": "assistant", "content": summary})
        write_history()
        st.session_state.search_status = False

if __name__ == "__main__":
    main()
