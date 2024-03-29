import time

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
            with open(self.save_path, 'wb') as f:
                f.write(response.content)
            return True
        else:
            print("Failed to download PDF:", response.status_code)
            return False

    def convertToPng(self):
        images = convert_from_path(self.save_path)
        for i, image in enumerate(images):
            image_path = os.path.join(PdfUtils.output_folder, f"{self.group_code}_{i+1}.png")
            image.save(image_path, "PNG")

    def createImageFromPdf(self):
        if not os.path.exists(PdfUtils.output_folder):
            os.makedirs(PdfUtils.output_folder)
        if self.downloadPdf():

            self.convertToPng()

    def clearDatas(self):
        for filename in os.listdir(PdfUtils.output_folder):
            if filename.startswith(self.group_code):
                file_path = os.path.join(PdfUtils.output_folder, filename)
                try:
                    os.remove(file_path)
                except OSError as e:
                    raise OSError(f"Ошибка при удалении файла '{filename}': {e.strerror}")

