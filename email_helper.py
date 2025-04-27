import smtplib
from email.message import EmailMessage
from datetime import datetime, timedelta
from dateutil import parser
import os

SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
ADMIN_EMAIL = os.environ["ADMIN_EMAIL"]
SMTP_SENDER_PASSWORD = os.environ["SMTP_SENDER_PASSWORD"]

def send_booking_email(name, email, mobile, service_type, service_name, service_date=None, service_time=None, description=''):
    recipients = [ADMIN_EMAIL, email]

    msg = EmailMessage()
    msg['Subject'] = f'Slot Booked: {service_name}'
    msg['From'] = ADMIN_EMAIL
    msg['To'] = ', '.join(recipients)

    body = f"""
🎉 Slot Booked Successfully!

👤 Name: {name}
📧 Email: {email}
📱 Mobile: {mobile}
🏷️ Service: {service_type} - {service_name}
{f"📅 Date: {service_date}" if service_date else ""}
{f"⏰ Time: {service_time}" if service_time else ""}
{f"📝 Description: {description}" if description else ""}
.
.
Thank you for booking with us! 🙌. We'll contact you shortly.
.
.
Regards,  
yourexamhelper.com
"""

    # Clean multiple blank lines from body
    body = "\n".join([line for line in body.splitlines() if line.strip() != ""])

    msg.set_content(body)

    # 🗓️ Attach calendar invite if both date & time are provided
    if service_date and service_time:
        try:
            start_datetime = parser.parse(f"{service_date} {service_time}")
            start_datetime_utc = start_datetime - timedelta(hours=5, minutes=30)  # Convert IST -> UTC
            end_datetime_utc = start_datetime_utc + timedelta(hours=1)

            ics_content = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//SlotBookingSystem//EN
BEGIN:VEVENT
UID:{start_datetime_utc.timestamp()}@slot-booking.com
DTSTAMP:{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}
DTSTART:{start_datetime_utc.strftime('%Y%m%dT%H%M%SZ')}
DTEND:{end_datetime_utc.strftime('%Y%m%dT%H%M%SZ')}
SUMMARY:Slot Booking - {service_name}
DESCRIPTION:Service for {name} at {service_time}
LOCATION:Online
STATUS:CONFIRMED
END:VEVENT
END:VCALENDAR
"""

            msg.add_attachment(
                ics_content.encode('utf-8'),
                maintype='text',
                subtype='calendar',
                filename='slot_invite.ics'
            )
            print("📎 Calendar invite attached.")
        except Exception as e:
            print(f"⚠️ Could not generate calendar invite: {e}")

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(ADMIN_EMAIL, SMTP_SENDER_PASSWORD)
            smtp.send_message(msg)
            print("📧 Email sent successfully to admin and user.")
    except Exception as e:
        print(f"❌ Error sending email: {e}")
