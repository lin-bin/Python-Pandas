import pytesseract
from PIL import Image

image = Image.open("1.jpg")
code = pytesseract.image_to_string(image)
print(code)
