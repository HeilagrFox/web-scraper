import csv
from loguru import logger

def form_csv(papers:dict, query:str)->None:
    csv_file = f"./results/papers_{query}.csv"
    with open(csv_file, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["Link", "Title", "Authors", "Abstract"])
        for paper in papers:
            title = paper.get("title", "")
            link = paper.get("link", "")
            abstract = paper.get("abstract", "")
            authors = paper.get("authors", "")
            writer.writerow([link,title, authors, abstract])
    logger.success('Файл csv с информацией по статьям был успешно создан ')
