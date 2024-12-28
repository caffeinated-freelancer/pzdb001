import qrcode
from PIL import Image, ImageDraw, ImageFont
from qrcode.main import QRCode

from pz.config import PzProjectConfig


class QRCodeService:
    config: PzProjectConfig

    def __init__(self, cfg: PzProjectConfig):
        self.config = cfg

    def create_qrcode(self, student_id: str, text: str, output_file: str):
        settings = self.config.qrcode
        # Data to encode

        # Create QR Code object
        qr = QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=settings.qrcode_box,
            border=settings.qrcode_border,
        )

        # Add data to the QR Code object
        qr.add_data(student_id)
        qr.make(fit=True)

        # Create an image from the QR Code
        qr_image = qr.make_image(fill_color="black", back_color="white").convert("RGB")

        # Add space for text

        # Create a font (You can use default or specify a TTF font)
        try:
            id_font = ImageFont.truetype("arial.ttf", settings.id_size)  # Requires a TTF file
        except IOError:
            id_font = ImageFont.load_default()
        try:
            font = ImageFont.truetype(settings.font_ttf, settings.text_size)
        except IOError:
            raise Exception("Font file not found. Please provide a valid Chinese font.")

        # Calculate text size using getbbox
        text_bbox = font.getbbox(text)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]

        qr_width, qr_height = qr_image.size
        canvas_width = qr_width
        canvas_height = qr_height + text_height + 10  # Add some padding

        canvas = Image.open(settings.template_file)
        canvas_width, canvas_height = canvas.size

        # Create a new image with extra space for text
        # canvas = Image.new("RGB", (canvas_width, canvas_height), "white")
        # canvas.paste(qr_image, box=(0, 0, 100, 100))

        # xx, yy = [int(x) for x in settings.qrcode_coordinate.split(',', 2)]

        xx = (canvas_width - qr_width) // 2
        yy = settings.qrcode_y_axis

        canvas.paste(qr_image, (xx, yy, xx + qr_width, yy + qr_height))
        # canvas.paste(qr_image, (0, 0, qr_width , qr_height ))

        # Draw the text on the canvas
        draw = ImageDraw.Draw(canvas)
        text_x = (canvas_width - text_width) // 2  # Center the text
        text_y = settings.text_y_axis

        draw.text((text_x, text_y), text, fill="black", font=font)
        xx, yy = [int(x) for x in settings.id_coordinate.split(',', 2)]
        draw.text((xx, yy), student_id, fill="black", font=id_font)

        # Save the resulting image
        canvas.save(output_file)
