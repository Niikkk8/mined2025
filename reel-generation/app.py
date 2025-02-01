import os
import PyPDF2
from gtts import gTTS
from moviepy.editor import *
from icrawler.builtin import GoogleImageCrawler
import google.generativeai as genai
from pdf2image import convert_from_path
from PIL import Image
import shutil

# Initialize Gemini with the provided API key
API_KEY = "AIzaSyAT_euHmfKz5uItW4B3NV_G4dURe3pJOTk"
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-pro')

def create_directory(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

def cleanup_directory(directory):
    if os.path.exists(directory):
        shutil.rmtree(directory)
    create_directory(directory)

def extract_text_from_pdf(pdf_path):
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text.strip()
    except Exception as e:
        raise Exception(f"Error extracting text from PDF: {str(e)}")

def generate_with_gemini(prompt, max_tokens=4096):
    try:
        response = model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.3,
                "top_p": 0.9,
                "top_k": 40,
                "max_output_tokens": max_tokens
            }
        )
        return response.text
    except Exception as e:
        raise Exception(f"Error generating content with Gemini: {str(e)}")

def generate_summary(text):
    prompt = """Create a detailed academic summary of this research paper using the following structure:
    1. OVERVIEW
    2. RESEARCH OBJECTIVES & METHODOLOGY
    3. KEY FINDINGS & RESULTS
    4. CONCLUSIONS & IMPLICATIONS
    5. FUTURE WORK & RECOMMENDATIONS
    6. PRACTICAL APPLICATIONS & IMPACT

    Text: {text}
    """
    return generate_with_gemini(prompt.format(text=text))

def generate_keywords_with_gemini(summary):
    prompt = f"Extract 5 meaningful keywords from this research paper summary:\n{summary}\n\nReturn only the keywords, separated by commas."
    keywords_response = generate_with_gemini(prompt)
    keywords = [keyword.strip() for keyword in keywords_response.split(',')]
    return keywords[:5]

def generate_reel_script(summary, keywords):
    prompt = f"""
    Create a 30-second engaging Instagram reel script based on this summary:
    {summary}

    Include:
    1. An attention-grabbing opening (🔍)
    2. Simple explanation of the research
    3. Key findings
    4. Engaging conclusion
    5. Add 2-3 relevant emojis in each section

    Make it trendy and suitable for social media.
    Keep sentences short and punchy.
    """
    return generate_with_gemini(prompt)

def process_image(image_path, target_size=(800, 600)):
    try:
        with Image.open(image_path) as img:
            if img.mode != 'RGB':
                img = img.convert('RGB')
            img.thumbnail(target_size, Image.Resampling.LANCZOS)
            img.save(image_path, 'JPEG', quality=85)
            return True
    except Exception as e:
        print(f"Error processing image {image_path}: {e}")
        return False

def download_and_process_images(keywords, output_dir='downloaded_images'):
    cleanup_directory(output_dir)

    processed_images = []
    for keyword in keywords:
        try:
            search_terms = [
                f"{keyword} concept",
                f"{keyword} illustration",
                f"{keyword} icon",
                f"{keyword} diagram"
            ]

            for term in search_terms[:2]:  # Use first 2 search terms
                crawler = GoogleImageCrawler(
                    storage={'root_dir': output_dir},
                    downloader_threads=2
                )
                crawler.crawl(
                    keyword=term,
                    max_num=2,
                    min_size=(300, 200),
                    filters={'type': 'photo'}  # Modify this to use valid filter options
                )

                for img_file in os.listdir(output_dir):
                    if img_file.lower().endswith(('.png', '.jpg', '.jpeg')):
                        img_path = os.path.join(output_dir, img_file)
                        if process_image(img_path):
                            processed_images.append(img_path)
                        else:
                            os.remove(img_path)  # Remove failed images

                if len(processed_images) >= 2:  # If we have enough images, move to next keyword
                    break

        except Exception as e:
            print(f"Error processing keyword {keyword}: {e}")
            continue

    return processed_images

def create_video_from_script(script, images, output_filename='reel_video.mp4'):
    try:
        tts = gTTS(text=script, lang='en', slow=False)
        audio_file = 'temp_audio.mp3'
        tts.save(audio_file)

        if not os.path.exists(audio_file):
            raise Exception("Audio file creation failed")

        audio_clip = AudioFileClip(audio_file)
        total_duration = audio_clip.duration

        if total_duration <= 0:
            raise Exception("Invalid audio duration")

        image_clips = []
        images = images * ((int(total_duration / 5) // len(images)) + 1)  # Repeat images if needed

        for i, img_path in enumerate(images):
            try:
                img_clip = ImageClip(img_path)
                img_clip = img_clip.set_duration(min(5, total_duration - i*5))  # 5 seconds per image or remaining time
                if img_clip.size[0] > 1920:  # Resize if too large
                    img_clip = img_clip.resize(width=1920)
                image_clips.append(img_clip)
            except Exception as e:
                print(f"Error processing image clip {img_path}: {e}")
                continue

        if not image_clips:
            raise Exception("No valid image clips created")

        video_clip = concatenate_videoclips(image_clips, method="compose")
        video_clip = video_clip.set_duration(total_duration)
        video_clip = video_clip.set_audio(audio_clip)

        segments = script.split('\n')
        txt_clips = []

        time_per_segment = total_duration / len(segments)
        for i, segment in enumerate(segments):
            if segment.strip():
                txt_clip = TextClip(
                    segment.strip(),
                    fontsize=30,
                    color='white',
                    stroke_color='black',
                    stroke_width=2,
                    size=(video_clip.w - 40, None),
                    method='label'
                ).set_position(('center', 'bottom'))

                start_time = i * time_per_segment
                txt_clip = txt_clip.set_start(start_time).set_duration(time_per_segment)
                txt_clips.append(txt_clip)

        final_video = CompositeVideoClip([video_clip] + txt_clips)

        final_video.write_videofile(
            output_filename,
            fps=24,
            codec='libx264',
            audio_codec='aac',
            threads=4
        )

        os.remove(audio_file)
        return True

    except Exception as e:
        print(f"Error creating video: {e}")
        return False

def generate_reel_video(pdf_path):
    try:
        pdf_text = extract_text_from_pdf(pdf_path)
        summary = generate_summary(pdf_text)
        keywords = generate_keywords_with_gemini(summary)
        script = generate_reel_script(summary, keywords)
        images = download_and_process_images(keywords)
        if not images:
            raise Exception("No valid images downloaded")

        success = create_video_from_script(script, images)

        if success:
            print("Video created successfully!")
        else:
            print("Video creation failed.")

    except Exception as e:
        print(f"Error in video generation process: {e}")

if _name_ == "_main_":
    pdf_path = "/content/a257-mehta stamped.pdf"  # Original path
    generate_reel_video(pdf_path)