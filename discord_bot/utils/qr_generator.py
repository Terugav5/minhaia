# discord_bot/utils/qr_generator.py

import qrcode
from io import BytesIO


def generate_qr_code(data: str) -> BytesIO:
    """
    Gera um QR Code a partir dos dados fornecidos e o retorna como um objeto BytesIO.
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    # Salva a imagem em um buffer de bytes na memória
    buffer = BytesIO()
    img.save(buffer, "PNG")
    buffer.seek(0)  # "Rewind" o buffer para o início
    return buffer
