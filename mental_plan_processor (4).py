# This script is meant to be run in a standard Python environment with Streamlit.
# It will not work properly in Pyodide, JupyterLite, or other browser-based environments.

import streamlit as st
import pandas as pd
import requests
import openai

st.set_page_config(page_title="Mental Health Plan Generator", layout="wide")

# Set your OpenAI API key securely (use secrets.toml in production)
openai.api_key = "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"

if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# Login page
if not st.session_state.authenticated:
    st.title("🔐 Sign In")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")

    if submit:
        if username == "admin" and password == "1234":
            st.session_state.authenticated = True
            st.success("✅ Login successful! Use the menu to proceed.")
        else:
            st.error("❌ Invalid credentials. Try again.")

if st.session_state.authenticated:
    st.title("🧠 AI-Powered Patient Treatment Generator")

    st.subheader("📦 View Available GPT Models")
    if st.button("🔍 List Models"):
        try:
            models = openai.Model.list()
            model_names = [m.id for m in models['data']]
            st.success(f"✅ Found {len(model_names)} models")
            st.selectbox("Choose a model", model_names)
        except Exception as e:
            st.error(f"❌ Error fetching models: {e}")

    # Chat interface
    st.subheader("🤖 Ask the AI Assistant")
    user_input = st.text_input("You:", key="chat_input")

    if user_input:
        st.session_state.chat_history.append(("You", user_input))
        try:
            gpt_response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "system", "content": "You are a helpful medical AI assistant."}] +
                         [{"role": "user", "content": m[1]} if m[0] == "You" else {"role": "assistant", "content": m[1]}
                          for m in st.session_state.chat_history if m[0] != "AI" or m[1] != "Loading..."]
            )
            reply = gpt_response["choices"][0]["message"]["content"].strip()
        except Exception as e:
            if "quota" in str(e).lower():
                reply = "⚠️ Your OpenAI quota has been exceeded. Please check your billing and usage at https://platform.openai.com/account/usage."
            else:
                reply = f"❌ OpenAI error: {str(e)}"

        st.session_state.chat_history.append(("AI", reply))

    for speaker, message in st.session_state.chat_history:
        st.markdown(f"**{speaker}:** {message}")

    def analyze_and_generate_plan(row):
        prompt = f"""
You are a medical AI assistant. Analyze the following patient details and generate:
- Condition Risk Level
- Initial Treatment Plan
- Adapted Plan based on feedback
- Final Affordable Plan (considering income level and location)

Patient Info:
{row.to_dict()}
"""
        try:
            response = requests.post(
                "https://n8n.yourdomain.com/webhook/ai-patient-plan",
                json={"text": prompt},
                timeout=15
            )
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"Status {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}

    uploaded_file = st.file_uploader("📤 Upload patient data file (CSV or Excel)", type=["csv", "xls", "xlsx"])

    if uploaded_file:
        try:
            if uploaded_file.name.endswith(".csv"):
                data = pd.read_csv(uploaded_file)
            else:
                data = pd.read_excel(uploaded_file)

            st.success("✅ File uploaded successfully!")
            st.write("### 📊 Uploaded Data Preview")
            st.dataframe(data.head())

            st.write("### 🧠 AI Treatment Suggestions")
            results = []

            for _, row in data.iterrows():
                output = analyze_and_generate_plan(row)
                if "error" in output:
                    st.warning(f"❌ Skipping row: {output['error']}")
                    continue

                results.append({
                    "Patient ID": row.get("id", "N/A"),
                    "Condition": row.get("condition", "N/A"),
                    "Risk Level": output.get("risk", "N/A"),
                    "Initial Plan": output.get("initial_plan", "N/A"),
                    "Adapted Plan": output.get("adapted_plan", "N/A"),
                    "Final Plan": output.get("final_plan", "N/A")
                })

            if results:
                df = pd.DataFrame(results)
                st.dataframe(df)
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button("⬇️ Download Results as CSV", data=csv, file_name="ai_treatment_plans.csv", mime='text/csv')
            else:
                st.info("No valid results generated.")

        except Exception as e:
            st.error(f"❌ Failed to process file: {e}")
    else:
        st.info("Upload a CSV or Excel file to get started.")
