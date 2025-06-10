import streamlit as st
import requests
from datetime import datetime
import re  # Import the regular expression module
import streamlit.components.v1 as components # Import components

# Eleven Labs widget HTML and JavaScript

webhook_url = st.secrets.get("N8N_WEBHOOK_URL", "")
ELEVEN_LABS_API_KEY = st.secrets.get("ELEVEN_LABS_API_KEY", "")

eleven_labs_widget_html = f"""
<elevenlabs-convai agent-id= {ELEVEN_LABS_API_KEY} ></elevenlabs-convai>
<script src="https://unpkg.com/@elevenlabs/convai-widget-embed" async type="text/javascript"></script>
"""
st.markdown('<div class="main-header"><h1>Hello, How can I help you?</h1></div>', unsafe_allow_html=True)
components.html(eleven_labs_widget_html, height=550) # Adjust height as needed

# Initialize session state variables if they don't exist
if "messages" not in st.session_state:
    st.session_state.messages = []
if "debug_info" not in st.session_state:
    st.session_state.debug_info = ""

# Display all previous chat messages with proper alignment
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if "image_url" in message:
            st.markdown(f'<img src="{message["image_url"]}" width="400">', unsafe_allow_html=True)
            st.markdown(message["content_text"])
        else:
            st.markdown(message["content"])

# Display persistent debug info in an expandable box
# if st.session_state.debug_info:
#     with st.expander("🛠️ Debug Info (Webhook Response)"):
#         st.markdown(st.session_state.debug_info)

# Chat input box for user prompt
prompt = st.chat_input("What would you like to create?")
if prompt:
    # Append user message to session state
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Immediately display user message
    with st.chat_message("user"):
        st.markdown(prompt)

    if webhook_url:
        try:
            # Send POST request to webhook with prompt and timestamp
            response = requests.post(webhook_url, json={
                "message": prompt,
                "timestamp": datetime.now().isoformat()
            })

            # Format debug info nicely with markdown code block
            debug_md = f"""
**Status:** {response.status_code}
**Response text:**
"""
            st.session_state.debug_info = debug_md

            # Process AI response if available
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and len(data) > 0 and "output" in data[0]:
                    ai_response_text = data[0]["output"]

                    # Updated regex to catch URLs inside square brackets
                    url_pattern = re.compile(r'\[(https?:\/\/[^\s\]]+)\]', re.IGNORECASE)
                    match = url_pattern.search(ai_response_text)

                    if match:
                        image_url = match.group(1).strip().replace("\\n", "").replace("\n", "")
                        content_text = ai_response_text.replace(match.group(0), "").strip()

                        # Store both the URL and the cleaned text
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": content_text,
                            "image_url": image_url,
                            "content_text": content_text
                        })
                    else:
                        st.session_state.messages.append({"role": "assistant", "content": ai_response_text})
                else:
                    ai_response_text = "No response from AI."
                    st.session_state.messages.append({"role": "assistant", "content": ai_response_text})
            else:
                st.error(f"Webhook returned status {response.status_code}")
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"Error: Webhook returned status {response.status_code}"
                })
        except Exception as e:
            st.error(f"Failed to send message: {str(e)}")
            st.session_state.messages.append({
                "role": "assistant",
                "content": f"Error: Failed to send message: {str(e)}"
            })
        
        # Refresh app to show AI response
        st.rerun()
