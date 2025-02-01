import fitz  # PyMuPDF
import base64
import os
from groq import Groq
from moviepy import (
    ImageClip, 
    CompositeVideoClip, 
    concatenate_videoclips, 
    AudioFileClip,
    VideoClip
)
from gtts import gTTS
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import tempfile
import shutil
import time
import requests
from io import BytesIO
import random
from icrawler.builtin import GoogleImageCrawler
import google.generativeai as genai
import subprocess
import json

# Initialize API clients
GEMINI_API_KEY = "AIzaSyCYS1M4u1YjlSPmRcook-eO-B2UV2OtyNc"  # Replace with your Gemini API key
genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel('gemini-pro')

client = Groq(
    api_key="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"  # Replace with your Groq API key
)

def get_search_terms(text):
    """Generate diverse search terms from paper content using Gemini API"""
    prompt = """Analyze this research paper and generate 15 different search terms (2-3 words each) 
    that capture different aspects of the paper's technology, methods, and concepts. 
    Make the terms diverse and visually representable.
    Format: Return only the terms, one per line, no numbers or extra text or exrta hyphens.
    Example format:
    neural networks
    data visualization
    cloud computing
    """
    
    response = gemini_model.generate_content(prompt + "\n\n" + text)
    terms = response.text.strip().split('\n')
    terms = [term.strip() for term in terms if term.strip()]
    
    while len(terms) < 15:
        terms.append("technology innovation")
    
    print("Generated search terms:", terms)
    return terms

def download_theme_images(query, output_dir, num_images=5):
    """Download images using icrawler with added error handling and fallback mechanisms"""
    print(f"\nSearching for images: '{query}'")
    os.makedirs(output_dir, exist_ok=True)
    
    downloaded_images = []
    
    try:
        # Add headers to mimic a real browser
        # headers = {
        #     'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        # }
        
        # Configure and create the crawler with retry mechanism
        google_crawler = GoogleImageCrawler(
            storage={'root_dir': output_dir},
            feeder_threads=1,
            parser_threads=1,
            downloader_threads=1,
        )
        
        # Add delay between requests to avoid rate limiting
        time.sleep(2)
        
        # Download images with retries
        max_retries = 1
        for attempt in range(max_retries):
            try:
                google_crawler.crawl(
                    keyword=query,
                    max_num=num_images,
                    min_size=(200,200),
                    max_size=None
                )
                break
            except Exception as e:
                print(f"Attempt {attempt + 1} failed: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(5)  # Wait before retrying
                continue
        
        # Verify downloaded images
        for filename in os.listdir(output_dir):
            if filename.endswith(('.jpg', '.jpeg', '.png')):
                file_path = os.path.join(output_dir, filename)
                try:
                    # Verify image can be opened
                    with Image.open(file_path) as img:
                        # Check if image is not corrupt
                        img.verify()
                    downloaded_images.append(file_path)
                    print(f"Successfully downloaded: {file_path}")
                except Exception as e:
                    print(f"Invalid image file {file_path}: {str(e)}")
                    if os.path.exists(file_path):
                        os.remove(file_path)
                            
    except Exception as e:
        print(f"Error downloading images: {str(e)}")
    
    # If no images downloaded, create fallback images
    if not downloaded_images:
        print("Creating fallback images...")
        colors = [(30, 30, 30), (45, 45, 45), (60, 60, 60), 
                 (75, 75, 75), (90, 90, 90)]  # Different shades of grey
        
        for i in range(num_images):
            fallback_img = Image.new('RGB', (800, 600), colors[i % len(colors)])
            fallback_path = os.path.join(output_dir, f"fallback_{i}.jpg")
            fallback_img.save(fallback_path)
            downloaded_images.append(fallback_path)
            print(f"Created fallback image: {fallback_path}")
    
    return downloaded_images

def extract_full_text(pdf_path):
    """Extract full text from PDF"""
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text.replace('*', '').replace('★', '').strip()

def get_paper_summary(text):
    """Get summary of paper using Gemini API"""
    prompt = "Summarize this research paper's main objective and methodology in a natural, engaging way. Focus on what makes it interesting and innovative. Keep it to 2-3 sentences, also directly start with the summary:"
    
    response = gemini_model.generate_content(prompt + "\n\n" + text)
    summary = response.text
    summary = summary.replace("Here is", "").replace("This paper", "The research")
    summary = summary.strip(".*: ")
    return summary.strip()

def extract_text_sections(pdf_path):
    """Extract abstract and conclusion from PDF"""
    doc = fitz.open(pdf_path)
    text = ""
    abstract = ""
    conclusion = ""
    
    for page in doc:
        text += page.get_text()
    
    text = text.replace('*', '').replace('★', '').strip()
    
    abstract_start = text.lower().find("abstract")
    if abstract_start != -1:
        abstract_end = text.lower().find("introduction", abstract_start)
        if abstract_end != -1:
            abstract = text[abstract_start:abstract_end].strip()
    
    conclusion_start = text.lower().find("conclusion")
    if conclusion_start != -1:
        conclusion_end = text.lower().find("references", conclusion_start)
        if conclusion_end != -1:
            conclusion = text[conclusion_start:conclusion_end].strip()
        else:
            conclusion = text[conclusion_start:].strip()
    
    return abstract, conclusion

def extract_images_from_pdf(pdf_path, output_folder):
    """Extract images from PDF"""
    os.makedirs(output_folder, exist_ok=True)
    doc = fitz.open(pdf_path)
    image_paths = []
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        images = page.get_images(full=True)
        
        for img_index, img in enumerate(images):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_data = base_image["image"]
            image_ext = base_image["ext"]
            image_filename = f"{output_folder}/page_{page_num+1}_img_{img_index+1}.{image_ext}"
            
            with open(image_filename, "wb") as f:
                f.write(image_data)
            
            image_paths.append(image_filename)
    
    return image_paths

def get_image_explanation(image_path, context=""):
    """Get explanation for image using LLaMA Vision API"""
    with open(image_path, "rb") as image_file:
        image_base64 = base64.b64encode(image_file.read()).decode("utf-8")
    
    image_data_url = f"data:image/png;base64,{image_base64}"
    
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": f"Given this research paper context: {context}\n\nExplain this figure's key insights in 1-2 clear, natural sentences:"
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": image_data_url
                    }
                }
            ]
        }
    ]
    
    completion = client.chat.completions.create(
        model="llama-3.2-90b-vision-preview",
        messages=messages,
        temperature=0.7
    )
    
    explanation = completion.choices[0].message.content
    explanation = explanation.replace("This figure", "The figure")
    explanation = explanation.replace("This image", "The image")
    return explanation.strip()

def create_text_image(text, size=(800, 150), fontsize=24, color=(255, 255, 255), bg_color=(0, 0, 0, 180), current_time=0, audio_duration=None):
    """Create text image with properly progressing captions"""
    img = Image.new('RGBA', size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Create semi-transparent background
    bg = Image.new('RGBA', size, bg_color)
    img.paste(bg, (0, 0), bg)
    
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", fontsize)
    except:
        try:
            font = ImageFont.truetype("arial.ttf", fontsize)
        except:
            font = ImageFont.load_default()

    if audio_duration and current_time is not None:
        words = text.split()
        
        # Calculate timing
        words_per_second = len(words) / audio_duration
        current_word_index = int(current_time * words_per_second)
        
        # Calculate words that fit in one line
        test_text = "A" * 50  # Test string
        test_bbox = draw.textbbox((0, 0), test_text, font=font)
        chars_per_line = int(50 * (size[0] - 40) / (test_bbox[2] - test_bbox[0]))
        
        # Build lines of text
        lines = []
        current_line = []
        current_line_length = 0
        
        for word in words:
            word_length = len(word)
            if current_line_length + word_length + 1 <= chars_per_line:
                current_line.append(word)
                current_line_length += word_length + 1
            else:
                lines.append(current_line)
                current_line = [word]
                current_line_length = word_length + 1
        if current_line:
            lines.append(current_line)
        
        # Determine which lines to show based on current word
        total_words_processed = 0
        current_line_index = 0
        for i, line in enumerate(lines):
            total_words_processed += len(line)
            if total_words_processed > current_word_index:
                current_line_index = i
                break
        
        # Show current line and next line
        lines_to_display = lines[current_line_index:current_line_index + 2]
        
        # Calculate word index within displayed lines
        words_before_current_lines = sum(len(line) for line in lines[:current_line_index])
        relative_word_index = current_word_index - words_before_current_lines
        
        # Draw the lines
        for line_num, line in enumerate(lines_to_display):
            y_pos = size[1]//3 + line_num * (fontsize + 10)
            x_pos = 20
            
            # Draw each word
            word_position = 0
            for word in line:
                # Determine if this is the current word
                is_current_word = (line_num == 0 and word_position == relative_word_index)
                
                # Choose color based on whether this is the current word
                word_color = (255, 255, 0) if is_current_word else color
                
                # Draw the word
                draw.text((x_pos, y_pos), word + " ", font=font, fill=word_color)
                
                # Move to next position
                bbox = draw.textbbox((x_pos, y_pos), word + " ", font=font)
                x_pos = bbox[2]
                word_position += 1
    
    else:
        # Center the text for non-timed display
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (size[0] - text_width) // 2
        y = (size[1] - text_height) // 2
        draw.text((x, y), text, font=font, fill=color)

    # Save to temporary file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    img.save(temp_file.name, "PNG")
    return temp_file.name

def create_section_with_background(title, text, duration, background_images, temp_dir, audio_clip=None):
    """Create a video section with background images and text overlay"""
    if not background_images:
        img_path = create_text_image(text, size=(800, 600), fontsize=28)
        clip = ImageClip(img_path).with_duration(duration)
        if audio_clip:
            clip = clip.with_audio(audio_clip)
        return clip

    clips = []
    segment_duration = duration / len(background_images)
    
    for img_path in background_images:
        # Properly resize and center the background image
        img = Image.open(img_path)
        # Calculate aspect ratio preserving resize
        aspect = img.size[0] / img.size[1]
        if aspect > (800/600):  # wider than target
            new_width = 800
            new_height = int(800 / aspect)
        else:  # taller than target
            new_height = 600
            new_width = int(600 * aspect)
        
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Create a black background
        background = Image.new('RGB', (800, 600), (0, 0, 0))
        # Center the image
        offset = ((800 - new_width) // 2, (600 - new_height) // 2)
        background.paste(img, offset)
        
        bg_clip = ImageClip(np.array(background)).with_duration(segment_duration)
        
        # Create title overlay with improved positioning
        if title:
            def make_title_frame(t):
                title_img = create_text_image(
                    title,
                    size=(800, 80),  # Reduced height for title
                    fontsize=36,
                    bg_color=(0, 0, 0, 200)  # More opacity
                )
                return np.array(Image.open(title_img))
            
            title_overlay = VideoClip(make_title_frame, duration=segment_duration)
        
        # Create text overlay with improved positioning
        def make_subtitle_frame(t):
            text_img = create_text_image(
                text,
                size=(800, 120),  # Adjusted height for better text fit
                fontsize=28,  # Slightly smaller font
                current_time=t,
                audio_duration=audio_clip.duration if audio_clip else None,
                bg_color=(0, 0, 0, 230)  # More opacity for better readability
            )
            return np.array(Image.open(text_img))
        
        content_overlay = VideoClip(make_subtitle_frame, duration=segment_duration)
        
        # Adjust positioning of overlays
        if title:
            combined = CompositeVideoClip([
                bg_clip,
                title_overlay.with_position(('center', 20)),  # Move title up
                content_overlay.with_position(('center', 480))  # Move text down
            ], size=(800, 600))
        else:
            combined = CompositeVideoClip([
                bg_clip,
                content_overlay.with_position(('center', 480))
            ], size=(800, 600))
        
        clips.append(combined)
    
    final_clip = concatenate_videoclips(clips)
    if audio_clip:
        final_clip = final_clip.with_audio(audio_clip)
    return final_clip

def generate_workflow_diagram(text):
    """Generate workflow diagram using Gemini and Groq"""
    # First, analyze with Gemini to get structured workflow
    gemini_prompt = """Analyze this research paper and provide a structured workflow of the methodology and approach. 
    Focus on:
    1. Problem Statement/Research Goals
    2. Methodology Steps
    3. Implementation Details
    4. Evaluation Methods
    5. Results Analysis
    
    Format your response as a clear, step-by-step workflow that shows how each part connects to others.
    Be specific but concise. Use bullet points and clear section headers."""
    
    workflow_analysis = gemini_model.generate_content(gemini_prompt + "\n\n" + text)
    
    # Then, use Groq to convert to Mermaid diagram
    groq_prompt = """Convert this research paper workflow into a Mermaid flowchart diagram.
    Use this Mermaid syntax:
    ```mermaid
    graph TD
        %% Main workflow
        subgraph MainFlow["Research Paper Workflow"]
            A["Problem Statement"] --> B["Methodology"]
            B --> C["Implementation"]
            C --> D["Evaluation"]
            D --> E["Results"]
        end
        
        %% Methodology subprocesses
        subgraph MethodSteps["Methodology Details"]
            B1["Method Step 1"] --> B2["Method Step 2"]
        end
        B --> MethodSteps
        
        %% Implementation subprocesses
        subgraph ImpSteps["Implementation Details"]
            C1["Step 1"] --> C2["Step 2"]
        end
        C --> ImpSteps
        
        %% Style definitions
        classDef default fill:#f9f9f9,stroke:#333,stroke-width:2px;
        classDef subgraphTitle fill:#e1e1e1,stroke:#666,stroke-width:2px;
        class MainFlow,MethodSteps,ImpSteps subgraphTitle;
    ```
    
    Generate only the Mermaid diagram code, nothing else."""
    
    messages = [
        {
            "role": "system",
            "content": "You are an expert at creating Mermaid diagrams. Generate only the Mermaid diagram code, nothing else."
        },
        {
            "role": "user",
            "content": groq_prompt + "\n\n" + workflow_analysis.text
        }
    ]
    
    completion = client.chat.completions.create(
        model="mixtral-8x7b-32768",
        messages=messages,
        temperature=0.3,
        max_tokens=1000,
    )
    
    mermaid_code = completion.choices[0].message.content
    if "```mermaid" in mermaid_code:
        mermaid_code = mermaid_code.split("```mermaid")[1].split("```")[0].strip()
    
    return mermaid_code

def get_workflow_explanation(workflow_image_path, paper_summary):
    """Get explanation for workflow diagram using LLaMA Vision"""
    with open(workflow_image_path, "rb") as image_file:
        image_base64 = base64.b64encode(image_file.read()).decode("utf-8")
    
    image_data_url = f"data:image/png;base64,{image_base64}"
    
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": f"Given this research paper summary: {paper_summary}\n\nExplain this workflow diagram in detail yet concise, describing how each component connects and flows. Focus on the methodology and process flow shown in the diagram. Keep it natural and engaging:"
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": image_data_url
                    }
                }
            ]
        }
    ]
    
    completion = client.chat.completions.create(
        model="llama-3.2-90b-vision-preview",
        messages=messages,
        temperature=0.7
    )
    
    explanation = completion.choices[0].message.content
    return explanation.strip()

def create_full_video(abstract, images_with_explanations, conclusion, paper_summary, full_text, output_path):
    """Create full video with all segments and dynamic backgrounds"""
    clips = []
    temp_files = []
    temp_dir = tempfile.mkdtemp()
    
    # Create a subdirectory for Mermaid output
    mermaid_dir = os.path.join(temp_dir, "mermaid")
    os.makedirs(mermaid_dir, exist_ok=True)
    
    try:
        print("Video Generation Progress:")
        
        print("Generating search terms...")
        search_terms = get_search_terms(full_text)
        
        print("Downloading theme images...")
        ai_images = download_theme_images(search_terms[0], temp_dir, num_images=2)
        ai_images.extend(download_theme_images(search_terms[1], temp_dir, num_images=2))
        ai_images.extend(download_theme_images(search_terms[2], temp_dir, num_images=1))
        
        research_images = download_theme_images(search_terms[3], temp_dir, num_images=2)
        research_images.extend(download_theme_images(search_terms[4], temp_dir, num_images=2))
        research_images.extend(download_theme_images(search_terms[5], temp_dir, num_images=1))
        
        conclusion_images = download_theme_images(search_terms[6], temp_dir, num_images=2)
        conclusion_images.extend(download_theme_images(search_terms[7], temp_dir, num_images=2))
        conclusion_images.extend(download_theme_images(search_terms[8], temp_dir, num_images=1))
        
        print("Creating title section...")
        title_duration = 2
        clips.append(create_section_with_background(
            "Research Paper Analysis",
            "An AI-Powered Summary",
            title_duration,
            ai_images,
            temp_dir
        ))
        
        print("Creating summary section...")
        summary_text = paper_summary
        tts = gTTS(text=summary_text, lang="en", slow=False)
        summary_audio = f"{temp_dir}/summary_audio.mp3"
        tts.save(summary_audio)
        summary_audio_clip = AudioFileClip(summary_audio)
        
        clips.append(create_section_with_background(
            "Paper Overview",
            summary_text,
            summary_audio_clip.duration,
            research_images,
            temp_dir,
            summary_audio_clip
        ))
        
        print("Creating abstract section...")
        abstract_sentences = abstract.split('.')[:3]
        shortened_abstract = '. '.join(abstract_sentences) + '.'
        
        abstract_tts = gTTS(text=shortened_abstract, lang="en", slow=False)
        abstract_audio = f"{temp_dir}/abstract_audio.mp3"
        abstract_tts.save(abstract_audio)
        abstract_audio_clip = AudioFileClip(abstract_audio)
        
        clips.append(create_section_with_background(
            "Abstract",
            shortened_abstract,
            abstract_audio_clip.duration,
            research_images,
            temp_dir,
            abstract_audio_clip
        ))
        
        print("Generating workflow diagram...")
        try:
            mermaid_code = generate_workflow_diagram(full_text)
            workflow_md = os.path.join(mermaid_dir, "workflow.md")
            
            with open(workflow_md, 'w') as f:
                f.write("```mermaid\n")
                f.write(mermaid_code)
                f.write("\n```\n")
            
            # Convert to PNG using mmdc
            mmdc_path = shutil.which('mmdc')
            if mmdc_path:
                try:
                    subprocess.run([
                        mmdc_path,
                        '-i', workflow_md,
                        '-o', os.path.join(mermaid_dir, "workflow.png"),
                        '-b', 'transparent'
                    ], check=True)
                    
                    # Check for the file with different possible names
                    possible_filenames = [
                        os.path.join(mermaid_dir, "workflow-1.png"),
                        os.path.join(mermaid_dir, "workflow.png"),
                        "./workflow-1.png",
                        "workflow-1.png"
                    ]
                    
                    workflow_png = None
                    for filename in possible_filenames:
                        if os.path.exists(filename):
                            workflow_png = filename
                            break
                    
                    if workflow_png and os.path.exists(workflow_png):
                        print(f"✅ Workflow diagram generated at: {workflow_png}")
                        
                        # Get workflow explanation
                        workflow_explanation = get_workflow_explanation(workflow_png, paper_summary)
                        
                        # Create workflow section
                        workflow_tts = gTTS(text=workflow_explanation, lang="en", slow=False)
                        workflow_audio = os.path.join(temp_dir, "workflow_audio.mp3")
                        workflow_tts.save(workflow_audio)
                        workflow_audio_clip = AudioFileClip(workflow_audio)
                        
                        # Process workflow image
                        image = Image.open(workflow_png)
                        target_size = (800, 450)
                        image.thumbnail(target_size, Image.Resampling.LANCZOS)
                        background = Image.new('RGB', target_size, (255, 255, 255))
                        offset = ((target_size[0] - image.size[0]) // 2,
                                 (target_size[1] - image.size[1]) // 2)
                        background.paste(image, offset)
                        processed_workflow_path = os.path.join(temp_dir, "processed_workflow.png")
                        background.save(processed_workflow_path)
                        
                        workflow_clip = ImageClip(processed_workflow_path)
                        
                        def make_workflow_frame(t):
                            text_img = create_text_image(
                                workflow_explanation,
                                size=(800, 150),
                                fontsize=32,
                                current_time=t,
                                audio_duration=workflow_audio_clip.duration,
                                bg_color=(0, 0, 0, 200)
                            )
                            return np.array(Image.open(text_img))
                        
                        workflow_text_overlay = VideoClip(make_workflow_frame, duration=workflow_audio_clip.duration)
                        
                        workflow_composite = CompositeVideoClip([
                            workflow_clip.with_duration(workflow_audio_clip.duration),
                            workflow_text_overlay.with_position(('center', 450))
                        ], size=(800, 600))
                        
                        workflow_composite = workflow_composite.with_audio(workflow_audio_clip)
                        clips.append(workflow_composite)
                        
                        temp_files.extend([
                            workflow_audio,
                            processed_workflow_path,
                            workflow_md,
                            workflow_png
                        ])
                    else:
                        print("Warning: Could not find generated workflow PNG file")
                        print("Checked locations:", possible_filenames)
                except subprocess.CalledProcessError as e:
                    print(f"Error running Mermaid CLI: {e}")
                    print("Command output:", e.output if hasattr(e, 'output') else 'No output available')
            else:
                print("Warning: Mermaid CLI not found, skipping workflow diagram")
                print("To install Mermaid CLI, run: npm install -g @mermaid-js/mermaid-cli")
        
        except Exception as e:
            print(f"Warning: Error generating workflow diagram: {str(e)}")
            print("Continuing without workflow diagram...")
        
        if images_with_explanations:
            print("Creating figures section...")
            for idx, (img_path, explanation) in enumerate(images_with_explanations, 1):
                print(f"Processing figure {idx}/{len(images_with_explanations)}...")
                
                tts = gTTS(text=explanation, lang="en", slow=False)
                audio_file = f"{temp_dir}/img_{idx}_audio.mp3"
                tts.save(audio_file)
                audio_clip = AudioFileClip(audio_file)
                duration = audio_clip.duration

                image = Image.open(img_path)
                target_size = (800, 450)
                image.thumbnail(target_size, Image.Resampling.LANCZOS)
                background = Image.new('RGB', target_size, 'white')
                offset = ((target_size[0] - image.size[0]) // 2,
                         (target_size[1] - image.size[1]) // 2)
                background.paste(image, offset)
                processed_img_path = f"{temp_dir}/processed_img_{idx}.png"
                background.save(processed_img_path)

                image_clip = ImageClip(processed_img_path)
                
                def make_explanation_frame(t):
                    text_img = create_text_image(
                        explanation,
                        size=(800, 150),
                        fontsize=32,
                        current_time=t,
                        audio_duration=audio_clip.duration,
                        bg_color=(0, 0, 0, 200)
                    )
                    return np.array(Image.open(text_img))
                
                text_overlay = VideoClip(make_explanation_frame, duration=duration)
                
                composite = CompositeVideoClip([
                    image_clip.with_duration(duration),
                    text_overlay.with_position(('center', 450))
                ], size=(800, 600))
                
                composite = composite.with_audio(audio_clip)
                clips.append(composite)
                
                temp_files.extend([audio_file, processed_img_path])
        
        print("Creating conclusion section...")
        conclusion_sentences = conclusion.split('.')[:3]
        shortened_conclusion = '. '.join(conclusion_sentences) + '.'
        
        conclusion_tts = gTTS(text=shortened_conclusion, lang="en", slow=False)
        conclusion_audio = f"{temp_dir}/conclusion_audio.mp3"
        conclusion_tts.save(conclusion_audio)
        conclusion_audio_clip = AudioFileClip(conclusion_audio)
        
        clips.append(create_section_with_background(
            "Conclusion",
            shortened_conclusion,
            conclusion_audio_clip.duration,
            conclusion_images,
            temp_dir,
            conclusion_audio_clip
        ))

        print("Compiling final video...")
        final_video = concatenate_videoclips(clips)
        final_video.write_videofile(
            output_path,
            fps=24,
            codec='libx264',
            preset='ultrafast',
            audio_codec='aac',
            threads=4,
            bitrate="2000k",
            ffmpeg_params=["-deadline", "realtime", "-cpu-used", "5"]
        )
        
        print("✅ Video created successfully")

    finally:
        # Cleanup
        for clip in clips:
            try:
                clip.close()
            except:
                pass
        
        for file_path in temp_files:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except:
                pass
        
        try:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
        except:
            pass

def process_paper(pdf_path, output_path):
    """Process a research paper and generate video"""
    try:
        print("Starting process...")
        
        print("Extracting text and generating summary...")
        full_text = extract_full_text(pdf_path)
        paper_summary = get_paper_summary(full_text)
        print("✅ Paper summary generated")
        
        print("Extracting text sections...")
        abstract, conclusion = extract_text_sections(pdf_path)
        print("✅ Text sections extracted")
        
        print("Extracting images...")
        with tempfile.TemporaryDirectory() as temp_dir:
            images_folder = os.path.join(temp_dir, "images")
            image_paths = extract_images_from_pdf(pdf_path, images_folder)
            print(f"✅ Found {len(image_paths)} images")
            
            if not image_paths:
                raise ValueError("No images found in the PDF.")
            
            images_with_explanations = []
            for i, img_path in enumerate(image_paths):
                print(f"Analyzing image {i+1}/{len(image_paths)}...")
                explanation = get_image_explanation(img_path, context=paper_summary)
                images_with_explanations.append((img_path, explanation))
            
            print("Generating video...")
            create_full_video(abstract, images_with_explanations, conclusion, paper_summary, full_text, output_path)
            print(f"✅ Video saved to: {output_path}")
            
    except Exception as e:
        print(f"Error processing paper: {str(e)}")
        raise e

if __name__ == "__main__":
    pdf_path = r"C:\Projects\Life Projects\Mined_2025\Integrating_Generative_AI_for_Enhanced_Automation_in_System_Design_Processes.pdf"
    output_path = "output_video.mp4"
    process_paper(pdf_path, output_path)