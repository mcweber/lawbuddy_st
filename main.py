# ---------------------------------------------------
VERSION ="20.12.2024"
# Author: M. Weber
# ---------------------------------------------------
#
# ---------------------------------------------------

import streamlit as st
import ask_llm
import ask_web
import ask_mongo
import manage_user as user
import manage_prompts as prompts

from dotenv import load_dotenv
load_dotenv()

# Functions -------------------------------------------------------------
@st.dialog("Login")
def login_code_dialog() -> None:
    with st.form(key="loginForm"):
        code = st.text_input(label="Code", type="password")
        if st.form_submit_button("Enter"):
            if code == os.environ.get('CODE'):
                st.session_state.code = True
                st.rerun()
            else:
                st.error("Code is not correct.")

@st.experimental_dialog("Login User")
def login_user_dialog() -> None:
    with st.form(key="loginForm"):
        st.write(f"Status: {st.session_state.userStatus}")
        user_name = st.text_input("Benutzer")
        user_pw = st.text_input("Passwort", type="password")
        if st.form_submit_button("Login"):
            if user_name and user_pw:
                active_user = chatbuddy_user.check_user(user_name, user_pw)
                if active_user:
                    st.session_state.userName = active_user["username"]
                    st.session_state.userRole = active_user["rolle"]
                    st.session_state.userStatus = 'True'
                    st.rerun()
                else:
                    st.error("User not found.")
            else:
                st.error("Please fill in all fields.")

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
        st.session_state.history: list = []
        st.session_state.marktbereich: str = "Alle"
        st.session_state.marktbereichIndex: int = 0
        st.session_state.results: str = ""
        st.session_state.searchResultsLimit:int  = 5
        st.session_state.searchStatus: bool = False
        st.session_state.searchWeb: bool = False
        st.session_state.showLatest: bool = False
        st.session_state.systemPrompt: str = prompts.get_systemprompt()
        st.session_state.userName: str = ""
        st.session_state.userRole: str = ""
        st.session_state.userStatus: bool = True
        st.session_state.webResults: str = ""

    if st.session_state.code == False:
        login_code_dialog()

    # Define Sidebar ---------------------------------------------------
    with st.sidebar:
        st.header("LawBuddy")
        st.caption(f"Version: {VERSION} Status: POC")
        # if st.session_state.userStatus and st.session_state.userName:
        #     st.caption(f"Eingeloggt als: {st.session_state.userName}")
        # else:
        #     st.caption("Nicht eingeloggt.")
        switch_searchWeb = st.checkbox(label="Web-Suche", value=st.session_state.searchWeb)
        if switch_searchWeb != st.session_state.searchWeb:
            st.session_state.searchWeb = switch_searchWeb
            st.rerun()
        switch_search_results = st.slider("Search Results", 1, 50, st.session_state.searchResultsLimit)
        if switch_search_results != st.session_state.searchResultsLimit:
            st.session_state.searchResultsLimit = switch_search_results
            st.rerun()
        switch_SystemPrompt = st.text_area("System-Prompt", st.session_state.systemPrompt, height=200)
        if switch_SystemPrompt != st.session_state.systemPrompt:
            st.session_state.systemPrompt = switch_SystemPrompt
            prompts.update_systemprompt(switch_SystemPrompt)
            st.rerun()
        st.divider()
        st.text_area("Web Results", st.session_state.webResults, height=200)
        st.divider()
        st.text_area("History", st.session_state.history, height=200)
        if st.button("Clear History"):
            st.session_state.history = []
            st.session_state.webResults = ""
            st.rerun()

    # Define Search Form ----------------------------------------------
    question = st.chat_input("Frage eingeben:")
    if question:
        if question == "test":
            question = "Was sagt das BAG zur Abmahnung?"
        if question == "reset":
            st.session_state.history = []
            st.session_state.webResults = ""
            st.rerun()
        st.session_state.searchStatus = True

    # Define Search & Search Results -------------------------------------------
    if st.session_state.userStatus and st.session_state.searchStatus:
        web_results_str = ""
        if st.session_state.searchWeb and st.session_state.webResults == "":
            # Web Search ------------------------------------------------
            web_search_handler = ask_web.WebSearch()
            results = web_search_handler.search(query=question, score=0.5, limit=st.session_state.searchResultsLimit)
            with st.expander("WEB Suchergebnisse"):
                for result in results:
                    st.write(f"[{round(result['score'], 3)}] {result['title']} [{result['url']}]")
                    # web_results_str += f"Titel: {result['title']}\nURL: {result['url']}\n\n"
                    web_results_str += f"Titel: {result['title']}\nURL: {result['url']}\nText: {result['content']}\n\n"
            st.session_state.webResults = web_results_str

        # Database Search ------------------------------------------------
        db_results_str = ""
        results_list, suchworte = ask_mongo.text_search(search_text=question, gen_suchworte=True, limit=10)
        with st.expander("Entscheidungssuche"):
            st.write(f"Suchworte: {suchworte}")
            for result in results_list:
                st.write(f"{result['gericht']}, {result['entsch_datum']}, {result['aktenzeichen']}")
                db_results_str += f"Gericht: {result['gericht']}\nDatum: {result['entsch_datum']}\nAktenzeichen: {result['aktenzeichen']}\nText: {result['xml_text']}\n\n"
        if len(results_list) == 0:
            st.write("Keine Entscheidungen gefunden.")
            exit()

        # LLM Search ------------------------------------------------
        llm_handler = ask_llm.LLMHandler(llm="gpt4omini")
        summary = llm_handler.ask_llm(
            # llm=st.session_state.llmStatus,
            temperature=0.2,
            question=question,
            history=st.session_state.history,
            systemPrompt=st.session_state.systemPrompt,
            db_results_str=db_results_str,
            web_results_str=st.session_state.webResults
            )
        # with st.chat_message("assistant"):
        #     # st.write(prompt)
        #     st.write(summary)
        st.session_state.history.append({"role": "user", "content": question})
        st.session_state.history.append({"role": "assistant", "content": summary})
        write_history()
        st.session_state.searchStatus = False

if __name__ == "__main__":
    main()
