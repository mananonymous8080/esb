import smtplib
from email.message import EmailMessage
from datetime import datetime, timedelta
from dateutil import parser
import os


SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
ADMIN_EMAIL = os.environ["ADMIN_EMAIL"]
SMTP_SENDER_PASSWORD = os.environ["SMTP_SENDER_PASSWORD"]  # Use app password if using Gmail

def send_booking_email(name, email, mobile, exam_name, exam_date, exam_time):
    recipients = [ADMIN_EMAIL, email]  # Sends to both admin and user

    msg = EmailMessage()
    msg['Subject'] = f'Exam Slot Confirmed: {exam_name}'
    msg['From'] = ADMIN_EMAIL
    msg['To'] = ', '.join(recipients)

    body = f"""
📚 Exam Slot Booked Successfully!

👤 Name: {name}
📧 Email: {email}
📱 Mobile: {mobile}
📘 Exam: {exam_name}
📅 Date: {exam_date}
⏰ Time: {exam_time}

A calendar invite is attached for your convenience. Please check your inbox and calendar.
"""

    msg.set_content(body)

    # Create datetime objects
    start_datetime = parser.parse(f"{exam_date} {exam_time}")
    start_datetime_utc = start_datetime - timedelta(hours=5, minutes=30)
    end_datetime_utc = start_datetime_utc + timedelta(hours=1)

    # Build .ics calendar content
    ics_content = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//ExamSlotSystem//EN
BEGIN:VEVENT
UID:{start_datetime_utc.timestamp()}@exam-slot.com
DTSTAMP:{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}
DTSTART:{start_datetime_utc.strftime('%Y%m%dT%H%M%SZ')}
DTEND:{end_datetime_utc.strftime('%Y%m%dT%H%M%SZ')}
SUMMARY:Exam Slot - {exam_name}
DESCRIPTION:Exam for {name} at {exam_time}
LOCATION:Online
STATUS:CONFIRMED
END:VEVENT
END:VCALENDAR
"""


    # Attach calendar invite
    msg.add_attachment(
    ics_content.encode('utf-8'),
    maintype='text',
    subtype='calendar',
    filename='exam_invite.ics'
    )


    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(ADMIN_EMAIL, SMTP_SENDER_PASSWORD)
            smtp.send_message(msg)
            print("📧 Email with calendar invite sent to admin and user.")
    except Exception as e:
        print(f"❌ Error sending email: {e}")
