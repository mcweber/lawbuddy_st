# ---------------------------------------------------
# Version: 10.11.2024
# Author: M. Weber
# ---------------------------------------------------
# ---------------------------------------------------

from datetime import datetime
import os
from dotenv import load_dotenv

import ask_llm

from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError

import torch
from transformers import BertTokenizer, BertModel

# Init LLM ----------------------------------
llm = ask_llm.LLMHandler(llm="gpt4o", local=False)
# llm = ask_llm.LLMHandler(llm="llama3", local=True)

# Init MongoDB Client
load_dotenv()
mongoClient = MongoClient(os.environ.get('MONGO_URI_PRIVAT'))
database = mongoClient.law_buddy
collection = database.rechtsprechung
collection_config = database.config

# Load pre-trained model and tokenizer
os.environ["TOKENIZERS_PARALLELISM"] = "false"
model_name = "bert-base-german-cased" # 768 dimensions
# model_name = "bert-base-multilingual-cased"
tokenizer = BertTokenizer.from_pretrained(model_name)
model = BertModel.from_pretrained(model_name)
# model_name = "sentence-transformers/all-MiniLM-L6-v2"
# tokenizer = AutoTokenizer.from_pretrained(model_name)
# model = AutoModel.from_pretrained(model_name)

# Define Database functions ----------------------------------
def generate_abstracts(input_field: str, output_field: str, max_iterations: int = 20) -> None:
    cursor = collection.find({output_field: ""}).limit(max_iterations)
    cursor_list = list(cursor)
    for record in cursor_list:
        abstract = write_summary(str(record[input_field]))
        print(record['titel'][:50])
        print("-"*50)
        collection.update_one({"_id": record.get('_id')}, {"$set": {output_field: abstract}})
    cursor.close()

def write_summary(text: str = "", length: int = 500) -> str:
    if text == "":
        return "empty"
    system_prompt = f"""
                    Du bist ein Redakteur im Bereich Transport und Verkehr.
                    Du bis Experte dafür, Zusammenfassungen von Fachartikeln zu schreiben.
                    Die maximale Länge der Zusammenfassungen sind {length} Wörter.
                    Wichtig ist nicht die Lesbarkeit, sondern die Kürze und Prägnanz der Zusammenfassung:
                    Was sind die wichtigsten Aussagen und Informationen des Textes?
                    """
    task = """
            Erstelle eine Zusammenfassung des Originaltextes in deutscher Sprache.
            Verwende keine Zeilenumrüche oder Absätze.
            Die Antwort darf nur aus dem eigentlichen Text der Zusammenfassung bestehen.
            """
    return llm.ask_llm(temperature=0.1, question=task, system_prompt=system_prompt, db_results_str=text)
    
def write_takeaways(text: str = "", max_takeaways: int = 5) -> str:
    if text == "":
        return "empty"
    system_prompt = """
                    Du bist ein Redakteur im Bereich Transport und Verkehr.
                    Du bis Experte dafür, die wichtigsten Aussagen von Fachartikeln herauszuarbeiten.
                    """
    task = f"""
            Erstelle eine Liste der wichtigsten Aussagen des Textes in deutscher Sprache.
            Es sollten maximal {max_takeaways} Aussagen sein.
            Jede Aussage sollte kurz und prägnant in einem eigenen Satz formuliert sein.
            Die Antwort darf nur aus den eigentlichen Aussagen bestehen.
            """
    return llm.ask_llm(temperature=0.1, question=task, system_prompt=system_prompt, db_results_str=text)

# Embeddings -------------------------------------------------            
def generate_embeddings(input_field: str, output_field: str, 
                        max_iterations: int = 10) -> None:
    cursor = collection.find({output_field: []}).limit(max_iterations)
    cursor_list = list(cursor)
    for record in cursor_list:
        article_text = record[input_field]
        if article_text == "":
            article_text = "Fehler: Kein Text vorhanden."
        else:
            embeddings = create_embeddings(text=article_text)
            collection.update_one({"_id": record['_id']}, {"$set": {output_field: embeddings}})
    print(f"\nGenerated embeddings for {max_iterations} records.")

def create_embeddings(text: str) -> list:
    encoded_input = tokenizer(text, padding=True, truncation=True, return_tensors="pt")
    with torch.no_grad():
        model_output = model(**encoded_input)
    return model_output.last_hidden_state.mean(dim=1).squeeze().tolist()

# Keywords ---------------------------------------------------
def generate_keywords(input_field: str, output_field: str, max_iterations: int = 10) -> None:
    print(f"Start: {input_field}|{output_field}")
    print(collection)
    cursor = collection.find({output_field: []}).limit(max_iterations)
    if cursor:
        print(f"MongoDB Suche abgeschlossen.")
        cursor_list = list(cursor)
        print(f"Anzahl Records: {len(cursor_list)}")
        for record in cursor_list:
            if record[input_field] == "":
                print("Kein Input-Text.")
                continue
            article_text = record.get(input_field, "Fehler: Kein Text vorhanden.")
            keywords = create_keywords(text=article_text)
            collection.update_one({"_id": record['_id']}, {"$set": {output_field: keywords}})
            print(keywords)
        print(f"\nGenerated keywords for {len(cursor_list)} records.")
    else:
        st.error("No articles without summary found.")
    cursor.close()

def create_keywords(text: str = "", max_keywords: int = 5) -> list:
    if not text:
        return []
    system_prompt = """
                    Du bist ein Rechtsanwalt und Bibliothekar.
                    Du bis Experte dafür, relevante Schlagwörter für die Inhalte von Gerichstentscheidungen zu schreiben.
                    """
    task = f"""
            Erstelle Schlagworte für den folgenden Text angegebenen Text.
            Erstelle maximal {max_keywords} Schlagworte.
            Die Antwort darf nur aus den eigentlichen Schlagworten bestehen.
            Das Format ist "Stichwort1, Stichwort2, Stichwort3, ..."
            """
    keywords_str = llm.ask_llm(temperature=0.1, question=task, system_prompt=system_prompt, db_results_str=text)
    keywords_list = [keyword.strip() for keyword in keywords_str.split(',') if keyword.strip()]
    return keywords_list

def list_keywords() -> list:
    pipeline = [
    {'$unwind': '$schlagworte'},
    {'$group': {
        '_id': '$schlagworte', 
        'count': {'$sum': 1}
        }
        },
    {'$sort': {'count': -1}},
    {'$project': {
        '_id': 0, 
        'keyword': '$_id', 
        'count': 1
        }
        }
    ]
    cursor_list = list(collection.aggregate(pipeline))
    return cursor_list

# Query & Filter ------------------------------------------------
def generate_query(question: str = "") -> str:
    task = f"""
            Erstelle auf Basis der Frage '{question}' eine Liste von maximal 3 Schlagworten mit deren Hilfe relevante Dokumente zu der Fragestellung in einer Datenbank gefunden werden können.
            Das Format ist "Stichwort1" "Stichwort2" "Stichwort3"
            """
    return llm.ask_llm(temperature=0.1, question=task) 
    
def generate_filter(filter: list, field: str) -> dict:
    return {field: {"$in": filter}} if filter else {}

# Search ------------------------------------------------
def text_search(search_text: str = "*", gen_suchworte: bool = False, score: float = 0.0, gericht_filter: list = [], limit: int = 10) -> (list, str):
    
    # define query ------------------------------------------------
    if search_text == "":
        return [], ""
    if search_text == "*":
        suchworte = "*"
        score = 0.0
        query = {
            "index": "volltext",
            "exists": {"path": "gericht"},
        }
    else:
        suchworte = generate_query(question=search_text) if gen_suchworte else search_text
        query = {
            "index": "volltext",
            "text": {
                "query": suchworte,
                "path": {"wildcard": "*"}
            }
        }

    # define fields ------------------------------------------------
    fields = {
        "_id": 1,
        "doknr": 1,
        "gericht": 1,
        "entsch_datum": 1,
        "aktenzeichen": 1,
        "xml_text": 1,
        "score": {"$meta": "searchScore"},
    }

    # define pipeline ------------------------------------------------
    pipeline = [
        {"$search": query},
        {"$project": fields},
        {"$match": {"score": {"$gte": score}}},
        {"$sort": {"entsch_datum": -1}},
        {"$limit": limit},
    ]
    if gericht_filter:
        pipeline.insert(1, {"$match": {"gericht": {"$in": gericht_filter}}})

    # execute query ------------------------------------------------
    cursor = collection.aggregate(pipeline)
    return list(cursor), suchworte


def vector_search(query_string: str = "*", gen_suchworte: bool = False, score: float = 0.0, filter : list = [], sort: str = "date", limit: int = 10) -> list[list, str]:
    suchworte = generate_query(question=query_string) if gen_suchworte else query_string
    embeddings_query = create_embeddings(text=suchworte)
    query = {
            "index": "vector_index",
            "path": "text_embeddings",
            "queryVector": embeddings_query,
            "numCandidates": int(limit * 10),
            "limit": limit,
            }
    fields = {
            "_id": 1,
            "quelle_id": 1,
            "jahrgang": 1,
            "nummer": 1,
            "titel": 1,
            "datum": 1,
            "untertitel": 1,
            "text": 1,
            "ki_abstract": 1,
            "date": 1,
            "score": {"$meta": "vectorSearchScore"}
            }
    pipeline = [
        {"$vectorSearch": query},
        {"$project": fields},
        {"$match": {"quelle_id": {"$in": filter}}},
        {"$match": {"score": {"$gte": score}}},  # Move this up
        {"$sort": {sort: -1}},
        {"$limit": limit},  # Add this stage
    ]
    return collection.aggregate(pipeline), suchworte

# Diff ------------------------------------------------
def group_by_field() -> dict:
    pipeline = [
            {   
            '$group': {
                '_id': '$quelle_id', 
                'count': {
                    '$sum': 1
                    }
                }
            }, {
            '$sort': {
                'count': -1
                }
            }
            ]
    result = collection.aggregate(pipeline)
    # transfor into dict
    return_dict = {}
    for item in result:
        return_dict[item['_id']] = item['count']
    return return_dict

def list_fields() -> dict:
    result = collection.find_one()
    return result.keys()

def get_document(id: str) -> dict:
    document = collection.find_one({"id": id})
    return document

def get_system_prompt() -> str:
    result = collection_config.find_one({"key": "systemprompt"})
    return str(result["content"])
    
def update_system_prompt(text: str = ""):
    result = collection_config.update_one({"key": "systemprompt"}, {"$set": {"content": text}})
