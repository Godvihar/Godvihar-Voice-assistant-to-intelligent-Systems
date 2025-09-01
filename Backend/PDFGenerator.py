import os
import subprocess
from fpdf import FPDF
# --- PDFGenerator.py ---
from Backend.Chatbot import ChatBot

def generate_dynamic_content(user_prompt):
    """Generates AI-based dynamic content dynamically from user's voice query."""
    ai_generated_content = ChatBot(user_prompt)
    return ai_generated_content


def open_notepad_and_wait(input_txt_path, initial_content=None):
    try:
        with open(input_txt_path, "w", encoding='utf-8') as f:
            if initial_content:
                f.write(initial_content)
            else:
                f.write("")

        print(f"[INFO] Opening Notepad for file: {input_txt_path}")
        subprocess.run(["notepad.exe", input_txt_path], check=True)
        print("[INFO] Notepad closed by user. Proceeding to generate PDF...")

    except Exception as e:
        print(f"[ERROR] Failed to open Notepad: {e}")


def convert_text_to_pdf(input_txt_path, output_pdf_path):
    try:
        # Read the content from the text file
        with open(input_txt_path, "r", encoding='utf-8') as file:
            text = file.read().strip()

        if not text:
            print("[WARNING] Text file is empty. PDF will not be generated.")
            return

        # Create a new PDF document
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        # Split the content by lines
        lines = text.split('\n')
        for line in lines:
            # Bold titles if they start with "**"
            if line.startswith("**") and line.endswith("**"):
                title = line.strip("*").strip()
                pdf.set_font("Arial", 'B', 16)
                pdf.cell(200, 10, txt=title, ln=True, align='C')
                pdf.ln(5)
                pdf.set_font("Arial", size=12)
            else:
                pdf.multi_cell(0, 10, line)

        # Save the PDF to the specified output path
        pdf.output(output_pdf_path)
        print(f"[INFO] PDF generated successfully: {output_pdf_path}")

    except Exception as e:
        print(f"[ERROR] Failed to create PDF: {e}")

def open_pdf(output_pdf_path):
    try:
        # Open the generated PDF
        full_pdf_path = os.path.abspath(output_pdf_path)
        os.startfile(full_pdf_path)
        print(f"[INFO] PDF opened: {full_pdf_path}")
    except Exception as e:
        print(f"[ERROR] Failed to open PDF: {e}")

def get_content_type_from_voice(command):
    # Keywords that can be detected from the voice command to identify content type
    keywords = ["letter", "story", "lyrics", "article", "note", "summary"]
    for keyword in keywords:
        if keyword in command.lower():
            return keyword
    return "generic"  # Default content type

if __name__ == "__main__":
    # --- Remove all this ---
    user_command = "Write a story about a dragon in a magical forest"
    content_type = get_content_type_from_voice(user_command)

    base_path = "C:\\Users\\vihar\\OneDrive\\Desktop\\Jarvis AI\\Data"
    os.makedirs(base_path, exist_ok=True)

    input_txt_path = os.path.join(base_path, f"{content_type}.txt")
    output_pdf_path = os.path.join(base_path, f"{content_type}.pdf")

    open_notepad_and_wait(input_txt_path)
    convert_text_to_pdf(input_txt_path, output_pdf_path)
    open_pdf(output_pdf_path)
