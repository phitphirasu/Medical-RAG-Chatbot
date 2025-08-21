import requests
from bs4 import BeautifulSoup
import re
import time
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_ollama.llms import OllamaLLM
from langchain.schema import Document

# Initialize 
messages = []  # chat log
retrieved_context = None  # context from first question

while True:
    user_question = input("\nYou: ")
    if user_question.lower() in ["exit", "quit"]:
        print("Exiting chatbot. Goodbye!")
        break

    messages.append({"role": "user", "content": user_question})

    print("\nAssistant is thinking...\n")

    # Web scrape
    if retrieved_context is None:
        BASE_URL = "https://www.agnoshealth.com/forums/search?page={}"
        HEADERS = {"User-Agent": "Mozilla/5.0"}

        all_links = []
        for page in range(1, 2):
            url = BASE_URL.format(page)
            resp = requests.get(url, headers=HEADERS)
            soup = BeautifulSoup(resp.text, "html.parser")
            for a in soup.select("a"):
                href = a.get("href")
                if href and href.startswith("/forums/"):
                    all_links.append("https://www.agnoshealth.com" + href)
            time.sleep(1)

        # Extract forum content
        forum_data = []
        date_pattern = re.compile(r"\d{1,2}/\d{1,2}/\d{2,4}")
        for link in all_links:
            resp = requests.get(link, headers=HEADERS)
            soup = BeautifulSoup(resp.text, "html.parser")
            detail_tag = soup.select_one(".space-y-4")
            detail_text = detail_tag.get_text(separator="\n", strip=True) if detail_tag else ""
            date_match = date_pattern.search(detail_text)
            question = detail_text[:date_match.start()].strip() if date_match else detail_text
            instruction_split = detail_text.split("ชาญ")
            instruction = instruction_split[1].strip() if len(instruction_split) > 1 else ""
            forum_data.append({"question": question, "instruction": instruction})
            time.sleep(1)

        # Create vector DB
        docs = [Document(page_content=f"Question: {f['question']}\nInstruction: {f['instruction']}") 
                for f in forum_data]

        embeddings = OllamaEmbeddings(model="bge-m3")
        vectorstore = Chroma.from_documents(documents=docs, embedding=embeddings)

        retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 1})
        retrieved_docs = retriever.invoke(user_question)

        # Save retrieved context
        retrieved_context = "\n".join([doc.page_content.strip() for doc in retrieved_docs])

    # Build prompt
    latest_question = user_question
    context_text = retrieved_context
    chat_log = "\n".join([f"{m['role'].capitalize()}: {m['content']}" for m in messages[:-1]])

    prompt = f"""
    คุณจะได้รับ 
    1. คำถามล่าสุดของผู้ใช้: {latest_question}
    2. ข้อมูลประวัติการให้คำแนะนำที่มี: {context_text}
    3. ประวัติการสนทนาก่อนหน้า: {chat_log}

    คุณจะต้องตอบคำถามผู้ใช้โดยที่ไม่ต้องบอกว่าได้รับข้อมูลอะไรมาบ้าง ให้ตอบเป็นประโยคเหมือนทั่ว ๆ ไป
    """

    llm = OllamaLLM(model="scb10x/llama3.1-typhoon2-8b-instruct:latest")
    response = llm.invoke(prompt)

    print(f"Assistant: {response}\n")

    messages.append({"role": "assistant", "content": response})
