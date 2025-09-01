import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import os
from dotenv import get_key, dotenv_values
import re
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

__all__ = ['send_email', 'extract_email_info_from_query', 'send_email_manually']

def send_email(recipient, subject, body, attachments=None):
    """
    Send an email with optional attachments.
    Returns True on success, False on failure.
    """
    try:
        sender_email = get_key(".env", "EMAIL_ADDRESS")
        sender_password = get_key(".env", "EMAIL_PASSWORD")
        smtp_server = get_key(".env", "SMTP_SERVER")
        smtp_port = int(get_key(".env", "SMTP_PORT"))

        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient
        msg['Subject'] = subject
        
        enhanced_body = f"{body}\n\n---\n<p style='font-size:small;color:gray;'>Sent by Dobby AI</p>"
        msg.attach(MIMEText(enhanced_body, 'html'))

        if attachments:
            for file_path in attachments:
                if os.path.isfile(file_path):
                    with open(file_path, "rb") as f:
                        part = MIMEApplication(f.read(), Name=os.path.basename(file_path))
                        part['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
                        msg.attach(part)
                else:
                    logging.debug(f"Attachment not found: {file_path}")

        with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
            server.login(sender_email, sender_password)
            server.send_message(msg)
            logging.info(f"Email sent successfully to {recipient}")
            return True

    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return False

import logging

def extract_email_info_from_query(query):
    """
    Extract the main message from a natural language query for email.
    Returns (recipient, message, message) for LLM formatting.
    """
    import re
    logger = logging.getLogger(__name__)
    original_query = query.strip()

    # Remove only the leading command phrase (case-insensitive)
    cleaned_query = re.sub(
        r'^(send|compose|write|draft)\s+(an?\s+)?(email|mail|message)?\s*(about|regarding|for|saying|to say|that says)?\s*',
        '',
        original_query,
        flags=re.IGNORECASE
    ).strip(" '\"\n\t")

    if not cleaned_query:
        logger.debug(f"[extract_email_info_from_query] Empty after cleaning: '{original_query}'")
        return None, "No Subject", ""

    # Use the remaining phrase as both subject and body (let LLM handle formatting)
    logger.debug(f"[extract_email_info_from_query] Extracted message: '{cleaned_query}' from: '{original_query}'")
    return None, cleaned_query, cleaned_query


def format_email_with_llm(body, provider="groq"):
    """
    Format email using LLM to make it more professional.
    Supports both Groq and Cohere APIs with fallback to simple formatting.
    
    Args:
        body (str): The email body content to format
        provider (str): Which LLM provider to use ('groq' or 'cohere')
        
    Returns:
        tuple: (subject, formatted_body)
    """
    if not body or not body.strip():
        return "No Subject", ""
        
    # Get API keys from environment
    env_vars = dotenv_values(".env")
    GROQ_API_KEY = env_vars.get("GROQ_API_KEY")
    COHERE_API_KEY = env_vars.get("COHERE_API_KEY")
    
    # Common prompt for both providers
    prompt = f"""
You are an expert email assistant. Please help format this email in a professional manner.

Instructions:
1. Generate a concise, clear subject line (max 10 words)
2. Format the body with proper greeting, paragraphs, and closing
3. Keep the original meaning but make it more professional
4. Use proper email etiquette
5. If the message is very short, expand it appropriately
6. Output as JSON with 'subject' and 'body' fields

Input message to format:
{body}

Example output format:
{{
  "subject": "Meeting Reschedule Request",
  "body": "Dear [Name],\n\nI hope this message finds you well..."
}}"""

    # Try Cohere API first if selected and key available
    if provider == "cohere" and COHERE_API_KEY:
        try:
            import requests
            url = "https://api.cohere.ai/v1/chat"
            headers = {
                "Authorization": f"Bearer {COHERE_API_KEY}", 
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            data = {
                "message": prompt,
                "model": "command-r-plus",
                "temperature": 0.4,
                "max_tokens": 1000
            }
            resp = requests.post(url, headers=headers, json=data, timeout=10)
            resp.raise_for_status()
            result = resp.json()
            
            # Parse the response
            try:
                import json
                content = result.get("text", "").strip()
                if content.startswith('```json'):
                    content = content[content.find('{'):content.rfind('}')+1]
                result_data = json.loads(content)
                return (
                    result_data.get("subject", "No Subject").strip() or "No Subject",
                    result_data.get("body", body).strip() or body
                )
            except (json.JSONDecodeError, AttributeError) as e:
                logger.warning(f"Failed to parse Cohere response: {e}")
                # Fall through to Groq or simple formatting
                
        except Exception as e:
            logger.error(f"Cohere API error: {e}")
            if provider == "cohere":  # Only fall through if Cohere was explicitly requested
                provider = "groq"
    
    # Try Groq API if selected and key available
    if provider == "groq" and GROQ_API_KEY:
        try:
            import requests
            url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {GROQ_API_KEY}", 
                "Content-Type": "application/json"
            }
            data = {
                "model": "mixtral-8x7b-32768",
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant that formats emails professionally."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.4,
                "max_tokens": 1000,
                "response_format": {"type": "json_object"}
            }
            resp = requests.post(url, headers=headers, json=data, timeout=10)
            resp.raise_for_status()
            
            # Parse the response
            try:
                content = resp.json()["choices"][0]["message"]["content"]
                import json
                result_data = json.loads(content.strip())
                return (
                    result_data.get("subject", "No Subject").strip() or "No Subject",
                    result_data.get("body", body).strip() or body
                )
            except (json.JSONDecodeError, KeyError, IndexError) as e:
                logger.warning(f"Failed to parse Groq response: {e}")
                
        except Exception as e:
            logger.error(f"Groq API error: {e}")
    
    # Fallback: Simple formatting if APIs fail or no keys available
    subject = body[:100].strip()
    if len(subject) > 50:
        subject = subject[:47] + "..."
    
    formatted_body = f"""{body}

Best regards,
{env_vars.get('Username', '')}"""
    
    return subject, formatted_body

import tkinter as tk
from tkinter import simpledialog, messagebox

def prompt_for_email_address():
    """Prompt user to enter email address via GUI dialog"""
    try:
        root = tk.Tk()
        root.withdraw()
        recipient = simpledialog.askstring("Recipient Email", "Please enter the recipient's email address:")
        root.destroy()
        if not recipient or '@' not in recipient:
            messagebox.showerror("Invalid Email", "Invalid email address format.")
            return None
        return recipient
    except Exception as e:
        logger.error(f"Error getting email input: {e}")
        return None

def prompt_for_subject():
    try:
        root = tk.Tk()
        root.withdraw()
        subject = simpledialog.askstring("Email Subject", "Please enter the subject:")
        root.destroy()
        return subject if subject else "No Subject"
    except Exception as e:
        logger.error(f"Error getting subject input: {e}")
        return "No Subject"

def prompt_for_body():
    try:
        root = tk.Tk()
        root.withdraw()
        body = simpledialog.askstring("Email Message", "Please enter the message:")
        root.destroy()
        return body if body else ""
    except Exception as e:
        logger.error(f"Error getting body input: {e}")
        return ""

def send_email_with_manual_input(body=None):
    """Send email with manual input for recipient, subject, and body using GUI dialogs
    
    Args:
        body (str, optional): Pre-filled email body. If None, will prompt user for body.
    """
    try:
        recipient = prompt_for_email_address()
        if not recipient:
            return False
            
        # Get subject and body if not provided
        subject = prompt_for_subject()
        if body is None:
            body = prompt_for_body()
            
        # Optionally format with LLM
        subject, formatted_body = format_email_with_llm(body)
        
        # Show confirmation
        root = tk.Tk()
        root.withdraw()
        confirm = messagebox.askyesno(
            "Confirm Email", 
            f"Send email to: {recipient}\n\n"
            f"Subject: {subject}\n\n"
            f"Message:\n{formatted_body}\n\n"
            "Send this email?"
        )
        root.destroy()
        
        if not confirm:
            return False
            
        success = send_email(recipient, subject, formatted_body)
        return success
    except Exception as e:
        logger.error(f"Error in manual email input: {e}", exc_info=True)
        return False

def send_email_manually():
    """Legacy function that calls send_email_with_manual_input for backward compatibility"""
    try:
        success = send_email_with_manual_input()
        if success:
            return "Email sent successfully!"
        else:
            return "Failed to send email or operation was cancelled."
    except Exception as e:
        logger.error(f"Error in send_email_manually: {e}", exc_info=True)
        return f"I encountered an error: {str(e)}"
