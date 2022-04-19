import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

import configparser

config = configparser.ConfigParser()
config.read("smtp.config")
email=config["default"]["email"]
password=config["default"]["password"]
smtp_server=config["default"]["smtp_server"]
smtp_port=config["default"]["smtp_port"]


email=config["default"]["email"]
password=config["default"]["password"]
smtp_server=config["default"]["smtp_server"]
smtp_port=config["default"]["smtp_port"]


mail_content = '''Hello,
This is a test mail.
In this mail we are sending some attachments.
The mail is sent using Python SMTP library.
Thank You
'''
#The mail addresses and password
sender_address = email
sender_pass = password
receiver_address = 'cywong@vtc.edu.hk'
#Setup the MIME
message = MIMEMultipart()
message['From'] = sender_address
message['To'] = receiver_address
message['Subject'] = 'A test mail sent by Python. It has an attachment.'
#The subject line
#The body and the attachments for the mail
message.attach(MIMEText(mail_content, 'plain'))
attach_file_name = "output/marks/1.pdf"
attach_file = open(attach_file_name, 'rb') # Open the file as binary mode
payload = MIMEBase('application', 'octate-stream')
payload.set_payload((attach_file).read())
encoders.encode_base64(payload) #encode the attachment
#add payload header with filename
payload.add_header('Content-Decomposition', 'attachment', filename=attach_file_name)
message.attach(payload)
#Create SMTP session for sending the mail
session = smtplib.SMTP(smtp_server, int(smtp_port),source_address=("127.0.0.1", 0))#use gmail with port
session.starttls() #enable security
session.ehlo()
session.login(sender_address, sender_pass) #login with mail_id and password
text = message.as_string()
session.sendmail(sender_address, receiver_address, text)
session.quit()
print('Mail Sent')