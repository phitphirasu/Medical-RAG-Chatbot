# Medical-RAG-Chatbot

A **Retrieval-Augmented Generation (RAG) chatbot** that scrapes [Agnos Health forums](https://www.agnoshealth.com/forums), extracts symptoms and doctor advice, and allows users to get initial guidance from diagnosis history through a **Streamlit interface**.

## Features

- Scrapes forum posts where a doctor has replied.
- Extracts symptoms and doctor advice.
- Stores each posts in a vector database for fast retrieval.
- Chatbot interface via Streamlit.

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/Medical-RAG-Chatbot.git
cd Medical-RAG-Chatbot
```
2. Create and activate a virtual environment:
   
   On Windows:
```bash
python -m venv .venv
.venv\Scripts\activate
```
   On Linux/Mac:
```bash
python -m venv .venv
source .venv/bin/activate
```
3. Install dependencies:
```bash
pip install -r requirements.txt
```
If you don't have Ollama yet

   3.1 download Ollama from https://ollama.com/download

   3.2 download relevant embedding model and LLMs
```bash
ollama pull bge-m3
ollama run scb10x/llama3.1-typhoon2-8b-instruct
```
## Usage
1.Run Streamlit Chatbot
```bash
streamlit run app_chat.py
```
Alternatively, run locally without Streamlit
```bash
python local_chat.py
```





