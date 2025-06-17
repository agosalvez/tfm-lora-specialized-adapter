from docling.document_converter import DocumentConverter


from docling.datamodel.base_models import ConversionStatus, PipelineOptions
from docling.datamodel.pipeline_options import PipelineOptions, EasyOcrOptions, TesseractOcrOptions
from docling.document_converter import DocumentConverter

pipeline_options = PipelineOptions()
pipeline_options.do_ocr = True
pipeline_options.ocr_options = TesseractOcrOptions()  # Use Tesseract

doc_converter = DocumentConverter(
    pipeline_options=pipeline_options,
)


source = "documento.pdf"  
converter = DocumentConverter()
result = converter.convert(source)
print(result.document.export_to_markdown())  # output: "## Docling Technical Report[...]"