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
            
        import re

        # Basic Markdown to HTML converter
        html_body = content
        
        # 1. Colors and Bolding specific keywords
        html_body = html_body.replace("RISK-ON", "<span style='color: green; font-weight: bold;'>RISK-ON</span>")
        html_body = html_body.replace("RISK-OFF", "<span style='color: red; font-weight: bold;'>RISK-OFF</span>")
        html_body = html_body.replace("BUY", "<span style='color: green; font-weight: bold;'>BUY</span>")
        html_body = html_body.replace("HOLD/SELL", "<span style='color: #d73a49; font-weight: bold;'>HOLD/SELL</span>")
        html_body = html_body.replace("SELL", "<span style='color: red; font-weight: bold;'>SELL</span>")

        # 2. Headers
        # # Header -> <h1>Header</h1>
        html_body = re.sub(r'^# (.+)$', r'<h1 style="color: #0366d6; font-size: 24px; border-bottom: 1px solid #eaecef; padding-bottom: 0.3em;">\1</h1>', html_body, flags=re.MULTILINE)
        # ## Header -> <h2>Header</h2>
        html_body = re.sub(r'^## (.+)$', r'<h2 style="font-size: 20px; border-bottom: 1px solid #eaecef; padding-bottom: 0.3em; margin-top: 24px;">\1</h2>', html_body, flags=re.MULTILINE)

        # 3. Bold (**text**)
        html_body = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', html_body)

        # 4. Horizontal Rule (---)
        html_body = re.sub(r'^\s*---\s*$', r'<hr style="border: 0; border-top: 2px solid #eaecef; margin: 20px 0;">', html_body, flags=re.MULTILINE)
        
        # 5. Lists (- Item)
        # Replace lines starting with "- " with a styled list item span
        html_body = re.sub(r'^-\s+(.+)$', r'<div style="margin-left: 20px; margin-bottom: 5px;">• \1</div>', html_body, flags=re.MULTILINE)

        # 6. Tables
        # This is simple/fragile parsing but works for the predictable table format in reporter.py
        # Find the table block (lines starting with |)
        lines = html_body.split('\n')
        new_lines = []
        in_table = False
        
        table_style = 'width: 100%; border-collapse: collapse; margin-top: 15px; margin-bottom: 15px; font-size: 14px;'
        th_style = 'border: 1px solid #dfe2e5; padding: 6px 13px; background-color: #f6f8fa; font-weight: bold; text-align: left;'
        td_style = 'border: 1px solid #dfe2e5; padding: 6px 13px;'
        
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('|'):
                if '---' in stripped: # Skip separator line
                    continue
                    
                cols = [c.strip() for c in stripped.strip('|').split('|')]
                
                if not in_table:
                    # Start of table (Header)
                    in_table = True
                    new_lines.append(f'<table style="{table_style}">')
                    new_lines.append('<thead><tr>')
                    for c in cols:
                        new_lines.append(f'<th style="{th_style}">{c}</th>')
                    new_lines.append('</tr></thead><tbody>')
                else:
                    # Table Body Row
                    new_lines.append('<tr>')
                    for c in cols:
                        new_lines.append(f'<td style="{td_style}">{c}</td>')
                    new_lines.append('</tr>')
            else:
                if in_table:
                    # End of table
                    in_table = False
                    new_lines.append('</tbody></table>')
                
                # Handling empty lines for paragraph breaks in non-table content
                if line.strip() == "":
                    new_lines.append('<div style="height: 10px;"></div>')
                else:
                    # Check if line is already an HTML tag (h1, h2, hr, div list)
                    if line.strip().startswith('<'):
                        new_lines.append(line)
                    else:
                        new_lines.append(f'<div>{line}</div>')

        # Close table if still open at end
        if in_table:
            new_lines.append('</tbody></table>')
            
        html_body = "\n".join(new_lines)
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; color: #24292e; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .card {{ background: #ffffff; border-radius: 6px; border: 1px solid #e1e4e8; padding: 32px; }}
                .footer {{ font-size: 12px; color: #586069; text-align: center; margin-top: 24px; }}
            </style>
        </head>
        <body style="background-color: #f6f8fa;">
            <div class="container">
                <div class="card">
                    {html_body}
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
