import PyPDF2

reader = PyPDF2.PdfReader('domestic_duck.pdf')

all_text = ""
for page in range(len(reader.pages)):
    all_text += reader.pages[0].extract_text()

print(all_text)
