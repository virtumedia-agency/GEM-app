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
            
        # Convert Markdown key elements to HTML
        html_content = content.replace('\n', '<br>')
        html_content = html_content.replace('**', '<b>').replace('**', '</b>') # Simple bold replacement
        html_content = html_content.replace('# ', '<h1>').replace('## ', '<h2>')
        html_content = html_content.replace('---', '<hr>')
        
        # Style the table
        if '|' in html_content:
             # Basic table conversion (very simple, assumes correct markdown table format)
             rows = [r for r in content.split('\n') if '|' in r]
             table_html = '<table style="width:100%; border-collapse: collapse; margin-top: 10px;">'
             
             # Header
             header_cols = [c.strip() for c in rows[0].split('|') if c.strip()]
             table_html += '<tr style="background-color: #f2f2f2;">'
             for hc in header_cols:
                 table_html += f'<th style="border: 1px solid #ddd; padding: 8px; text-align: left;">{hc}</th>'
             table_html += '</tr>'
             
             # Body (skipping separator row |---|)
             for row in rows[2:]:
                 cols = [c.strip() for c in row.split('|') if c.strip()]
                 if cols:
                     table_html += '<tr>'
                     for c in cols:
                         table_html += f'<td style="border: 1px solid #ddd; padding: 8px;">{c}</td>'
                     table_html += '</tr>'
             table_html += '</table>'
             
             # Replace the markdown table block in the content with the HTML table
             # This is a bit tricky with simple string replace, so we construct a new body
             # Instead, let's just make a cleaner professional HTML template using the decision logic directly if possible,
             # but since we only have 'content' string here, let's wrap the whole thing in a nice container 
             # and rely on the <pre> block for the parts we didn't assist.
             pass

        # Let's use a cleaner approach: Create a nice HTML wrapper and put the text content in a pre-wrap div
        # BUT user wants "more readable" than markdown source.
        # Let's try to convert the provided Markdown string to basic HTML structure manually for better UX
        
        # Better Strategy: Render a proper HTML template
        # Since we just have the string here, let's format it simply but nicely
        
        formatted_body = content.replace("RISK-ON", "<span style='color: green; font-weight: bold;'>RISK-ON</span>")
        formatted_body = formatted_body.replace("RISK-OFF", "<span style='color: red; font-weight: bold;'>RISK-OFF</span>")
        formatted_body = formatted_body.replace("BUY", "<span style='color: green; font-weight: bold;'>BUY</span>")
        formatted_body = formatted_body.replace("SELL", "<span style='color: red; font-weight: bold;'>SELL</span>")
        
        # Convert newlines to breaks for the non-table parts, but keep pre-formatting for table
        # Actually, standard <pre> tag is the safest for Markdown if we don't use a library like 'markdown'
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .card {{ background: #ffffff; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); padding: 24px; border: 1px solid #e1e4e8; }}
                h1 {{ color: #1a7f37; font-size: 24px; border-bottom: 2px solid #eaecef; padding-bottom: 10px; }}
                .decision {{ font-size: 18px; background: #f6f8fa; padding: 15px; border-left: 5px solid #0366d6; margin: 20px 0; }}
                pre {{ background: #f6f8fa; padding: 16px; border-radius: 6px; overflow: auto; font-size: 13px; }}
                hr {{ border: 0; border-top: 1px solid #eaecef; margin: 24px 0; }}
                .footer {{ font-size: 12px; color: #6a737d; text-align: center; margin-top: 24px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="card">
                    <b>Raport GEM ETF</b>
                    <div style="white-space: pre-wrap;">{formatted_body}</div>
                </div>
                <div class="footer">
                    Automated email from GEM ETF Decision App
                </div>
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
