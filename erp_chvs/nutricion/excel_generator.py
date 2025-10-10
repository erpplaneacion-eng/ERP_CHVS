import io
from openpyxl import Workbook
from openpyxl.drawing.image import Image as OpenpyxlImage
from PIL import Image as PillowImage
from .models import TablaMenus

def generate_menu_excel(menu_id):
    """
    Generates an Excel file for a given menu, including the program image.
    """
    try:
        menu = TablaMenus.objects.get(pk=menu_id)
        programa = menu.id_contrato
        image_path = programa.imagen.path if programa.imagen else None
    except TablaMenus.DoesNotExist:
        return None

    # Create a workbook and select the active worksheet
    wb = Workbook()
    ws = wb.active
    ws.title = "Análisis Nutricional"

    # Merge cells for the image
    ws.merge_cells('A1:B1')

    # Insert image if it exists
    if image_path:
        try:
            # Use Pillow to open the image and get its dimensions
            pil_img = PillowImage.open(image_path)
            # Resize if necessary (optional)
            # pil_img.thumbnail((width, height))

            # Add image to the worksheet
            img = OpenpyxlImage(pil_img)
            ws.add_image(img, 'A1')
        except FileNotFoundError:
            # Handle case where image file is missing
            ws['A1'] = "Imagen no encontrada"

    # Save the workbook to a BytesIO stream
    stream = io.BytesIO()
    wb.save(stream)
    stream.seek(0)
    return stream
