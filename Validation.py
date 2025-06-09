# Here i will make all function, which will be used in validation

import random, string , io
from PIL import Image, ImageDraw, ImageFont , ImageFilter

def generate_captcha_code(length = 5):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k = length))


def generate_captcha_image(captcha_code):
    image = Image.new('RGB',(286,35), color = (255, 255, 255))
    font = ImageFont.load_default(20)
    # font = ImageFont.truetype("arial.ttf", 20)
    draw = ImageDraw.Draw(image)
    draw.text((110, 5), captcha_code, font=font, fill=(0, 0, 0))
    buf = io.BytesIO()
    image.save(buf, format='PNG')
    buf.seek(0)
    return buf

    