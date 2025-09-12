# import boto3
# from botocore.exceptions import ClientError

# def send_email(recipient_email: str, subject: str, body: str):
#     # Initialize SES client
#     ses_client = boto3.client("ses", region_name="us-east-1")  # Change region if needed
    
#     sender_email = "sheel@holbox.ai"  # Must be verified in SES

#     try:
#         response = ses_client.send_email(
#             Source=sender_email,
#             Destination={"ToAddresses": [recipient_email]},
#             Message={
#                 "Subject": {"Data": subject, "Charset": "UTF-8"},
#                 "Body": {
#                     "Text": {"Data": body, "Charset": "UTF-8"},
#                 },
#             },
#         )
#         print("✅ Email sent! Message ID:", response["MessageId"])
#     except ClientError as e:
#         print("❌ Error:", e.response["Error"]["Message"])


# # Example usage
# if __name__ == "__main__":
#     send_email(
#         recipient_email="pavan.anumula@holbox.ai",
#         subject="Test Email from SES",
#         body="Hello! This is a test email sent via Amazon SES."
#     )


import boto3
from botocore.exceptions import ClientError
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage


def send_product_email(recipient_email: str, image1_path: str, image2_path: str, recipient_name: str = "Customer"):
    ses_client = boto3.client("ses", region_name="us-east-1")  # Change if using another SES region
    sender_email = "sheel@holbox.ai"  # Must be verified in SES

    # Create a multipart email (HTML + images)
    msg = MIMEMultipart("related")
    msg["Subject"] = "Your Product Look Preview"
    msg["From"] = sender_email
    msg["To"] = recipient_email

    # HTML body with inline image references
    html_body = f"""
    <html>
        <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
            <p>Dear {recipient_name},</p>
            
            <p>
                We are delighted to share with you an exclusive preview of how our jewellery looks when worn.
                Below, you’ll find your personalized virtual try-on images that reflect the elegance and charm 
                of the piece we recently discussed.
            </p>
            
            <p>
                <img src="cid:image1" style="max-width:400px; border-radius:12px; margin:10px 0;"/><br><br>
                <img src="cid:image2" style="max-width:400px; border-radius:12px; margin:10px 0;"/>
            </p>
            
            <p>
                Our collections are crafted to highlight individuality and timeless beauty — and we hope these 
                previews give you a glimpse of how effortlessly this design complements your style.
            </p>
            
            <p>
                Should you wish to explore more designs or schedule a private consultation, please let us know. 
                We would be delighted to assist you in finding the perfect piece.
            </p>
            
            <p>
                Warm regards,<br>
                <strong>The Shop LC Team</strong>
            </p>
        </body>
    </html>
    """


    msg_alt = MIMEMultipart("alternative")
    msg.attach(msg_alt)
    msg_alt.attach(MIMEText(html_body, "html"))

    # Attach images as inline
    with open(image1_path, "rb") as f:
        img1 = MIMEImage(f.read())
        img1.add_header("Content-ID", "<image1>")
        msg.attach(img1)

    with open(image2_path, "rb") as f:
        img2 = MIMEImage(f.read())
        img2.add_header("Content-ID", "<image2>")
        msg.attach(img2)

    try:
        response = ses_client.send_raw_email(
            Source=sender_email,
            Destinations=[recipient_email],
            RawMessage={"Data": msg.as_string()},
        )
        print("✅ Email sent! Message ID:", response["MessageId"])
    except ClientError as e:
        print("❌ Error:", e.response["Error"]["Message"])
        return {"Error": e.response["Error"]["Message"]}


# Example usage
# if __name__ == "__main__":
#     send_product_email(
#         recipient_email="pavan.anumula@holbox.ai",
#         recipient_name="Pavan",
#         image1_path="/home/ubuntu/chain.jpeg",
#         image2_path="/home/ubuntu/virtual_tryon/virtual_tryon_1757503453.png",
#     )

