import sys
import json

encoded_data = "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"
image_to_create = "tmp.png"
# image_to_create = str(sys.argv[1])

base64_decoded_content = encoded_data.decode("base64")

with open(image_to_create, "wb") as output_file:
    output_file.write(base64_decoded_content)
