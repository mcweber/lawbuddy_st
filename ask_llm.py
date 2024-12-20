# ---------------------------------------------------
# Version: 18.12.2024
# Author: M. Weber
# ---------------------------------------------------
# 30.08.2024 switched to class-based approach
# 12.10.2023 added source documents
# 18.12.2024 added CODE for authentication
# ---------------------------------------------------

from datetime import datetime
import os
from dotenv import load_dotenv
import psutil

import openai
# import anthropic
# from groq import Groq
import ollama

def check_code(code) -> bool:
    load_dotenv()
    return code == os.environ.get('CODE')


class LLMHandler:
    def __init__(self, llm: str = "gpt4omini", local: bool = False):
        # self.LLMS = ["gpt4omini", "gpt4o", "anthropic", "mistral", "llama3.1", "gemma"]
        self.LLM = llm
        self.LOCAL = local
        load_dotenv()
        self.openaiClient = openai.OpenAI(api_key=os.environ.get('OPENAI_API_KEY_PRIVAT'))
    
    @staticmethod
    def is_ollama_running() -> bool:
        for proc in psutil.process_iter(['pid', 'name']):
            if 'ollama' in proc.info['name'].lower():
                return True
        return False

    @staticmethod
    def define_prompt(system_prompt: str = "", question: str = "", history: list = [], db_results_str: str = "", web_results_str: str = "", source_doc_str:str = "") -> list:
        prompt = [
            {"role": "system", "content": f"{system_prompt} Current date is {datetime.now().date()}."}
        ]
        prompt.extend(history)
        if db_results_str:
            prompt.append({"role": "assistant", "content": f'Here are some relevant information from a database search:\n{db_results_str}'})
        if web_results_str:
            prompt.append({"role": "assistant", "content": f'Here are some relevant information from a web search:\n{web_results_str}'})
        if source_doc_str:
            prompt.append({"role": "assistant", "content": f'This is the source document:\n{source_doc_str}'})
        question_prefix = "Based on the above information, " if web_results_str or db_results_str else ""
        prompt.append({"role": "user", "content": f"{question_prefix}{question}"})

        return prompt

    def ask_llm(self, temperature: float = 0.2, question: str = "", history: list = [],
                system_prompt: str = "", db_results_str: str = "", web_results_str: str = "", source_doc_str: str = "") -> str:
        prompt = self.define_prompt(system_prompt, question, history, db_results_str, web_results_str, source_doc_str)
        if self.LOCAL:
            return self._handle_local_llm(prompt)
        else:
            return self._handle_remote_llm(temperature, prompt)

    def _handle_local_llm(self, input_messages: list) -> str:
        if self.LLM == "mistral":
            response = ollama.chat(model="mistral", messages=input_messages)
            return response['message']['content']
        elif self.LLM == "llama3.2":
            response = ollama.chat(model="llama3.2", messages=input_messages)
            return response['message']['content']
        else:
            return f"Error: No valid local LLM specified [{self.LLM}]."

    def _handle_remote_llm(self, temperature: float, input_messages: list) -> str:
        if self.LLM == "gpt4o":
            response = self.openaiClient.chat.completions.create(model="gpt-4o", temperature=temperature, messages=input_messages)
            return response.choices[0].message.content
        elif self.LLM == "gpt4omini":
            response = self.openaiClient.chat.completions.create(model="gpt-4o-mini", temperature=temperature, messages=input_messages)
            return response.choices[0].message.content
        # elif self.LLM == "anthropic":
        #     response = self.anthropicClient.messages.create(model="claude-3-5-sonnet-20240620", max_tokens=1024, system=input_messages[0]['content'], messages=input_messages[1:])
        #     return response.content[0].text
        # elif self.LLM == "groq_mixtral-8x7b-32768":
        #     response = self.groqClient.chat.completions.create(model="mixtral-8x7b-32768", temperature=temperature, messages=input_messages)
        #     return response.choices[0].message.content
        # elif self.LLM == "groq_llama3-70b-8192":
        #     response = self.groqClient.chat.completions.create(model="llama3-70b-8192", temperature=temperature, messages=input_messages)
        #     return response.choices[0].message.content
        # # elif self.LLM == "groq_gemma-7b-it":
        #     response = self.groqClient.chat.completions.create(model="gemma-7b-it", temperature=temperature, messages=input_messages)
        #     return response.choices[0].message.content
        else:
            return "Error: No valid remote LLM specified."
