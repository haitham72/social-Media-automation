import streamlit as st
import requests
from datetime import datetime
import re
import streamlit.components.v1 as components
import google.generativeai as genai
import json
import os
from PIL import Image
import hashlib
# hi

N8N_WEBHOOK_URL = "https://ihisam74.app.n8n.cloud/webhook/a6820b65-76cf-402b-a934-0f836dee6ba0/chat"
ELEVEN_LABS_API_KEY = "agent_01jvft97waft7rgnwh806ksk7q"
GEMINI_API_KEY = "AIzaSyBe0r45CcxVSjedLuPEaupGwR4yQunEl5c"

def download_and_display_drive_image(file_id, caption="Generated Image"):
    download_url = f"https://drive.google.com/uc?id={file_id}&export=download"
    image_path = f"/tmp/{file_id}.jpg"

    # Download the image
    response = requests.get(download_url)
    if response.status_code == 200:
        with open(image_path, "wb") as f:
            f.write(response.content)

        # Display with 50% size
        img = Image.open(image_path)
        st.image(img, caption=caption, width=img.width // 2)
        return image_path
    else:
        st.warning("Failed to download image.")
        return None

def unique_key_for_url(url, index):
    key_base = f"{url}_{index}"
    return "create_video_" + hashlib.md5(key_base.encode()).hexdigest()

st.set_page_config(
    page_title="AI assistant",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="expanded"
)

st.image("icons/banner.gif", use_container_width=True)

image_paths = [
    "icons/baby.jpg",
    "icons/batman.gif",
    "icons/assisstant.gif",
    "icons/Deep_research.gif",
]

columns_dynamic = st.columns(len(image_paths))

for i, image_path in enumerate(image_paths):
    with columns_dynamic[i]:
        st.image(image_path, use_container_width=True, width=250)

# Configure Gemini
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.0-flash-exp')

eleven_labs_widget_html = f"""
<elevenlabs-convai agent-id= {ELEVEN_LABS_API_KEY} ></elevenlabs-convai>
<script src="https://unpkg.com/@elevenlabs/convai-widget-embed" async type="text/javascript"></script>
"""

st.markdown('<div class="main-header"><h1>Hello, How can I help you?</h1></div>', unsafe_allow_html=True)
components.html(eleven_labs_widget_html, height=330)

SYSTEM_PROMPT = """
You are **Haitham**, an intelligent AI assistant. You can help with general questions and conversations, but you have special capabilities for specific tasks through automation tools.

### 🎯 CORE PRINCIPLES
* Answer any question naturally and helpfully
* Speak in the user's language (English, Hindi, Arabic)
* Be conversational and friendly
* Only mention special automation capabilities when relevant

### 🛠️ SPECIAL AUTOMATION CAPABILITIES
When users ask for these specific tasks, let them know you can help with automation:

**Content Creation:**
- "create image of..." → Image generation
- "create video of..." → Video creation, if the user wants to create a video of the image, send back to webhook 'create a video of of the previously generated image url'
- "YouTube video/post about..." → YouTube content creation

**Communication:**
- Send/read/reply emails → Email automation
- Get/update/add contacts → Contact management

**Research & Information:**
- "Research [topic]" → Deep research
- "Search for [topic]" → Quick search
- YouTube URL analysis → Video transcription

**Live Support:**
- "Call agent" → Live assistance

### 📋 RESPONSE GUIDELINES
* Be natural and conversational
* For automation tasks, confirm what you understand and that you'll process it
* Use simple, clear language
* Don't overwhelm with technical details
* Be helpful for both general chat and specific automation requests

- video creation output:
- do not give output like this:
"ok i have created a video for you here is the link <a href="https://drive.google.com/uc?id=1WCHkvU1WyIZFxTm_SLMGKGnzIxZUVSr2&export=download">download</a> would you like to continue the demo?\n"
- instead give output direct url like this:
"i have created a video for you here is the link https://drive.google.com/uc?id=1WCHkvU1WyIZFxTm_SLMGKGnzIxZUVSr2&export=download"
- never ask for describtion of the video, just immediatly pass it to createVideo tool

"""

TASK_TRIGGERS = {
    'createimages': ['create image', 'generate image', 'make image', 'image of'],
    'createVideo': ['create video', 'generate video', 'make video', 'video of'],
    'createPost': ['youtube video', 'youtube post', 'create youtube', 'youtube about'],
    'emailAgent': ['send email', 'read email', 'reply email', 'check inbox', 'email'],
    'contactAgent': ['add contact', 'get contact', 'update contact', 'contact'],
    'DeepResearch': ['research', 'deep research'],
    'Tavily': ['search for', 'quick search'],
    'callAgent': ['call agent', 'live help', 'call support'],
    'youtub_transcribe': ['youtube.com', 'youtu.be']
}

def detect_automation_task(message):
    message_lower = message.lower()
    for tool, triggers in TASK_TRIGGERS.items():
        for trigger in triggers:
            if trigger in message_lower:
                return tool
    return None

def send_to_n8n_webhook(message, task_type):
    if not N8N_WEBHOOK_URL:
        return None, "Webhook URL not configured"
    try:
        response = requests.post(N8N_WEBHOOK_URL, json={
            "message": message,
            "task_type": task_type,
            "timestamp": datetime.now().isoformat()
        })
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and len(data) > 0 and "output" in data[0]:
                return data[0]["output"], None
            else:
                return data, None
        else:
            return None, f"Webhook returned status {response.status_code}"
    except Exception as e:
        return None, f"Failed to send to webhook: {str(e)}"

def extract_and_convert_drive_link(text):
    file_id_match = re.search(r'id=([a-zA-Z0-9_-]{10,})', text)
    
    if file_id_match:
        file_id = file_id_match.group(1)
        image_url = f"https://drive.google.com/uc?id={file_id}&export=view"
        
        clean_text = re.sub(r'<a href=[\'"].*?[\'"].*?>.*?</a>', '', text)  # Remove HTML link
        clean_text = re.sub(r'https?://drive\.google\.com/\S+', '', clean_text)  # Remove raw URL
        clean_text = clean_text.strip()

        return image_url, clean_text

    return None, text.strip()

def extract_file_id_from_response(text):
    match = re.search(r'id=([a-zA-Z0-9_-]{10,})', text)
    return match.group(1) if match else None

def get_gemini_response(message, conversation_history):
    if not GEMINI_API_KEY:
        return "Gemini API key not configured"
    try:
        context = SYSTEM_PROMPT + "\n\nConversation history:\n"
        for msg in conversation_history[-5:]:
            context += f"{msg['role']}: {msg['content']}\n"
        context += f"\nUser: {message}\nAssistant:"
        response = model.generate_content(context)
        return response.text
    except Exception as e:
        return f"Error getting Gemini response: {str(e)}"

if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_generated_image_url" not in st.session_state:
    st.session_state.last_generated_image_url = ""

for i, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        if "image_url" in message:
            try:
                img = Image.open(message["image_url"])
                st.image(img, caption=message.get("content_text", ""), width=img.width // 2)
            except:
                st.image(message["image_url"], caption=message.get("content_text", ""), use_container_width=True)

            # Add "Create a video" button under each assistant image
            if message["role"] == "assistant":
                video_url = st.session_state.get("last_generated_image_url", None)
                if video_url:
                    btn_key = unique_key_for_url(video_url, i)
                    if st.button("Create a video", key=btn_key):
                        video_message = f"create a video of {video_url}"
                        with st.chat_message("assistant"):
                            with st.spinner("Sending video creation request..."):
                                response, error = send_to_n8n_webhook(video_message, "createVideo")
                                if error:
                                    st.error(f"Error: {error}")
                                    st.session_state.messages.append({"role": "assistant", "content": f"Error sending video request: {error}"})
                                else:
                                    st.success("Video creation request sent!")
                                    st.session_state.messages.append({"role": "assistant", "content": response or "Video request sent."})
                        st.rerun()
        else:
            st.markdown(message["content"])

prompt = st.chat_input("What would you like to create or ask?")
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    automation_task = detect_automation_task(prompt)
    if automation_task and N8N_WEBHOOK_URL:
        with st.chat_message("assistant"):
            with st.spinner("Processing your automation request..."):
                webhook_response, error = send_to_n8n_webhook(prompt, automation_task)
                if error:
                    response_text = f"I understand you want help with '{automation_task}', but there was an issue: {error}"
                    st.markdown(response_text)
                    st.session_state.messages.append({"role": "assistant", "content": response_text})
                else:
                    if isinstance(webhook_response, str):
                        image_url, clean_text = extract_and_convert_drive_link(webhook_response)
                        if image_url:
                            file_id = extract_file_id_from_response(webhook_response)
                            if file_id:
                                local_path = download_and_display_drive_image(file_id, caption=clean_text or "Generated Image")

                                # Store original drive URL in session for video creation use
                                st.session_state.last_generated_image_url = image_url

                                st.session_state.messages.append({
                                    "role": "assistant",
                                    "content": clean_text,
                                    "image_url": local_path,  # Local path for display
                                    "content_text": clean_text
                                })

                        else:
                            st.markdown(webhook_response)
                            st.session_state.messages.append({"role": "assistant", "content": webhook_response})
                    else:
                        response_text = str(webhook_response)
                        st.markdown(response_text)
                        st.session_state.messages.append({"role": "assistant", "content": response_text})
    else:
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                gemini_response = get_gemini_response(prompt, st.session_state.messages)
                st.markdown(gemini_response)
                st.session_state.messages.append({"role": "assistant", "content": gemini_response})
    st.rerun()
