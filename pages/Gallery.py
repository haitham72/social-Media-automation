import streamlit as st
import pandas as pd
import requests
from PIL import Image
import io
import plotly.express as px
from datetime import datetime
import re
import hashlib
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import base64
from urllib.parse import urlparse

# Configure page
st.set_page_config(
    page_title="AI Gallery",
    page_icon="🖼️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize theme in session state
if 'theme' not in st.session_state:
    st.session_state.theme = 'light'

# Theme toggle function
def toggle_theme():
    st.session_state.theme = 'light' if st.session_state.theme == 'dark' else 'dark'

# Dynamic CSS based on theme
# Dynamic CSS based on theme
def get_theme_css():
    if st.session_state.theme == 'dark':
        return """
        <style>
            .main-header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 1rem;
                border-radius: 10px;
                margin-bottom: 2rem;
                color: white;
                text-align: center; /* Center header text */
            }
            .theme-toggle {
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 1000;
                background: #667eea;
                color: white;
                border: none;
                padding: 0.5rem 1rem;
                border-radius: 20px;
                cursor: pointer;
                font-size: 0.9rem;
                transition: all 0.3s ease;
            }
            .theme-toggle:hover {
                background: #764ba2;
                transform: scale(1.05);
            }
            .image-card {
                position: relative;
                border-radius: 15px;
                overflow: hidden;
                margin-bottom: 1.5rem;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
                transition: transform 0.3s ease, box-shadow 0.3s ease;
                background: linear-gradient(145deg, #1e1e2e, #2d2d3a);
            }
            .image-card:hover {
                transform: translateY(-5px);
                box-shadow: 0 12px 40px rgba(103, 126, 234, 0.4);
            }

            .image-overlay {
                position: absolute;
                bottom: 0;
                left: 0;
                right: 0;
                background: linear-gradient(transparent, rgba(0,0,0,0.8));
                color: white;
                padding: 1rem;
                transform: translateY(100%);
                transition: transform 0.3s ease;
            }
            .image-card:hover .image-overlay {
                transform: translateY(0);
            }
            .image-title {
                font-size: 1.1rem;
                font-weight: bold;
                margin-bottom: 0.5rem;
                color: #ffffff;
            }
            .image-description {
                font-size: 0.9rem;
                color: #cccccc;
                margin-bottom: 0.8rem;
                line-height: 1.4;
            }
            .video-container {
                width: 100%;
                aspect-ratio: 16 / 9;
                margin: 1rem 0;
                background: linear-gradient(145deg, #1e1e2e, #2d2d3a);
                border-radius: 15px;
                overflow: hidden;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            }
            .video-container video {
                width: 100%;
                height: 100%;
                object-fit: cover;
                border-radius: 10px;
            }
            .stApp {
                background: linear-gradient(180deg, #0f0f23 0%, #1a1a2e 100%);
            }
            .stTabs [data-baseweb="tab-list"] {
                background: rgba(30, 30, 46, 0.8);
                border-radius: 10px;
                padding: 0.5rem;
            }
            .stTabs [data-baseweb="tab"] {
                background: transparent;
                color: #cccccc;
                border-radius: 8px;
            }
            .stTabs [aria-selected="true"] {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }

            /* CSS for the "Enter your image prompt" input box in dark theme */
            .stTextInput > div > div > input[type="text"] {
                background-color: #28283a; /* Darker background */
                color: #ffffff; /* White text */
                border: 1px solid #667eea; /* Border color */
                border-radius: 8px;
                padding: 0.75rem 1rem;
            }
            .stTextInput > div > div > input[type="text"]:focus {
                border-color: #764ba2; /* Highlight border on focus */
                box-shadow: 0 0 0 0.1rem rgba(118, 75, 162, 0.25);
            }
        </style>
        """
    else:
        return """
        <style>
            .main-header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 1rem;
                border-radius: 10px;
                margin-bottom: 2rem;
                color: white;
                text-align: center; /* Center header text */
            }
            .theme-toggle {
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 1000;
                background: #667eea;
                color: white;
                border: none;
                padding: 0.5rem 1rem;
                border-radius: 20px;
                cursor: pointer;
                font-size: 0.9rem;
                transition: all 0.3s ease;
            }
            .theme-toggle:hover {
                background: #764ba2;
                transform: scale(1.05);
            }
            .image-card {
                position: relative;
                border-radius: 15px;
                overflow: hidden;
                margin-bottom: 1.5rem;
                box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
                transition: transform 0.3s ease, box-shadow 0.3s ease;
                background: linear-gradient(145deg, #ffffff, #f0f0f0);
            }
            .image-card:hover {
                transform: translateY(-5px);
                box-shadow: 0 8px 24px rgba(103, 126, 234, 0.3);
            }
            .image-container {
                position: relative;
                width: 100%;
                height: 350px;
                overflow: hidden;
            }
            .image-overlay {
                position: absolute;
                bottom: 0;
                left: 0;
                right: 0;
                background: linear-gradient(transparent, rgba(0,0,0,0.7));
                color: white;
                padding: 1rem;
                transform: translateY(100%);
                transition: transform 0.3s ease;
            }
            .image-card:hover .image-overlay {
                transform: translateY(0);
            }
            .image-title {
                font-size: 1.1rem;
                font-weight: bold;
                margin-bottom: 0.5rem;
                color: #ffffff;
            }
            .image-description {
                font-size: 0.9rem;
                color: #cccccc;
                margin-bottom: 0.8rem;
                line-height: 1.4;
            }
            .stApp {
                background: linear-gradient(180deg, #f8f9fa 0%, #e9ecef 100%);
            }
            .stTabs [data-baseweb="tab-list"] {
                background: rgba(255, 255, 255, 0.9);
                border-radius: 10px;
                padding: 0.5rem;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
            }
            .stTabs [data-baseweb="tab"] {
                background: transparent;
                color: #333333;
                border-radius: 8px;
            }
            .stTabs [aria-selected="true"] {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }

            /* CSS for the "Enter your image prompt" input box in light theme */
            .stTextInput > div > div > input[type="text"] {
                background-color: #f0f2f6; /* Light background */
                color: #333333; /* Dark text */
                border: 1px solid #ced4da; /* Border color */
                border-radius: 8px;
                padding: 0.75rem 1rem;
            }
            .stTextInput > div > div > input[type="text"]:focus {
                border-color: #667eea; /* Highlight border on focus */
                box-shadow: 0 0 0 0.1rem rgba(102, 126, 234, 0.25);
            }
        </style>
        """

# Apply theme CSS
st.markdown(get_theme_css(), unsafe_allow_html=True)

# Theme toggle button
theme_icon = "🌙" if st.session_state.theme == 'light' else "☀️"

# Hidden button for theme toggle functionality
if st.button(theme_icon, key="theme_toggle", help="Toggle theme"):
    toggle_theme()
    st.rerun()

# Constants for video handling
CACHE_DIR = "cached_videos"
os.makedirs(CACHE_DIR, exist_ok=True)

# Video Gallery Functions
def get_drive_file_id(url):
    """Extract Google Drive file ID from URL"""
    parsed = urlparse(url)
    parts = parsed.path.split('/')
    if 'file' in parts and 'd' in parts:
        return parts[parts.index('d') + 1]
    return None

def download_video(file_id):
    """Download and cache video from Google Drive"""
    dest_path = os.path.join(CACHE_DIR, f"{file_id}.mp4")
    if os.path.exists(dest_path):
        return dest_path

    download_url = f"https://drive.google.com/uc?export=download&id={file_id}"
    with requests.get(download_url, stream=True) as r:
        if r.status_code == 200:
            with open(dest_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
            return dest_path
        return None

@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_and_resize_image(image_url, max_size=(600, 400)):
    """Load and resize image with caching"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(image_url, timeout=10, headers=headers)
        response.raise_for_status()
        if 'image' in response.headers.get('content-type', '').lower():
            img = Image.open(io.BytesIO(response.content))
            # Convert to RGB if necessary
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')
            # Resize while maintaining aspect ratio
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            # Convert back to bytes for caching
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='JPEG', quality=85, optimize=True)
            img_byte_arr.seek(0)
            return img_byte_arr.getvalue(), True, None
        else:
            return None, False, f"Not an image: {response.headers.get('content-type', 'unknown')}"
    except Exception as e:
        return None, False, str(e)

def load_images_batch(image_data_list, max_workers=5):
    """Load multiple images concurrently"""
    results = {}
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all image loading tasks
        future_to_idx = {
            executor.submit(load_and_resize_image, data['url']): data['idx']
            for data in image_data_list if data['url']
        }
        # Collect results as they complete
        for future in as_completed(future_to_idx):
            idx = future_to_idx[future]
            try:
                img_bytes, success, error = future.result()
                results[idx] = {
                    'img_bytes': img_bytes,
                    'success': success,
                    'error': error
                }
            except Exception as e:
                results[idx] = {
                    'img_bytes': None,
                    'success': False,
                    'error': str(e)
                }
    return results

def clean_text_for_display(text):
    """Clean text to prevent markdown parsing issues"""
    if pd.isna(text) or text is None:
        return "N/A"
    # Convert to string and clean
    text = str(text)
    # Remove or escape problematic characters that break markdown
    text = re.sub(r'[^\w\s\-.,!?()[\]{}:;"\']', '', text)
    # Limit length to prevent very long strings
    if len(text) > 200:
        text = text[:200] + "..."
    return text

def safe_load_csv(url):
    """Safely load CSV with error handling"""
    try:
        # Convert Google Sheets URL format if needed
        if 'docs.google.com/spreadsheets' in url and '/edit' in url:
            # Extract the spreadsheet ID
            if '/d/' in url:
                sheet_id = url.split('/d/')[1].split('/')[0]
                url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
        # Try different encoding options
        for encoding in ['utf-8', 'latin-1', 'cp1252']:
            try:
                df = pd.read_csv(
                    url,
                    encoding=encoding,
                    quotechar='"',
                    escapechar='\\',
                    skipinitialspace=True,
                    on_bad_lines='skip',
                    dtype=str  # Force all columns to string to avoid type issues
                )
                # Clean column names (remove extra spaces and special characters)
                df = df.iloc[::-1]

                df.columns = df.columns.str.strip()
                # Remove completely empty rows
                df = df.dropna(how='all')

                # Clean all text data (but keep original for URLs)
                text_columns = []
                for col in df.columns:
                    if col.lower() not in ['url', 'link', 'image_url', 'imageurl', 'freepic']: # Added 'freepic'
                        text_columns.append(col)
                for col in text_columns:
                    if df[col].dtype == 'object':
                        df[col] = df[col].apply(clean_text_for_display)
                return df
            except UnicodeDecodeError:
                continue
        # If all encodings fail, return empty dataframe
        st.error("❌ Failed to decode CSV with any encoding")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"❌ Error loading CSV: {str(e)}")
        return pd.DataFrame()

def send_to_webhook(description, image_ref=None, is_image_request=False): # Changed 'url' to 'image_ref'
    webhook_url = st.secrets.get("N8N_WEBHOOK_URL", "")
    if webhook_url:
        try:
            if is_image_request:
                message = f"create an image of {description}"
                payload = {
                    "message": message,
                    "type": "image_request",
                    "timestamp": datetime.now().isoformat()
                }
                st.info(f"Sending image generation request: {message}")
            else: # This is for "Create a video" button
                message = f"create a video of {description}"
                if image_ref: # Use image_ref (which will be FreePic)
                    message += f", here is the image {image_ref}"
                payload = {
                    "message": message,
                    "type": "video_creation_request", # Changed type for clarity
                    "timestamp": datetime.now().isoformat()
                }
                # st.info(f"Sending video creation request: {message}")

            response = requests.post(webhook_url, json=payload)
            if response.status_code == 200:
                st.success("✅ Request sent to webhook successfully!")
            else:
                st.error(f"Webhook returned error: {response.status_code} - {response.text}")
        except Exception as e:
            st.error(f"❌ Failed to send to webhook: {str(e)}")
    else:
        st.warning("⚠️ No N8N webhook URL configured in secrets.")


def image_gallery():
    # --- Generate New Image Section (Moved to Top) ---
    st.subheader("Generate New Image")
    prompt = st.text_input("Enter your image prompt:", key="new_image_prompt")
    if st.button("Generate Image", key="generate_image_button"):
        if prompt:
            send_to_webhook(prompt, is_image_request=True)
            st.session_state["new_image_prompt_value"] = "" # Clear input after sending
            st.rerun() # Rerun to clear the input field and show success message
        else:
            st.warning("Please enter a prompt to generate an image.")
    st.markdown("---") # Separator


    images_url = st.secrets.get("IMAGES_GOOGLE_SHEET_URL", "")
    if not images_url:
        st.error("❌ No IMAGES_GOOGLE_SHEET_URL found in secrets")
        return

    with st.spinner('Loading gallery...'):
        df = safe_load_csv(images_url)

    if df.empty:
        st.error("❌ No data loaded from CSV")
        return

    if 'createdDate' in df.columns:
        df = df.sort_values(by='createdDate', ascending=False)

    image_data_list = []
    for idx, row in df.iterrows():
        possible_url_columns = ['URL', 'url', 'Url', 'image_url', 'imageUrl', 'link', 'Link']
        image_url = next((str(row[col]).strip() for col in possible_url_columns if col in row and str(row[col]).strip() and str(row[col]) != 'N/A'), None)
        
        # Get the 'FreePic' value
        freepic_value = clean_text_for_display(row.get('URL', '')) # Safely get FreePic

        if image_url:
            image_data_list.append({
                'idx': idx,
                'url': image_url,
                'name': clean_text_for_display(row.get('name', row.get('Name', f'Image {idx+1}'))),
                'desc': clean_text_for_display(row.get('description', row.get('Description', 'No description'))),
                'URL': freepic_value # Add freepic to the data list
            })

    if not image_data_list:
        st.warning("⚠️ No valid image URLs found in the data")
        return

    with st.spinner(f'Loading {len(image_data_list)} images...'):
        image_results = load_images_batch(image_data_list)

    cols = st.columns(4)
    images_displayed = 0

    for i, data in enumerate(image_data_list):
        idx = data['idx']
        col = cols[i % 4]

        with col:
            if idx in image_results and image_results[idx]['success']:
                img_bytes = image_results[idx]['img_bytes']
                encoded_img = base64.b64encode(img_bytes).decode()
                st.markdown(f"""
                <div class="image-card">
                    <div class="image-container">
                        <img src="data:image/jpeg;base64,{encoded_img}" style="width:100%; height:350px; object-fit:cover;" />
                        <div class="image-overlay">
                            <div class="image-title">{data['name']}</div>
                            <div class="image-description">{data['desc']}</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # "Create a video" button
                if st.button("Create a video", key=f"view_{idx}"):
                    send_to_webhook(data['desc'], data['URL']) # Pass data['freepic']
                images_displayed += 1
            else:
                error_msg = image_results.get(idx, {}).get('error', 'Unknown error')
                error_bg = "#2d1b1b" if st.session_state.theme == 'dark' else "#f8d7da"
                st.markdown(f"""
                <div class="image-card" style="background: {error_bg};">
                    <div style="padding: 1rem; text-align: center;">
                        <div class="image-title">❌ {data['name']}</div>
                        <div class="image-description">{data['desc']}</div>
                        <div style="color: #ff6b6b; font-size: 0.8rem; margin-top: 0.5rem;">
                            Error: {error_msg[:50]}...
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)


def video_gallery():
    videos_url = st.secrets.get("VIDEOS_GOOGLE_SHEET_URL", "")
    if not videos_url:
        st.error("❌ No VIDEOS_GOOGLE_SHEET_URL found in secrets")
        return

    selected_cols=4

    with st.spinner('Loading video gallery...'):
        df = safe_load_csv(videos_url)
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')

        # Drop rows with invalid or missing dates
        df = df.dropna(subset=['Date'])

        # Sort by date, newest first
        df = df.sort_values(by='Date', ascending=False)


    if df.empty:
        st.warning("No video data available.")
        return

    # Display videos
    cols = st.columns(selected_cols)
    for idx, row in df.iterrows():
        name = clean_text_for_display(row.get("name"))
        description = clean_text_for_display(row.get("description"))
        url = row.get("url")

        # Try to fix Google Drive URLs
        file_id = get_drive_file_id(url)

        if file_id:
            video_path = download_video(file_id)
            if video_path:
                with cols[idx % selected_cols]:
                    # st.markdown(f"<div class='video-container'>", unsafe_allow_html=True)
                    st.markdown(f"### {name}")
                    st.markdown(description)
                    st.video(video_path)
                    st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.warning(f"⚠️ Couldn't download video for ID: {file_id}")
        else:
            with cols[idx % selected_cols]:
                # st.markdown(f"<div class='video-container'>", unsafe_allow_html=True)
                st.markdown(f"## {name}")
                st.markdown(description)
                try:
                    st.video(url)
                except:
                    st.error("Invalid video URL")
                st.markdown("</div>", unsafe_allow_html=True)


def main():
    # st.markdown('<div class="main-header"><h1>🖼️ AI Gallery</h1></div>', unsafe_allow_html=True)

    # Gallery tabs
    tab1, tab2 = st.tabs(["🖼️ Images", "🎥 Videos"])

    with tab1:
        image_gallery()

    with tab2:
        video_gallery()

if __name__ == "__main__":
    main()