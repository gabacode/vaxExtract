from PyPDF2 import PdfFileReader

def getRanges(file):
    
    result_list = []
    r_pages = []
    
    reader = PdfFileReader(file)
    pages = reader.numPages
    
    for page_number in range(0, pages):
        page = reader.getPage(page_number)
        page_content = page.extractText()
    
        if "ALLEGATO" in page_content:
            result = {"page": page_number}
            result_list.append(result)
        
    r_pages.append(pages)
    
    for i in range(len(result_list)):
        r_pages.append(result_list[i]['page'])
    
    r_pages.sort()

    allegati = {
        "a1" : [r_pages[0], r_pages[1]],
        "a2" : [r_pages[1]+1, r_pages[2]]
    }

    return allegati
