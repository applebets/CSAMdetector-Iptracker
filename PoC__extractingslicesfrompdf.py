import fitz  # PyMuPDF
import os

def extract_every_4th_image_from_pdf(pdf_path, output_folder):
    doc = fitz.open(pdf_path)
    os.makedirs(output_folder, exist_ok=True)

    global_index = 0
    saved_count = 0

    for page_num in range(len(doc)):
        for img_index, img in enumerate(doc[page_num].get_images(full=True)):
            xref = img[0]
            if (global_index + 1) % 4 == 0:
                try:
                    pix = fitz.Pixmap(doc, xref)
                    if pix.n > 4:  # convert to RGB
                        pix = fitz.Pixmap(fitz.csRGB, pix)

                    img_path = os.path.join(output_folder, f"page{page_num+1}_img{img_index+1}.png")
                    pix.save(img_path)
                    saved_count += 1
                except Exception as e:
                    print(f"⚠️ Error saving image {global_index + 1}: {e}")
            global_index += 1

    print(f"✅ Extracted {saved_count} images (every 4th) from {pdf_path} into {output_folder}")
