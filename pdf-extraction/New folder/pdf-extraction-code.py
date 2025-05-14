import fitz  # PyMuPDF
import re
import json
import os
import base64
from bs4 import BeautifulSoup
import html
from PIL import Image
import io
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("extraction.log"),
        logging.StreamHandler()
    ]
)
def extract_questions_from_pdf(pdf_path, output_dir):
    """
    Extract questions from PDF while preserving formatting.
    
    This function processes a PDF containing nuclear engineering questions,
    extracts each question (one per page), preserves formatting including
    superscripts, subscripts, tables, and special characters.
    
    Args:
        pdf_path: Path to the PDF file
        output_dir: Directory to save the extracted data
    
    Returns:
        List of extracted question objects
    """
    # Create output directories
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(os.path.join(output_dir, "images"), exist_ok=True)
    
    # Open the PDF
    doc = fitz.open(pdf_path)
    total_pages = len(doc)
    logging.info(f"Processing PDF with {total_pages} pages")
    
    questions = []
    
    # Process each page (question)
    for page_num in range(total_pages):
        if page_num % 50 == 0:
            logging.info(f"Processing page {page_num+1}/{total_pages}")
        
        page = doc[page_num]
        
        # Get raw HTML representation (preserves formatting)
        html_text = page.get_text("html")
        soup = BeautifulSoup(html_text, 'html.parser')
        
        # Extract topic
        topic_match = re.search(r"TOPIC:\s*(.*?)(?:\n|$)", page.get_text())
        topic = topic_match.group(1).strip() if topic_match else "Unknown"
        
        # Extract answer
        answer_match = re.search(r"ANSWER:\s*([A-D])\.?", page.get_text())
        answer = answer_match.group(1) if answer_match else None
        
        # Extract full question text with formatting
        question_html = extract_question_content(soup)
        
        # Extract options A, B, C, D
        options = extract_options(soup, page.get_text())
        
        # Extract images if present
        images = extract_images(doc, page, page_num, output_dir)
        
        # Create question object
        question = {
            "id": page_num + 1,
            "topic": topic,
            "question_html": clean_html(question_html),
            "options": [clean_html(opt) for opt in options],
            "answer": answer,
            "images": images,
            "page_number": page_num + 1
        }
        
        questions.append(question)
    
    # Save questions to JSON file
    output_file = os.path.join(output_dir, "nuclear_questions.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(questions, f, ensure_ascii=False, indent=2)
    
    logging.info(f"Extracted {len(questions)} questions to {output_file}")
    
    # Save topics list
    topics = list(set(q["topic"] for q in questions))
    topics_file = os.path.join(output_dir, "topics.json")
    with open(topics_file, "w", encoding="utf-8") as f:
        json.dump(topics, f, ensure_ascii=False, indent=2)
    
    logging.info(f"Found {len(topics)} unique topics")
    
    return questions
    def extract_question_content(soup):
    def extract_question_content(soup):
    """Extract the main question content from the HTML soup"""
    # Find content between TOPIC and first option (A)
    content = ""
    in_question = False
    
    for element in soup.find_all(['p', 'div']):
        # Rest of the function...
        text = element.get_text().strip()
        
        # Start extracting after we see "TOPIC:"
        if not in_question and "TOPIC:" in text:
            in_question = True
            continue
        
        # Stop when we reach option A
        if in_question and re.match(r"^\s*A\.\s", text):
            break
        
        # Collect the question content
        if in_question:
            content += str(element)
    
    return content
    def extract_options(soup, page_text):
    """Extract the options (A, B, C, D) with formatting preserved"""
    options = []
    
    # Find option blocks in the text
    option_pattern = r"([A-D])\.\s+(.*?)(?=\s+[A-D]\.\s+|\s+ANSWER:|$)"
    option_matches = re.findall(option_pattern, page_text, re.DOTALL)
    
    for letter, text in option_matches:
        # Clean up the text but preserve formatting
        option_html = ""
        
        # Find the corresponding HTML in the soup
        for element in soup.find_all(['p', 'div']):
            element_text = element.get_text().strip()
            if letter + "." in element_text and text.strip() in element_text:
                # Remove the option letter prefix
                element_html = str(element)
                element_html = re.sub(r"<[^>]*>\s*" + letter + r"\.\s*</[^>]*>", "", element_html)
                option_html = element_html
                break
        
        if not option_html:
            # Fallback to just the text if we couldn't find the HTML
            option_html = f"<p>{text.strip()}</p>"
        
        options.append(option_html)
    
    # Make sure we got 4 options - sometimes the regex doesn't catch everything
    if len(options) != 4:
        # Try an alternate approach
        options = []
        option_letters = ['A', 'B', 'C', 'D']
        
        for letter in option_letters:
            # Look for pattern "{letter}. text"
            for element in soup.find_all(['p', 'div']):
                element_text = element.get_text().strip()
                if element_text.startswith(f"{letter}."):
                    option_text = element_text[len(f"{letter}."):]
                    options.append(f"<p>{option_text.strip()}</p>")
                    break
            else:
                # If not found, add a placeholder
                options.append(f"<p>Option {letter} (not found)</p>")
    
    return options
    def extract_images(doc, page, page_num, output_dir):
    """Extract and save images from the page"""
    images = []
    
    # Extract images using PyMuPDF
    for img_index, img in enumerate(page.get_images(full=True)):
        xref = img[0]
        base_image = doc.extract_image(xref)
        image_bytes = base_image["image"]
        
        # Save the image
        image_filename = f"question_{page_num+1}_img_{img_index+1}.png"
        image_path = os.path.join(output_dir, "images", image_filename)
        
        with open(image_path, "wb") as img_file:
            img_file.write(image_bytes)
        
        images.append(image_filename)
    
    # If images weren't found through PyMuPDF's get_images(), try alternative approach
    if not images:
        # Try to extract as a page image if there might be figures/diagrams
        pixmap = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # Higher resolution
        image_bytes = pixmap.tobytes()
        
        # Convert to PIL Image for processing
        pil_img = Image.open(io.BytesIO(image_bytes))
        
        # Save only if it seems to have useful content (e.g., diagrams)
        # This is a simplified heuristic - you might need to adjust
        if has_diagram_content(pil_img):
            image_filename = f"question_{page_num+1}_full_page.png"
            image_path = os.path.join(output_dir, "images", image_filename)
            pil_img.save(image_path)
            images.append(image_filename)
    
    return images
    def has_diagram_content(img):
    """
    Basic heuristic to determine if an image likely contains diagrams.
    This is just a simplified example - real implementation would be more sophisticated.
    """
    # Convert to grayscale for analysis
    gray_img = img.convert('L')
    
    # Count non-white pixels
    non_white_pixels = sum(1 for pixel in gray_img.getdata() if pixel < 240)
    total_pixels = gray_img.width * gray_img.height
    
    # If more than 5% non-white, likely has content
    return non_white_pixels > (total_pixels * 0.05)

def clean_html(html_content):
    """Clean HTML content while preserving formatting"""
    if not html_content:
        return ""
    
    # Remove excessive whitespace but preserve tags
    html_content = re.sub(r'\s+', ' ', html_content)
    
    # Ensure subscripts and superscripts are properly formatted
    html_content = re.sub(r'<sub>(.*?)</sub>', r'<sub>\1</sub>', html_content)
    html_content = re.sub(r'<sup>(.*?)</sup>', r'<sup>\1</sup>', html_content)
    
    # Fix common formatting issues
    # Convert plain text fractions to proper HTML
    html_content = re.sub(r'(\d+)/(\d+)', r'<span class="fraction">\1/\2</span>', html_content)
    
    # Fix special characters
    html_content = html_content.replace('&nbsp;', ' ')
    
    return html_content
    def create_sqlite_database(questions, db_path):
    """Create an SQLite database from the extracted questions"""
    import sqlite3
    
    # Connect to the database (will create if it doesn't exist)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS topics (
        id INTEGER PRIMARY KEY,
        name TEXT UNIQUE
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS questions (
        id INTEGER PRIMARY KEY,
        topic_id INTEGER,
        question_html TEXT,
        answer TEXT,
        page_number INTEGER,
        FOREIGN KEY (topic_id) REFERENCES topics (id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS options (
        id INTEGER PRIMARY KEY,
        question_id INTEGER,
        option_letter TEXT,
        option_html TEXT,
        FOREIGN KEY (question_id) REFERENCES questions (id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS images (
        id INTEGER PRIMARY KEY,
        question_id INTEGER,
        image_path TEXT,
        FOREIGN KEY (question_id) REFERENCES questions (id)
    )
    ''')
    
    # Insert topics
    topics = set(q["topic"] for q in questions)
    topic_id_map = {}
    
    for topic in topics:
        cursor.execute('INSERT OR IGNORE INTO topics (name) VALUES (?)', (topic,))
        cursor.execute('SELECT id FROM topics WHERE name = ?', (topic,))
        topic_id = cursor.fetchone()[0]
        topic_id_map[topic] = topic_id
    
    # Insert questions, options, and images
    for q in questions:
        cursor.execute('''
        INSERT INTO questions (id, topic_id, question_html, answer, page_number)
        VALUES (?, ?, ?, ?, ?)
        ''', (
            q["id"],
            topic_id_map[q["topic"]],
            q["question_html"],
            q["answer"],
            q["page_number"]
        ))
        
        # Insert options
        option_letters = ['A', 'B', 'C', 'D']
        for i, option_html in enumerate(q["options"]):
            if i < len(option_letters):
                cursor.execute('''
                INSERT INTO options (question_id, option_letter, option_html)
                VALUES (?, ?, ?)
                ''', (
                    q["id"],
                    option_letters[i],
                    option_html
                ))
        
        # Insert images
        for image_path in q["images"]:
            cursor.execute('''
            INSERT INTO images (question_id, image_path)
            VALUES (?, ?)
            ''', (
                q["id"],
                image_path
            ))
    
    conn.commit()
    conn.close()
    logging.info(f"Created SQLite database at {db_path}")
    if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Extract nuclear engineering questions from PDF")
    parser.add_argument("pdf_path", help="Path to the PDF file")
    parser.add_argument("--output-dir", default="extracted_data", help="Directory to save extracted data")
    parser.add_argument("--create-db", action="store_true", help="Create SQLite database")
    
    args = parser.parse_args()
    
    # Extract questions
    questions = extract_questions_from_pdf(args.pdf_path, args.output_dir)
    
    # Create database if requested
    if args.create_db:
        db_path = os.path.join(args.output_dir, "nuclear_quiz.db")
        create_sqlite_database(questions, db_path)
        
    logging.info("Extraction completed successfully")
    