import requests
from pdf2image import convert_from_path
import os


class PdfUtils:
    url = "https://80.78.253.10/api/schedule/"
    output_folder = "datas"

    def __init__(self, group_code):
        self.group_code = group_code
        self.save_path = os.path.join(PdfUtils.output_folder, f"{self.group_code}.pdf")


    def downloadPdf(self):
        response = requests.get(PdfUtils.url + self.group_code, verify=False)

        if response.status_code == 200:
            with open(PdfUtils.save_path, 'wb') as f:
                f.write(response.content)
            return True
        else:
            print("Failed to download PDF:", response.status_code)
            return False

    def convertToPng(self):
        images = convert_from_path(PdfUtils.save_path)
        for i, image in enumerate(images):
            image_path = os.path.join(PdfUtils.output_folder, f"{PdfUtils.group_code}_{i+1}.png")
            image.save(image_path, "PNG")

    def createImageFromPdf(self):
        if not os.path.exists(PdfUtils.output_folder):
            os.makedirs(PdfUtils.output_folder)
        if self.downloadPdf():
            self.convertToPng()
            print("PDF успешно сконвертирован в PNG.")
        else:
            print("Не удалось загрузить PDF-файл.")

    def clearDatas(self):
        """TODO"""


PdfUtils = PdfUtils("vb-9822-22")
PdfUtils.createImageFromPdf()