
from semantic_scholar_client import SemanticScholarClient
from habr_client import HabrClient

from form_csv import form_csv
from config import load_config
from proxy import get_proxy
from loguru import logger

config=load_config()
LIMIT = config.get('LIMIT', {})
PROXY = get_proxy(config=config)

class SearchClient():
    def __init__(self):
        client_kwargs = {}
        if LIMIT is not None:
            client_kwargs['limit'] = LIMIT
        self.semanticScolar = SemanticScholarClient(**client_kwargs,proxy=PROXY)
        self.habr = HabrClient(**client_kwargs)
        
    def get_articles_csv(self,query):
        if not query:
            logger.error('Пустой запрос не валиден для дальнейших действий')
            return
        all_papers = []
        habr_papers =self.habr.get_articles(query)
        semantic_scholar_papers = self.semanticScolar.get_articles(query)
        all_papers.extend(semantic_scholar_papers)
        all_papers.extend(habr_papers)
        if not all_papers:
            logger.warn(f'Ни одной статьи не было найдено по запросу:"{query}". Попробуйте изменить запрос')
            return
        form_csv(all_papers,query)
              

if __name__ == "__main__":
    query = "MLOps"
    web_scraper = SearchClient()
    web_scraper.get_articles_csv(query=query)
