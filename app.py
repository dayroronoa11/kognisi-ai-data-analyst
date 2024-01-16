from openai import OpenAI
import streamlit as st
import time
import re
import pyperclip

hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True) 
TOPIC = [
    {
        "label" : "Data Development (Demo)",
        "file_id" : "file-CBPmRGhA8nx99kMS1OIL2oGC",
        "assistant_id" : "asst_oSVXm87AMrPRGaEsQ3XtCcI4"
    }
]

question_bank = {
    "FileOverview": {
        "question": "Can you provide an overview of the data file, including the number of rows, columns, and data types?",
    },
    "MissingValues": {
        "question": "Are there any missing values in the data file? If so, can you provide a summary?",
    },
    "StatisticalSummary": {
        "question": "Can you provide a statistical summary of the numeric columns in the data file, including mean, median, and standard deviation?",
    },
    "CategoricalSummary": {
        "question": "Can you provide a summary of the categorical columns in the data file, including unique values and their counts?",
    },
    "Correlations": {
        "question": "Can you calculate the correlation coefficients between the numeric columns in the data file?",
    },
    "Outliers": {
        "question": "Are there any outliers in the numeric columns of the data file? If so, can you provide details on their counts and positions?",
    },
    "Normalization": {
        "question": "Do any columns in the data file require normalization or scaling? If so, which method would you recommend and why?",
    },
    "FeatureSelection": {
        "question": "Which features in the data file seem to be the most important or relevant for analysis? Can you provide a ranking or explanation?",
    },
    "DataVisualizations": {
        "question": "What types of data visualizations would be most useful for understanding the patterns and trends in the data file?",
    },
    "TimeSeriesAnalysis": {
        "question": "Is there a time-based component to the data file? If so, can you provide insights on trends, seasonality, or cyclical patterns?",
    },
    "Clustering": {
        "question": "Can you suggest any clustering techniques that might be useful for grouping similar records in the data file?",
    },
    "PredictiveModels": {
        "question": "What predictive modeling techniques would be appropriate for the data file, given its features and the problem you want to solve?",
    },
    "ModelEvaluation": {
        "question": "How would you evaluate the performance of the predictive models trained on the data file?",
    },
    "DataCleaning": {
        "question": "Are there any data quality issues or inconsistencies in the data file that need to be addressed before analysis?",
    },
    "DataTransformation": {
        "question": "Do any columns in the data file require transformation, such as encoding categorical variables or applying mathematical transformations?",
    }
}

def add_chat_to_ui(role, content):
    cm = None
    if role== "assistant":
        cm = st.chat_message(role, avatar="https://img-c.udemycdn.com/user/200_H/220263604_0a69_2.jpg")
    else:
        cm = st.chat_message(role)
    with cm:
        content_splitted = content.split("\n")
        for each_line in content_splitted:
            st.write(each_line)
    
def add_new_message(role, content):
    add_chat_to_ui(role, content)
    st.session_state.messages.append({"role": role, "content": content})

def add_user_response_and_wait_openai(client, thread_id, content="", file_ids=[], assistant_id="", max_attempt = 50):
    client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        file_ids=file_ids,
        content= content
    )
    run = client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=assistant_id
    )

    last_status = "in_progress"
    while last_status != "completed" and max_attempt > 0:
        print("waiting")
        time.sleep(2)
        check = client.beta.threads.runs.retrieve(
            thread_id=thread_id,
            run_id=run.id
        )
        last_status = check.status
        max_attempt -= 1
    if last_status == "completed":
        messages = client.beta.threads.messages.list(
            thread_id=thread_id
        )
        response = messages.data[0].content[0].text.value
        response = re.sub(r"【.*?】", '', response)
        return response
    else:
        print("last_status : {}".format(last_status))
        print(check)
        return "ERROR"
    
def launch_assistant(topic):
    file_id = ""
    assistant_id = ""
    for f in TOPIC:
        if f["label"] == topic:
            file_id = f["file_id"]
            assistant_id = f["assistant_id"]
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    st.title("💬 AI Data Analyst (Kognisi)") 
    
    if "messages" not in st.session_state:
        thread = client.beta.threads.create()
        st.session_state["thread_id"] = thread.id
        st.session_state["messages"] = []
        add_new_message("assistant", "Hallo! Apakah ada yang bisa saya bantu?")
    else:
        for msg in st.session_state.messages:
            add_chat_to_ui(msg["role"], msg["content"])
    if prompt := st.chat_input():
        add_new_message("user", prompt)
        response = add_user_response_and_wait_openai(client, st.session_state["thread_id"], prompt, file_ids=[file_id], assistant_id=assistant_id)
        add_new_message("assistant", response)
    
topic_input = ""
with st.sidebar:
    topic_input = st.selectbox("Topic to test", key="topic", options=[a["label"] for a in TOPIC])
    st.markdown("Example prompt [Source](https://github.com/cameronjoejones/streamlit-gpt-data-assistant/blob/main/question_bank.py)")
    for k, question in question_bank.items():
        if st.button(k):
            pyperclip.copy(question["question"])
            st.success('Text copied successfully!')
    st.markdown("""
    Other Examples:
    - [ChatGPT Data Science Prompt](https://github.com/travistangvh/ChatGPT-Data-Science-Prompts)
    - [Accelerate Your Data Science Skills with These Ultimate ChatGPT Prompts](https://www.learnprompt.org/chat-gpt-prompts-for-data-science/)""")
if topic_input != "":
    if "request_id" in st.session_state:
        if topic_input != st.session_state["topic"]:
            print("RESETTING MESSAGES AND THREADS")
            del st.session_state["messages"]
            del st.session_state["thread_id"]
    launch_assistant(topic_input)
else:
    st.write("Add Topic you want to learn...")