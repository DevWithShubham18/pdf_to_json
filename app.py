import streamlit as st
import fitz
import json
import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

#api_key = os.getenv("GROQ_API_KEY")
api_key = st.secrets["GROQ_API_KEY"]
if not api_key:
    st.error("GROQ_API_KEY not found")
    st.stop()

client = Groq(api_key=api_key)

st.title("PDF to JSON Extractor")

st.sidebar.title("Progress Checklist")

uploaded = False
extracted = False
generated = False

uploaded_file = st.file_uploader("Upload company report PDF", type=["pdf"])

if uploaded_file is not None:
    uploaded = True

    temp_path = "temp_report.pdf"
    with open(temp_path, "wb") as f:
        f.write(uploaded_file.read())

    st.success("PDF uploaded successfully")

    text = ""

    try:
        doc = fitz.open(temp_path)
        for page in doc:
            text += page.get_text()
        doc.close()
        extracted = True
    except Exception as e:
        st.error(f"Error reading PDF: {e}")

    st.subheader("Extracted Text Preview")
    st.text_area("Preview", text[:2000], height=200)

    if text.strip() == "":
        st.warning("No text extracted from PDF.")

    if st.button("Generate JSON"):

        schema = {
            "company_name": "string",
            "reporting_year": "string",
            "revenue": "string",
            "profit_growth_percent": "string",
            "summary": "string"
        }

        prompt = f"""
Extract structured data from the company report.

Follow this JSON schema EXACTLY:
{json.dumps(schema, indent=2)}

Rules:
- Return ONLY valid JSON
- Do not add extra fields
- If data is missing, return "N/A"

Text:
{text[:10000]}
"""

        with st.spinner("Generating structured JSON..."):
            try:
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {
                            "role": "system",
                            "content": "You extract structured data. Always return valid JSON."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0
                )

                result = response.choices[0].message.content.strip()
                result = result.replace("```json", "").replace("```", "").strip()

                st.subheader("JSON Output")

                try:
                    json_output = json.loads(result)
                    st.json(json_output)
                    generated = True
                except:
                    st.warning("Model did not return valid JSON. Showing raw output:")
                    st.write(result)

            except Exception as e:
                st.error(f"LLM call failed: {e}")

st.sidebar.write(f"{'✅' if uploaded else '⬜'} Upload PDF")
st.sidebar.write(f"{'✅' if extracted else '⬜'} Extract Text")
st.sidebar.write(f"{'✅' if generated else '⬜'} Generate JSON")
