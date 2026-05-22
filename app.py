import os
import io
import base64
from html import escape

from flask import Flask, request, Response, render_template
import qrcode
from qrcode.constants import (
    ERROR_CORRECT_L,
    ERROR_CORRECT_M,
    ERROR_CORRECT_Q,
    ERROR_CORRECT_H,
)


app = Flask(__name__, template_folder=".", static_folder=".")

MAX_TEXT_LENGTH = 500
MAX_SIZE = 1024
MIN_SIZE = 128
MAX_BORDER = 20
MIN_BORDER = 0

ERROR_LEVELS = {
    "L": ERROR_CORRECT_L,
    "M": ERROR_CORRECT_M,
    "Q": ERROR_CORRECT_Q,
    "H": ERROR_CORRECT_H,
}


def to_int(value, default):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def generate_qr_png_data_url(text, size, border, error_level):
    qr = qrcode.QRCode(
        version=None,
        error_correction=ERROR_LEVELS[error_level],
        box_size=10,
        border=border,
    )
    qr.add_data(text)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    img = img.resize((size, size))

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    png_base64 = base64.b64encode(buffer.getvalue()).decode("ascii")

    return f"data:image/png;base64,{png_base64}"


@app.route("/", methods=["GET", "POST"])
def index():
    text = ""
    size = 512
    border = 4
    error_level = "M"
    error = ""
    qr_data_url = ""

    if request.method == "POST":
        text = request.form.get("text", "").strip()
        size = to_int(request.form.get("size"), 512)
        border = to_int(request.form.get("border"), 4)
        error_level = request.form.get("error_level", "M").upper()

        if not text:
            error = "テキストを入力してください。"
        elif len(text) > MAX_TEXT_LENGTH:
            error = f"テキストは最大{MAX_TEXT_LENGTH}文字までです。"
        elif size < MIN_SIZE or size > MAX_SIZE:
            error = f"サイズは{MIN_SIZE}px以上、{MAX_SIZE}px以下で指定してください。"
        elif border < MIN_BORDER or border > MAX_BORDER:
            error = f"余白は{MIN_BORDER}以上、{MAX_BORDER}以下で指定してください。"
        elif error_level not in ERROR_LEVELS:
            error = "誤り訂正レベルは L / M / Q / H から選んでください。"
        else:
            try:
                qr_data_url = generate_qr_png_data_url(text, size, border, error_level)
            except Exception:
                error = "QRコードの生成中にエラーが発生しました。入力内容を確認してください。"

    html = render_template(
        "index.html",
        text=escape(text),
        size=size,
        border=border,
        error_level=error_level,
        error=error,
        qr_data_url=qr_data_url,
        max_text_length=MAX_TEXT_LENGTH,
        max_size=MAX_SIZE,
        min_size=MIN_SIZE,
        max_border=MAX_BORDER,
        min_border=MIN_BORDER,
    )

    return Response(html, content_type="text/html; charset=utf-8")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    debug = os.environ.get("DEBUG", "").lower() in ("1", "true", "yes", "on")
    app.run(host="0.0.0.0", port=port, debug=debug)