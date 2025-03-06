# ---------------------------------------------------
VERSION = "06.03.2025"
# Author: M. Weber
# ---------------------------------------------------
# ---------------------------------------------------

import streamlit as st
from scrape_web import scrape_web
import ask_llm
import ask_web
import ask_mongo
import ask_doc

import os
from dotenv import load_dotenv
load_dotenv()

# Functions -------------------------------------------------------------
@st.dialog("Login")
def login_code_dialog() -> None:
    with st.form(key="login_code_form"):
        code = st.text_input(label="Code", type="password")
        if st.form_submit_button("Enter"):
            if code == os.environ.get('CODE1'):
                st.success("Code is correct.")
                st.session_state.code = True
                st.rerun()
            else:
                st.error("Code is not correct.")
                st.session_state.code = False
                st.stop()

def write_history() -> None:
    for entry in st.session_state.history:
        with st.chat_message(entry["role"]):
            st.write(f"{entry['content']}")

# Main -----------------------------------------------------------------
def main() -> None:
    st.set_page_config(page_title='lawbuddy', initial_sidebar_state="expanded")
    
    # Initialize Session State -----------------------------------------
    if 'init' not in st.session_state:
        # Check if System-Prompt exists
        if ask_mongo.get_system_prompt() == {}:
            ask_mongo.update_system_prompt("Du bist ein hilfreicher Assistent.")
        st.session_state.init: bool = True
        st.session_state.code: bool = False
        st.session_state.history: list = []
        st.session_state.llm: str = "gemini"
        st.session_state.marktbereich: str = "Alle"
        st.session_state.marktbereichIndex: int = 0
        st.session_state.results: str = ""
        st.session_state.search_db: bool = False
        st.session_state.searchResultsLimit:int  = 20
        st.session_state.searchStatus: bool = False
        st.session_state.searchWeb: bool = False
        st.session_state.showLatest: bool = False
        st.session_state.source_doc_str: str = ""
        st.session_state.systemPrompt: str = ask_mongo.get_system_prompt()
        st.session_state.userRole: str = ""
        st.session_state.webResults: str = ""
        
    if not st.session_state.code:
        login_code_dialog()
    
    # Define Sidebar ---------------------------------------------------
    with st.sidebar:
        st.header("LawBuddy")
        st.caption(f"Version: {VERSION}  | Status: POC | LLM: {st.session_state.llm}")
        
        # Search Web ---------------------------------------------------
        switch_searchWeb = st.checkbox(label="Web-Suche", value=st.session_state.searchWeb)
        if switch_searchWeb != st.session_state.searchWeb:
            st.session_state.searchWeb = switch_searchWeb
            st.rerun()
        if st.session_state.searchWeb:    
            switch_search_results = st.slider(label="Search Results", min_value=10, max_value=50, value=st.session_state.searchResultsLimit, step=10)
            if switch_search_results != st.session_state.searchResultsLimit:
                st.session_state.searchResultsLimit = switch_search_results
                st.rerun()
            st.divider()
        
        # File Upload ---------------------------------------------------
        file_data = st.file_uploader(label="Datei Upload", type=["pdf", "xlsx"])
        if file_data:
            file_type = str(file_data.name)[-3:]
            if file_type == "pdf":
                st.session_state.source_doc_str = ask_doc.read_pdf_streamlit(file_data)
            elif file_type == "lsx":
                st.session_state.source_doc_str = ask_doc.read_excel_streamlit(file_data)
        else:
            st.error("Keine Datei geladen.")
        st.divider()

        # Web Page Upload ---------------------------------------------------
        url = st.text_input(label="Upload Web page:")
        if url:
            st.session_state.source_doc_str = ask_doc.scrape_web(url)
            st.success("Webseite geladen.")
        else:
            st.error("Keine Webseite geladen.")
        st.divider()

        # System Prompt ---------------------------------------------------
        switch_SystemPrompt = st.text_area("System-Prompt", st.session_state.systemPrompt, height=200)
        if switch_SystemPrompt != st.session_state.systemPrompt:
            st.session_state.systemPrompt = switch_SystemPrompt
            ask_mongo.update_system_prompt(switch_SystemPrompt)
            st.rerun()
        st.divider()

        # History ---------------------------------------------------
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
        st.session_state.searchStatus = True

    # Define Search & Search Results -------------------------------------------
    if st.session_state.code and st.session_state.searchStatus:
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
        # if st.session_state.search_db:
        #     results_list, suchworte = ask_mongo.text_search(search_text=question, gen_suchworte=True, limit=10)
        #     with st.expander("Entscheidungssuche"):
        #         st.write(f"Suchworte: {suchworte}")
        #         for result in results_list:
        #             st.write(f"{result['gericht']}, {result['entsch_datum']}, {result['aktenzeichen']}")
        #             db_results_str += f"Gericht: {result['gericht']}\nDatum: {result['entsch_datum']}\nAktenzeichen: {result['aktenzeichen']}\nText: {result['xml_text']}\n\n"
        #     if len(results_list) == 0:
        #         st.write("Keine Entscheidungen gefunden.")
        #         exit()
            
        # LLM Search ------------------------------------------------
        llm_handler = ask_llm.LLMHandler(llm=st.session_state.llm)
        summary = llm_handler.ask_llm(
            temperature=0.2,
            question=question,
            history=st.session_state.history,
            system_prompt=st.session_state.systemPrompt,
            db_results_str=db_results_str,
            web_results_str=st.session_state.webResults,
            source_doc_str=st.session_state.source_doc_str
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
