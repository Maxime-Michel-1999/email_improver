import streamlit as st
import os
import random
from groq import Groq
import gspread
from google.oauth2.service_account import Credentials

# Configure Streamlit page
st.set_page_config(layout="wide", initial_sidebar_state="collapsed", menu_items=None)


# Configure API credentials from Streamlit secrets
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
GOOGLE_SHEETS_CREDENTIALS = {
    "type": st.secrets["type"],
    "project_id": st.secrets["project_id"],
    "private_key_id": st.secrets["private_key_id"],
    "private_key": st.secrets["private_key"],
    "client_email": st.secrets["client_email"],
    "client_id": st.secrets["client_id"],
    "auth_uri": st.secrets["auth_uri"],
    "token_uri": st.secrets["token_uri"],
    "auth_provider_x509_cert_url": st.secrets["auth_provider_x509_cert_url"],
    "client_x509_cert_url": st.secrets["client_x509_cert_url"],
    "universe_domain": st.secrets["universe_domain"],
    "sheet_url": st.secrets["sheet_url"]
}

client = Groq(api_key=GROQ_API_KEY)

# Custom CSS
st.markdown("""
<style>
    .main {
        padding: 2rem;
        max-width: 1200px;
        margin: 1rem auto;
    }
    .stTextArea textarea {
        border-radius: 8px;
        border: 1px solid #ddd;
        padding: 12px;
    }
    .stButton button {
        width: 100%;
        border-radius: 8px;
        padding: 8px 16px;
        background-color: #4CAF50;
        color: white;
        border: none;
    }
    .stButton button:hover {
        background-color: #45a049;
    }
    .success-msg {
        color: #4CAF50;
        padding: 8px;
        border-radius: 4px;
        margin: 8px 0;
    }
    .error-msg {
        color: #f44336;
        padding: 8px;
        border-radius: 4px;
        margin: 8px 0;
    }
    .block-container {
        padding-top: 1rem;
        padding-left: 5rem;
        padding-right: 5rem;
    }
</style>
""", unsafe_allow_html=True)


# Available models
MODELS = [
    "gemma2-9b-it",
    "llama3-70b-8192", 
    "llama3-8b-8192",
    "mixtral-8x7b-32768"
]

def get_random_models():
    """Get two different random models from the available models list."""
    selected = random.sample(MODELS, 2)
    return selected[0], selected[1]

def get_improved_email(email_text, model, temperature):
    """Generate improved email using specified model and temperature."""
    response = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant that improves email writing. Only return the improved email text, no other text, no subject."
            },
            {
                "role": "user", 
                "content": f"Please improve this email text: {email_text}"
            }
        ],
        model=model,
        temperature=temperature,
    )
    return response.choices[0].message.content

def get_llm_responses(email_text):
    """Get two different improved versions of the email text using different models."""
    model1, model2 = get_random_models()
    
    # First LLM response
    suggestion1 = get_improved_email(email_text, model1, 0.7)
    
    # Second LLM response with different temperature
    suggestion2 = get_improved_email(email_text, model2, 0.9)
    
    return suggestion1, suggestion2, model1, model2

def save_email_data(email_input, suggestion1, suggestion2, model1, model2):
    """Save the email input and generated outputs to Google Sheets."""
    

    # Define the scope for the APIs
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 
              'https://www.googleapis.com/auth/drive']
    

    # Authenticate and authorize
    credentials = Credentials.from_service_account_info(GOOGLE_SHEETS_CREDENTIALS, scopes=SCOPES)
    gc = gspread.authorize(credentials)

    # Open the Google Sheet by URL or name
    sheet = gc.open_by_url(GOOGLE_SHEETS_CREDENTIALS["sheet_url"])

    # Get the first worksheet
    worksheet = sheet.get_worksheet(0)

    # Write headers if sheet is empty
    if not worksheet.get_all_values():
        headers = ['Input', 'Output A', 'Output B', 'Model A', 'Model B']
        worksheet.append_row(headers)

    # Write the email data to the next available row
    next_row = len(worksheet.get_all_values()) + 1
    worksheet.append_row([
        email_input,
        suggestion1, 
        suggestion2,
        model1,
        model2
    ])

# Streamlit UI
st.title("✉️ Email Improvement Assistant")

# Input text area for email
email_input = st.text_area("Enter your email text:", height=100, placeholder="Type or paste your email here...")

if st.button("✨ Get Suggestions"):
    if email_input:
        with st.spinner("🔄 Generating suggestions..."):
            suggestion1, suggestion2, model1, model2 = get_llm_responses(email_input)
            
            # Store suggestions in session state
            st.session_state.suggestion1 = suggestion1
            st.session_state.suggestion2 = suggestion2
            st.session_state.model1 = model1
            st.session_state.model2 = model2
            
            save_email_data(email_input, suggestion1, suggestion2, model1, model2)
            
    else:
        st.markdown("<p class='error-msg'>❌ Please enter some email text first!</p>", unsafe_allow_html=True)

# Display suggestions if they exist in session state
if 'suggestion1' in st.session_state and 'suggestion2' in st.session_state:
    st.subheader("📝 Choose your preferred version:")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.text_area("Version 1:", value=st.session_state.suggestion1, height=200, key="sug1")
        st.caption(f"🤖 Generated using {st.session_state.model1}")
        if st.button("Choose Version 1"):
            st.session_state.selected = st.session_state.suggestion1
            st.markdown("<p class='success-msg'>✅ Version 1 selected!</p>", unsafe_allow_html=True)
            
    with col2:
        st.text_area("Version 2:", value=st.session_state.suggestion2, height=200, key="sug2")
        st.caption(f"🤖 Generated using {st.session_state.model2}")
        if st.button("Choose Version 2"):
            st.session_state.selected = st.session_state.suggestion2
            st.markdown("<p class='success-msg'>✅ Version 2 selected!</p>", unsafe_allow_html=True)

if 'selected' in st.session_state:
    st.subheader("📋 Your selected version:")
    st.text_area("Final version:", value=st.session_state.selected, height=200)
