import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import time
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_ollama.llms import OllamaLLM
from langchain.schema import Document

st.title("Agnos ผู้ช่วยทางการแพทย์ของคุณ")

# Initialize states
if "messages" not in st.session_state:
    st.session_state.messages = []
if "retrieved_context" not in st.session_state:
    st.session_state.retrieved_context = None

# Display previous chat
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# User input
if user_question := st.chat_input("ถามคำถามที่ท่านต้องการทราบ...."): #ทำงานเมื่อมี input

    # Save user input
    st.session_state.messages.append({"role": "user", "content": user_question})
    with st.chat_message("user"):
        st.markdown(user_question)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):

            # Web Scrape ในกรณีที่ยังไม่มี First query
            if st.session_state.retrieved_context is None: #กรณียังไม่มีการ Query (ไม่มี chat log)(เป็นคำถามแรก)
                BASE_URL = "https://www.agnoshealth.com/forums/search?page={}"
                HEADERS = {"User-Agent": "Mozilla/5.0"}

                all_links = []
                for page in range(1, 2): #ปรับ range ตามจำนวน page ที่จะทำการ scraping ได้
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
                    detail_text = detail_tag.get_text(separator="\n", strip=True) if detail_tag else "" #เอาข้อมูลที่อยู่ใน class = 'space-y-4'
                    date_match = date_pattern.search(detail_text) #return RegEx Match Object
                    question = detail_text[:date_match.start()].strip() if date_match else detail_text #text[start:first match position]
                    instruction_split = detail_text.split("ชาญ")
                    instruction = instruction_split[1].strip() if len(instruction_split) > 1 else "" #text หลังคำว่า 'ชาญ' ให้เป็น instruction
                    forum_data.append({"question": question, "instruction": instruction})
                    time.sleep(1)

                # Create vector DB
                docs = [Document(page_content=f"Question: {f['question']}\nInstruction: {f['instruction']}") 
                        for f in forum_data]

                embeddings = OllamaEmbeddings(model="bge-m3")
                vectorstore = Chroma.from_documents(documents=docs, embedding=embeddings)

                retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 1})
                retrieved_docs = retriever.invoke(user_question)

                # Save retrieved context to session state
                st.session_state.retrieved_context = "\n".join([doc.page_content.strip() for doc in retrieved_docs])

            # Build prompt
            latest_question = user_question
            context_text = st.session_state.retrieved_context
            chat_log = "\n".join(
                [f"{m['role'].capitalize()}: {m['content']}" for m in st.session_state.messages[:-1]]
            )
            # print("Latest Question:", latest_question)
            # print("Context:", context_text)
            # print("Chat Log:", chat_log)


            llm = OllamaLLM(model="scb10x/llama3.1-typhoon2-8b-instruct:latest")
            response = llm.invoke(f"""
            คุณจะได้รับ 
            1.คำถามซึ่งผู้ใช้จะถามคุณ 
            2.คุณจะได้ข้อมูลซึ่งเป็นประวัติการให้คำแนะนำโดยแพทย์ผู้เชี่ยวชาญโดยชุดข้อมูลที่คุณจะได้นั้นจะมี 'question' ซึ่งเป็นคำถามโดยผู้ป่วย และ 'instruction' ซึ่งเป็นการให้คำแนะนำของแพทย์
            3.คุณจะได้ประวัติการสนทนาก่อนหน้า(ถ้ามี)
            คำถามที่ผู้ใช้ถาม: {latest_question}
            ข้อมูลประวัติการให้คำแนะนำที่มี: {context_text}
            ประวัติการสนทนาก่อนหน้า: {chat_log}
            คุณจะต้องตอบคำถามผู้ใช้โดยที่ไม่ต้องบอกว่าได้รับข้อมูลอะไรมาบ้าง ให้ตอบเป็นประโยคเหมือนทั่ว ๆ ไป
            """)

            st.markdown(response)

    # Save assistant reply
    st.session_state.messages.append({"role": "assistant", "content": response})
