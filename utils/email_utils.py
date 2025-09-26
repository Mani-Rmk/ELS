import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from core.config import SMTP_SERVER, SMTP_PORT, EMAIL_ADDRESS, EMAIL_PASSWORD
from passlib.context import CryptContext

def send_email(to_email: str, subject: str, body_text: str, body_html: str = None, cc: list = None, bcc: list = None):

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = to_email

    # Add CC if provided
    if cc:
        msg["Cc"] = ", ".join(cc)

    # Attach plain text
    part1 = MIMEText(body_text, "plain")
    msg.attach(part1)

    # Attach HTML if provided
    if body_html:
        part2 = MIMEText(body_html, "html")
        msg.attach(part2)

    # Final recipient list (to + cc + bcc)
    recipients = [to_email]
    if cc:
        recipients.extend(cc)
    if bcc:
        recipients.extend(bcc)

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.sendmail(EMAIL_ADDRESS, recipients, msg.as_string())
        print(f"✅ Email sent to {to_email} (CC: {cc if cc else 'None'})")
        return True
    except Exception as e:
        print(f"❌ Failed to send email to {to_email}: {e}")
        return False
    
def hash_password(password: str) -> str:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    return pwd_context.hash(password)
