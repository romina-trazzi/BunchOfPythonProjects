import pdfkit
import uuid
import os
from jinja2 import Environment, FileSystemLoader

def generate_pdf_report(symbol, chart_path, stats_table):
    env = Environment(loader=FileSystemLoader("templates"))
    template = env.get_template("report_template.html")

    html = template.render(symbol=symbol, chart_path=chart_path, stats=stats_table)

    output_path = os.path.join("output/reports", f"{uuid.uuid4().hex}.pdf")
    config = pdfkit.configuration(wkhtmltopdf="C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe")  # ← personalizza path
    pdfkit.from_string(html, output_path, configuration=config)

    return output_path