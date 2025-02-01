import groq
import google.generativeai as genai
import PyPDF2
import os

# Initialize Groq client
GROQ_API_KEY = "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"
groq_client = groq.Groq(api_key=GROQ_API_KEY)

# Initialize Gemini
GEMINI_API_KEY = "AIzaSyCYS1M4u1YjlSPmRcook-eO-B2UV2OtyNc"
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
    """Use Gemini to analyze the paper and extract workflow"""
    try:
        prompt = """Analyze this research paper and provide a structured workflow of the methodology and approach. 
        Focus on:
        1. Problem Statement/Research Goals
        2. Methodology Steps
        3. Implementation Details
        4. Evaluation Methods
        5. Results Analysis
        
        Format your response as a clear, step-by-step workflow that shows how each part connects to others.
        Be specific but concise. Use bullet points and clear section headers.
        
        Text:
        {text}
        """
        
        response = gemini_model.generate_content(
            prompt.format(text=text[:10000]),  # Limit text length
            generation_config={
                "temperature": 0.3,
                "top_p": 0.9,
                "top_k": 40,
                "max_output_tokens": 2048
            }
        )
        
        print("\nGemini Analysis:")
        print("-" * 40)
        print(response.text)
        print("-" * 40)
        return response.text
    
    except Exception as e:
        print(f"Error in Gemini analysis: {str(e)}")
        raise

def generate_mermaid_with_groq(workflow_text):
    """Use Groq to generate Mermaid diagram from Gemini's analysis"""
    try:
        prompt = """Convert this research paper workflow into a Mermaid flowchart diagram.
        The diagram should:
        1. Show the main workflow steps
        2. Include subprocesses and key details
        3. Use clear, descriptive labels
        4. Show connections between steps
        
        Use this Mermaid syntax:
        ```mermaid
        graph TD
            %% Main workflow
            subgraph MainFlow["Research Paper Workflow"]
                A["Problem Statement/Research Goals"] --> B["Methodology"]
                B --> C["Implementation"]
                C --> D["Evaluation"]
                D --> E["Results Analysis"]
            end
            
            %% Methodology subprocesses
            subgraph MethodSteps["Methodology Details"]
                B1["Method Step 1"] --> B2["Method Step 2"]
            end
            B --> MethodSteps
            
            %% Implementation subprocesses
            subgraph ImpSteps["Implementation Details"]
                C1["Implementation Step 1"] --> C2["Implementation Step 2"]
                C2 --> C3["Implementation Step 3"]
            end
            C --> ImpSteps
            
            %% Evaluation subprocesses
            subgraph EvalSteps["Evaluation Process"]
                D1["Evaluation Method 1"] --> D2["Evaluation Method 2"]
                D2 --> D3["Results Validation"]
            end
            D --> EvalSteps
            
            %% Results subprocesses
            subgraph ResSteps["Results Analysis"]
                E1["Key Findings"] --> E2["Performance Metrics"]
                E2 --> E3["Conclusions"]
            end
            E --> ResSteps
            
            %% Style definitions
            classDef default fill:#f9f9f9,stroke:#333,stroke-width:2px;
            classDef subgraphTitle fill:#e1e1e1,stroke:#666,stroke-width:2px;
            class MainFlow,MethodSteps,ImpSteps,EvalSteps,ResSteps subgraphTitle;
        ```
        
        Workflow to convert:
        {text}
        """
        
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert at creating Mermaid diagrams. Generate only the Mermaid diagram code, nothing else."
                },
                {
                    "role": "user",
                    "content": prompt.format(text=workflow_text)
                }
            ],
            model="mixtral-8x7b-32768",
            temperature=0.3,
            max_tokens=1000,
        )
        
        response = chat_completion.choices[0].message.content
        # Extract the Mermaid code more robustly
        if "mermaid" in response:
            # Split by 'mermaid' and take everything after it
            parts = response.split("mermaid", 1)
            if len(parts) > 1:
                # Clean up the code and remove any trailing markdown markers
                mermaid_code = parts[1].strip()
                # Remove any trailing markdown code block markers
                mermaid_code = mermaid_code.split("```")[0].strip()
            else:
                raise Exception("Could not extract Mermaid diagram code from response")
        else:
            raise Exception("Response does not contain Mermaid diagram code")
        return mermaid_code
    
    except Exception as e:
        print(f"Error generating Mermaid diagram: {str(e)}")
        raise

def process_paper(pdf_path):
    """Main function to process PDF and generate workflow diagram"""
    try:
        # Extract text from PDF
        print("Extracting text from PDF...")
        pdf_text = extract_text_from_pdf(pdf_path)
        
        # Analyze paper with Gemini
        print("\nAnalyzing paper structure with Gemini...")
        workflow_analysis = analyze_with_gemini(pdf_text)
        
        # Generate Mermaid diagram with Groq
        print("\nGenerating Mermaid diagram with Groq...")
        mermaid_diagram = generate_mermaid_with_groq(workflow_analysis)
        
        # Save diagram to markdown file
        md_output_file = 'paper_workflow.md'
        with open(md_output_file, 'w') as f:
            f.write("```mermaid\n")
            f.write(mermaid_diagram)
            f.write("\n```\n")
        
        # Convert to PNG using mmdc (Mermaid CLI)
        png_output_file = 'paper_workflow.png'
        import subprocess
        try:
            subprocess.run(['npx', '--yes', 'mmdc', '-i', md_output_file, '-o', png_output_file], check=True)
            print(f"\nMermaid diagram has been saved as PNG to '{png_output_file}'")
        except subprocess.CalledProcessError as e:
            print(f"Error converting to PNG: {e}")
        except FileNotFoundError:
            print("Error: mmdc command not found. Installing @mermaid-js/mermaid-cli...")
            subprocess.run(['npm', 'install', '-g', '@mermaid-js/mermaid-cli'], check=True)
            subprocess.run(['npx', '--yes', 'mmdc', '-i', md_output_file, '-o', png_output_file], check=True)
            print(f"\nMermaid diagram has been saved as PNG to '{png_output_file}'")
        
        print(f"\nMermaid diagram has been saved to '{md_output_file}'")
        print("\nGenerated Mermaid Diagram:")
        print("=" * 80)
        print(mermaid_diagram)
        
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    # Specify your PDF path
    pdf_path = "/Users/devmehta/Desktop/jaskeeratt/ddog.pdf"
    process_paper(pdf_path)