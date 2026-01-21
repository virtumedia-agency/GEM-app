import resend
import os
from typing import Dict, Optional

class EmailSender:
    def __init__(self, config: Dict):
        api_key = os.environ.get("RESEND_API_KEY")
        if not api_key:
            print("Warning: RESEND_API_KEY not found in environment variables.")
        
        resend.api_key = api_key
        self.config = config['email']

    def send_email(self, subject: str, content: str) -> Dict:
        """
        Sends an email using Resend API.
        """
        if not resend.api_key:
            print("Skipping email send: No API Key.")
            return {"id": "skipped"}
            
        # Wrap Markdown in simple HTML for better readability in clients that support it
        # Converting updates line breaks to <br> would be better, but <pre> preserves formatting
        html_content = f"""
        <html>
            <body style="font-family: sans-serif; line-height: 1.5;">
                <div style="background-color: #f4f4f4; padding: 20px;">
                    <div style="background-color: #fff; padding: 20px; border-radius: 5px; white-space: pre-wrap; font-family: monospace;">
{content}
                    </div>
                    <p style="font-size: 12px; color: #888; margin-top: 20px;">
                        This is an automated message from GEM ETF Decision App.
                    </p>
                </div>
            </body>
        </html>
        """
        
        params = {
            "from": self.config['from'],
            "to": [self.config['to']],
            "subject": subject,
            "text": content,
            "html": html_content
        }
        
        try:
            email = resend.Emails.send(params)
            print(f"Email sent! ID: {email.get('id')}")
            return email
        except Exception as e:
            print(f"Failed to send email: {e}")
            # Don't crash the main app, just log error? 
            # PRD FR-07.4 says "error logowany". Raising allows main.py to catch and log.
            raise e
