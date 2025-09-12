# import argparse
# import mimetypes
# import os
# import time
# from google import genai
# from google.genai import types
# from dotenv import load_dotenv  # <-- NEW

# MODEL_NAME = "gemini-2.5-flash-image-preview"

# # Load environment variables from .env
# load_dotenv()


# def remix_images(
#     image_paths: list[str],
#     prompt: str,
#     output_dir: str,
# ):
#     """
#     Remixes images using the Google Generative AI model.

#     Args:
#         image_paths: A list of 1–5 input image paths.
#         prompt: The prompt for remixing the images.
#         output_dir: Directory to save the remixed images.
#     """
#     api_key = os.environ.get("GEMINI_API_KEY")
#     if not api_key:
#         raise ValueError("GEMINI_API_KEY environment variable not set in .env or system.")

#     client = genai.Client(api_key=api_key)

#     contents = _load_image_parts(image_paths)
#     contents.append(genai.types.Part.from_text(text=prompt))

#     generate_content_config = types.GenerateContentConfig(
#         response_modalities=["IMAGE", "TEXT"],
#     )

#     print(f"Remixing with {len(image_paths)} images and prompt: {prompt}")

#     stream = client.models.generate_content_stream(
#         model=MODEL_NAME,
#         contents=contents,
#         config=generate_content_config,
#     )

#     _process_api_stream_response(stream, output_dir)


# def _load_image_parts(image_paths: list[str]) -> list[types.Part]:
#     """Loads image files and converts them into GenAI Part objects."""
#     parts = []
#     for image_path in image_paths:
#         with open(image_path, "rb") as f:
#             image_data = f.read()
#         mime_type = _get_mime_type(image_path)
#         parts.append(
#             types.Part(inline_data=types.Blob(data=image_data, mime_type=mime_type))
#         )
#     return parts


# def _process_api_stream_response(stream, output_dir: str):
#     """Processes the streaming response from the GenAI API, saving images and printing text."""
#     file_index = 0
#     for chunk in stream:
#         if (
#             chunk.candidates is None
#             or chunk.candidates[0].content is None
#             or chunk.candidates[0].content.parts is None
#         ):
#             continue

#         for part in chunk.candidates[0].content.parts:
#             if part.inline_data and part.inline_data.data:
#                 timestamp = int(time.time())
#                 file_extension = mimetypes.guess_extension(part.inline_data.mime_type)
#                 file_name = os.path.join(
#                     output_dir,
#                     f"remixed_image_{timestamp}_{file_index}{file_extension}",
#                 )
#                 _save_binary_file(file_name, part.inline_data.data)
#                 file_index += 1
#             elif part.text:
#                 print(part.text)


# def _save_binary_file(file_name: str, data: bytes):
#     """Saves binary data to a specified file."""
#     with open(file_name, "wb") as f:
#         f.write(data)
#     print(f"File saved to: {file_name}")


# def _get_mime_type(file_path: str) -> str:
#     """Guesses the MIME type of a file based on its extension."""
#     mime_type, _ = mimetypes.guess_type(file_path)
#     if mime_type is None:
#         raise ValueError(f"Could not determine MIME type for {file_path}")
#     return mime_type


# def main():
#     parser = argparse.ArgumentParser(
#         description="Remix images using Google Generative AI."
#     )
#     parser.add_argument(
#         "-i",
#         "--image",
#         action="append",
#         required=True,
#         help="Paths to input images (1-5 images). Provide multiple -i flags for multiple images.",
#     )
#     parser.add_argument(
#         "--prompt",
#         type=str,
#         help="Optional prompt for remixing the images.",
#     )
#     parser.add_argument(
#         "--output-dir",
#         type=str,
#         default="output",
#         help="Directory to save the remixed images.",
#     )

#     args = parser.parse_args()

#     all_image_paths = args.image

#     num_images = len(all_image_paths)
#     if not (1 <= num_images <= 5):
#         parser.error("Please provide between 1 and 5 input images using the -i flag.")

#     # Determine the prompt
#     final_prompt = args.prompt
#     if final_prompt is None:
#         if num_images == 1:
#             final_prompt = "Turn this image into a professional quality studio shoot with better lighting and depth of field."
#         else:
#             final_prompt = "Combine the subjects of these images in a natural way, producing a new image."

#     # Ensure output directory exists
#     output_dir = '/home/ubuntu/virtual_tryon'
#     os.makedirs(output_dir, exist_ok=True)

#     remix_images(
#         image_paths=all_image_paths,
#         prompt=final_prompt,
#         output_dir=output_dir,
#     )


# if __name__ == "__main__":
#     main()




#-----------------
# Function Form
#-----------------
import os
import time
import mimetypes
from google import genai
from google.genai import types
from dotenv import load_dotenv
from email_trial import send_product_email
MODEL_NAME = "gemini-2.5-flash-image-preview"

# Load environment variables
load_dotenv()


def virtual_tryon(jewellery_image: str, recipient_email :str, recipient_name : str,output_dir: str = "/home/ubuntu/virtual_tryon") -> str:
    """
    Creates a virtual try-on image by combining a model photo with a jewellery image.

    Args:
        model_image (str): Path to the model image.
        jewellery_image (str): Path to the jewellery image.
        prompt (str, optional): User prompt for customization. Defaults to a standard virtual try-on prompt.
        output_dir (str, optional): Directory where the output image will be saved.

    Returns:
        str: Path to the saved virtual try-on image.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not set in .env or environment variables.")

    # Initialize client
    client = genai.Client(api_key=api_key)
    model_image = "/home/ubuntu/user.png"
    # Load both images
    parts = []
    for img in [model_image, jewellery_image]:
        with open(img, "rb") as f:
            image_data = f.read()
        mime_type, _ = mimetypes.guess_type(img)
        parts.append(types.Part(inline_data=types.Blob(data=image_data, mime_type=mime_type)))

    # Add prompt
    # if prompt is None:
    prompt = "Make the jewellery appear naturally worn by the model, with seamless blending, realistic lighting, and natural skin reflection for a lifelike result."
    parts.append(types.Part.from_text(text=prompt))

    config = types.GenerateContentConfig(response_modalities=["IMAGE"])

    # Run generation
    stream = client.models.generate_content_stream(
        model=MODEL_NAME,
        contents=parts,
        config=config,
    )

    # Ensure output dir exists
    os.makedirs(output_dir, exist_ok=True)

    # Save the image
    saved_file = None
    for chunk in stream:
        if not chunk.candidates:
            continue

        candidate = chunk.candidates[0]
        if not candidate.content or not candidate.content.parts:
            continue  # skip empty chunks

        for part in candidate.content.parts:
            if part.inline_data and part.inline_data.data:
                timestamp = int(time.time())
                ext = mimetypes.guess_extension(part.inline_data.mime_type) or ".png"
                saved_file = os.path.join(output_dir, f"virtual_tryon_{timestamp}{ext}")
                with open(saved_file, "wb") as f:
                    f.write(part.inline_data.data)


    if saved_file is None:
        raise RuntimeError("No image was generated from the API.")

    print(f"Virtual try-on image saved at: {saved_file}")

    try:
        send_product_email(recipient_email,jewellery_image,saved_file,recipient_name)
    except Exception as e:
        return {"Error Occured while sending email to the user": {e}}

    

# output_path = virtual_tryon(
#     model_image="/home/ubuntu/kriti.jpg",
#     jewellery_image="/home/ubuntu/chain.jpeg",
#     prompt=None
# )
# print("Generated file:", output_path)


#   "prompt": "You are an AI assistant handling customer service for a E-commerece brand called ** Shop LC **. Greet the customers by their name (use the get_user_details function to get this information), your task is to assist customers with the Status of their Previous Orders (Enquire about it). Assist customers directly with the undelivered orders information by utlising the given functions and enquire about what they are looking for particularly all while maintaining a **friendly and human-like tone** over the phone. Keep the responses simple and conversational as if speaking over the phone .     ###IMPORTANT : while listing the order information to the  customer, Dont' provide numbering instead use the sentence , short and sweet based solution and Do not use any Markdown formatting (like **bold**) when presenting response to the customer.      ### Functions and Their Descriptions: - ** get_user_details ** - Use this method to fetch the user details (name,number ...etc). ** fetch_orders ** - use this method to fetch all the customer orders . Using this method , figure out the orders directly and assist customers ** get_order_information ** (orderno) - use this method to Fetch the  particular order information  using the order number. ** get_products_list ** - use this method to Fetch the list of products.  ### Task :-  while handling the customer requests, you should need to take a chance to present the brand products to customer as suggestions such that that they tend to buy them or kind of brand products marketing. Make it more interactive , simple and handle gracefully. After confirming with that they are intrested in , you will have to utilise the function **virtual_tryon ** (jewellery_image,prompt,recipient_email,recipient_name) - to generate the image of user with the product and send to the user through email , you can utilise the other funtions to get the required parameters (email, name .. from user details and) to pass to this functions"
            