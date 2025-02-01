from flask import Flask, request, jsonify
from flask_cors import CORS
import pdfplumber
import google.generativeai as genai
from werkzeug.serving import WSGIRequestHandler
import json

WSGIRequestHandler.protocol_version = "HTTP/1.1"

app = Flask(__name__)
CORS(app, resources={
    r"/api/*": {
        "origins": "*",
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024

GEMINI_API_KEY = "AIzaSyAJG76gsqVHGiJ0TKwTZqKvrpdvmFw7k0M"
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-pro')

def extract_text_from_pdf(pdf_file):
    try:
        with pdfplumber.open(pdf_file) as pdf:
            text = ""
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return None

def extract_key_points(text):
    try:
        analysis_prompt = f"""Analyze this research paper and identify 5 key points for discussion:
        1. Main objective/problem being addressed
        2. Methodology or approach
        3. Key findings or results
        4. Practical implications
        5. Future directions or challenges
        
        Format the response as:
        Point1: [brief description]
        Point2: [brief description]
        Point3: [brief description]
        Point4: [brief description]
        Point5: [brief description]
        
        Text: {text[:3000]}"""
        
        response = model.generate_content(analysis_prompt)
        points = response.text.strip().split('\n')
        return points
    except Exception as e:
        print(f"Error extracting key points: {e}")
        return []

def extract_paper_details(text):
    try:
        analysis_prompt = f"""Analyze the following research paper text and extract:
        1. The paper's title
        2. The main research topic/field
        Keep the response in simple format: "Title: [title]\nTopic: [topic]"
        
        Text: {text[:2000]}"""
        
        response = model.generate_content(analysis_prompt)
        analysis = response.text.strip()
        
        title_line = [line for line in analysis.split('\n') if line.startswith('Title:')]
        topic_line = [line for line in analysis.split('\n') if line.startswith('Topic:')]
        
        title = title_line[0].replace('Title:', '').strip() if title_line else "Untitled Research Paper"
        topic = topic_line[0].replace('Topic:', '').strip() if topic_line else "General Research"
        
        return title, topic
    except Exception as e:
        print(f"Error extracting paper details: {e}")
        return "Untitled Research Paper", "General Research"

def get_conversation_style(preferences):
    length_map = {
        'short': "Keep responses concise, between 1-2 sentences.",
        'medium': "Provide moderate detail, between 2-3 sentences.",
        'long': "Give comprehensive responses, between 3-4 sentences."
    }

    tone_map = {
        'casual': "Use a conversational, friendly tone with everyday language and relatable examples.",
        'professional': "Maintain a professional tone while being clear and accessible.",
        'academic': "Use academic language and technical terminology appropriately."
    }

    detail_map = {
        'overview': "Focus on high-level concepts and main takeaways.",
        'balanced': "Balance key concepts with supporting details.",
        'detailed': "Include specific details, methodology, and technical aspects."
    }

    audience_map = {
        'general': "Explain concepts for an educated but non-expert audience.",
        'academic': "Use scholarly language and focus on research implications.",
        'industry': "Emphasize practical applications and industry relevance."
    }

    pace_map = {
        'slow': "Use shorter sentences and clear transitions.",
        'normal': "Maintain a natural conversational pace.",
        'fast': "Use efficient language while maintaining clarity."
    }

    return f"""
    {length_map[preferences['length']]}
    {tone_map[preferences['tone']]}
    {detail_map[preferences['detailLevel']]}
    {audience_map[preferences['targetAudience']]}
    {pace_map[preferences['speakingPace']]}
    """

def generate_conversation(text, key_points, preferences, title, topic):
    conversation = []
    style_instructions = get_conversation_style(preferences)
    included_sections = preferences['includedSections']
    
    # Introduction
    intro_prompt = f"""Generate a welcoming podcast introduction for a research paper discussion.
    The paper is titled '{title}' about {topic}'.
    
    Guidelines:
    - Start with a general welcome
    - No personal references or specific host names
    - Focus on the topic and its importance
    - Use engaging but professional language
    
    {style_instructions}"""
    
    host_intro = model.generate_content(intro_prompt)
    conversation.append({"speaker": "Host", "message": host_intro.text.strip()})
    
    guest_intro = model.generate_content(f"""
    Generate an expert's opening response about the paper '{title}'.
    - Focus directly on the research topic
    - Express enthusiasm about the research
    - Use natural, conversational language
    
    {style_instructions}
    """)
    conversation.append({"speaker": "Guest", "message": guest_intro.text.strip()})
    
    # Main sections
    if included_sections.get('methodology', True):
        for prompt in [
            (f"Ask about the research objective and its significance.\nContext: {key_points[0] if key_points else ''}", True),
            (f"Explain the research objective and its importance.\nContext: {key_points[0] if key_points else ''}", False),
            (f"Ask about the research methodology.\nContext: {key_points[1] if len(key_points) > 1 else ''}", True),
            (f"Explain the methodology clearly.\nContext: {key_points[1] if len(key_points) > 1 else ''}", False)
        ]:
            response = model.generate_content(f"{prompt[0]}\n{style_instructions}")
            conversation.append({
                "speaker": "Host" if prompt[1] else "Guest",
                "message": response.text.strip()
            })
    
    if included_sections.get('results', True):
        for prompt in [
            (f"Ask about key findings.\nContext: {key_points[2] if len(key_points) > 2 else ''}", True),
            (f"Share the key findings and their importance.\nContext: {key_points[2] if len(key_points) > 2 else ''}", False)
        ]:
            response = model.generate_content(f"{prompt[0]}\n{style_instructions}")
            conversation.append({
                "speaker": "Host" if prompt[1] else "Guest",
                "message": response.text.strip()
            })
    
    if included_sections.get('implications', True):
        for prompt in [
            (f"Ask about practical implications.\nContext: {key_points[3] if len(key_points) > 3 else ''}", True),
            (f"Discuss practical applications.\nContext: {key_points[3] if len(key_points) > 3 else ''}", False)
        ]:
            response = model.generate_content(f"{prompt[0]}\n{style_instructions}")
            conversation.append({
                "speaker": "Host" if prompt[1] else "Guest",
                "message": response.text.strip()
            })
    
    # Closing
    closing = model.generate_content(f"""Generate a concluding remark.
    Summarize key points and thank the audience.
    {style_instructions}""")
    conversation.append({"speaker": "Host", "message": closing.text.strip()})
    
    return conversation

@app.route('/api/generate-podcast', methods=['POST'])
def generate_podcast():
    try:
        if 'pdf' not in request.files:
            return jsonify({'error': 'No PDF file provided'}), 400

        preferences = json.loads(request.form.get('preferences', '{}'))
        pdf_file = request.files['pdf']
        
        if pdf_file.filename == '':
            return jsonify({'error': 'No selected file'}), 400

        research_paper_text = extract_text_from_pdf(pdf_file)
        if not research_paper_text:
            return jsonify({'error': 'Failed to extract text from PDF'}), 400

        title, topic = extract_paper_details(research_paper_text)
        key_points = extract_key_points(research_paper_text)
        conversation = generate_conversation(
            research_paper_text,
            key_points,
            preferences,
            title,
            topic
        )

        return jsonify({
            'conversation': conversation,
            'title': title,
            'topic': topic
        })

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000, threaded=True, host='0.0.0.0')