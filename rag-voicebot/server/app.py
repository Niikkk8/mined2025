from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
import PyPDF2
import io

app = Flask(__name__)
# Enable CORS for all routes with proper configuration
CORS(app, resources={
    r"/*": {
        "origins": ["http://localhost:5173", "http://localhost:5174", "http://localhost:3000"],  # Add your frontend URL
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

# Initialize Gemini with API key
API_KEY = "AIzaSyCYS1M4u1YjlSPmRcook-eO-B2UV2OtyNc"
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-pro')

def extract_text_from_pdf(pdf_file):
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text.strip()
    except Exception as e:
        print(f"Error in PDF extraction: {str(e)}")  # Debug print
        raise Exception(f"Error extracting text from PDF: {str(e)}")

def generate_summary(text):
    try:
        prompt = """Create a detailed academic summary of this text using the following structure:
        1. OVERVIEW
        2. KEY POINTS
        3. CONCLUSIONS
        
        Text: {text}
        """
        
        response = model.generate_content(
            prompt.format(text=text),
            generation_config={
                "temperature": 0.3,
                "top_p": 0.9,
                "top_k": 40,
                "max_output_tokens": 4096
            }
        )
        return response.text
    except Exception as e:
        print(f"Error in summary generation: {str(e)}")  # Debug print
        raise Exception(f"Error generating summary: {str(e)}")

@app.route('/api/process-file', methods=['POST'])
def process_file():
    try:
        print("Received file upload request")  # Debug print
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        # Read and process the PDF
        pdf_content = file.read()
        pdf_file = io.BytesIO(pdf_content)
        
        print("Extracting text from PDF...")  # Debug print
        extracted_text = extract_text_from_pdf(pdf_file)
        
        print("Generating summary...")  # Debug print
        summary = generate_summary(extracted_text)

        return jsonify({
            'text': extracted_text,
            'summary': summary
        })

    except Exception as e:
        print(f"Error processing file: {str(e)}")  # Debug print
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        prompt = data.get('prompt')
        context = data.get('context', '')
        
        if not prompt:
            return jsonify({'error': 'No prompt provided'}), 400

        system_prompt = f"""You are an AI assistant helping with document analysis. 
        Here is the context from the uploaded document:
        {context}
        
        Please answer the following question based on this context. 
        If the question is not related to the document content, 
        clearly state that and provide a general response based on your knowledge.
        
        Question: {prompt}"""

        response = model.generate_content(system_prompt)
        return jsonify({'response': response.text})

    except Exception as e:
        print(f"Error in chat: {str(e)}")  # Debug print
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("Starting Flask server...")  # Debug print
    app.run(debug=True, port=5000)