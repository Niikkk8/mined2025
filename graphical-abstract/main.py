import os
import groq
import google.generativeai as genai
import PyPDF2
from graphviz import Digraph
from transformers import pipeline, AutoModelForSequenceClassification, AutoTokenizer
from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.cluster import KMeans
import nltk
import networkx as nx
import matplotlib.pyplot as plt

# Initialize API clients
GROQ_API_KEY = "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"
GEMINI_API_KEY = "AIzaSyCYS1M4u1YjlSPmRcook-eO-B2UV2OtyNc"

groq_client = groq.Groq(api_key=GROQ_API_KEY)
genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel('gemini-pro')

def extract_text_from_pdf(pdf_path):
    """Extract text from a PDF file"""
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text.strip()
    except Exception as e:
        raise Exception(f"Error extracting text from PDF: {str(e)}")

def analyze_with_gemini(text):
    """Use Gemini and other models to analyze the paper and extract key components for each section"""
    try:
        # Download required NLTK data
        nltk.download('punkt')
        
        # Initialize models
        summarizer = pipeline('summarization', model='facebook/bart-large-cnn')
        classifier = pipeline('zero-shot-classification', model='facebook/bart-large-mnli')
        sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # First, get a concise summary
        summary = summarizer(text[:1024], max_length=130, min_length=30, do_sample=False)[0]['summary_text']
        
        # Classify main topics
        topics = classifier(
            text[:1024],
            candidate_labels=['methodology', 'findings', 'impact', 'background', 'future work']
        )
        
        # Encode text for semantic analysis
        sentences = [s.strip() for s in text.split('.') if len(s.strip()) > 10][:50]
        embeddings = sentence_model.encode(sentences)
        
        # Cluster sentences for better organization
        n_clusters = min(5, len(sentences))
        kmeans = KMeans(n_clusters=n_clusters, random_state=42).fit(embeddings)
        clusters = {i: [] for i in range(n_clusters)}
        for sent, label in zip(sentences, kmeans.labels_):
            clusters[label].append(sent)
        
        prompts = {
            "methodology": """Analyze the methodology section of this research paper and provide:
            1. Research Design
            2. Data Collection Methods
            3. Analysis Techniques
            4. Tools and Technologies Used
            Format as concise bullet points.
            
            Text: {text}
            """,
            "findings": """Extract the key findings and results from this research paper:
            1. Primary Results
            2. Statistical Significance
            3. Key Observations
            4. Performance Metrics
            Format as concise bullet points.
            
            Text: {text}
            """,
            "impact": """Analyze the impact and implications of this research:
            1. Practical Applications
            2. Industry Impact
            3. Future Directions
            4. Limitations and Challenges
            Format as concise bullet points.
            
            Text: {text}
            """
        }
        
        results = {}
        for section, prompt in prompts.items():
            response = gemini_model.generate_content(
                prompt.format(text=text[:10000]),
                generation_config={
                    "temperature": 0.3,
                    "top_p": 0.9,
                    "top_k": 40,
                    "max_output_tokens": 2048
                }
            )
            results[section] = response.text
        
        return results
    except Exception as e:
        raise Exception(f"Error in Gemini analysis: {str(e)}")

def create_visual_abstract(analysis_results, section):
    """Create an enhanced visual abstract using multiple visualization techniques"""
    try:
        # Create both hierarchical and network-based visualizations
        dot = Digraph(comment=f'Research Visual Abstract - {section.title()}')
        dot.attr(rankdir='TB')
        
        # Enhanced style configurations
        colors = {
            'methodology': '#E6F3FF',  # Soft blue
            'findings': '#E6FFE6',      # Soft green
            'impact': '#FFE6E6'         # Soft red
        }
        
        # Create a network graph for complex relationships
        G = nx.DiGraph()
        
        # Add gradient and modern styling
        dot.attr('node', shape='box', style='rounded,filled,radial', fillcolor=f'{colors.get(section, "#F5F5F5")}:white')
        dot.attr('edge', color='#666666', penwidth='2.0')
        dot.attr(bgcolor='transparent')
        
        dot.attr('node', shape='box', style='rounded,filled', fillcolor=colors.get(section, 'lightgray'))
        dot.attr('edge', color='#666666')
        
        # Create nodes and edges based on the section analysis
        sections = analysis_results[section].split('\n')
        prev_node = None
        
        for i, point in enumerate(sections):
            if point.strip():
                # Create a node for each bullet point
                node_id = f'node_{i}'
                dot.node(node_id, point.strip())
                
                # Connect to previous node
                if prev_node:
                    dot.edge(prev_node, node_id)
                prev_node = node_id
        
        # Save the visual abstract
        output_file = f'visual_abstract_{section}'
        dot.render(output_file, format='png', cleanup=True)
        return f'{output_file}.png'
    
    except Exception as e:
        raise Exception(f"Error creating visual abstract for {section}: {str(e)}")

def process_paper(pdf_path):
    """Main function to process paper and generate multiple visual abstracts"""
    try:
        # Extract text from PDF
        print("Extracting text from PDF...")
        pdf_text = extract_text_from_pdf(pdf_path)
        
        # Analyze paper with Gemini for each section
        print("\nAnalyzing paper sections...")
        analysis_results = analyze_with_gemini(pdf_text)
        
        # Create visual abstracts for each section
        print("\nGenerating visual abstracts...")
        output_files = {}
        for section in analysis_results.keys():
            output_files[section] = create_visual_abstract(analysis_results, section)
            print(f"\nVisual abstract for {section} has been saved as '{output_files[section]}'")
        
        print("\nAnalysis Results:")
        print("=" * 80)
        for section, analysis in analysis_results.items():
            print(f"\n{section.upper()}:")
            print("-" * 40)
            print(analysis)
        
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    pdf_path = "dd.pdf"  # Replace with your PDF path
    process_paper(pdf_path)