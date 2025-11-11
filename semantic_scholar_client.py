# import yaml
import httpx
import re
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception, RetryError
from loguru import logger

def is_http_429_or_network_error(exception):
    if isinstance(exception, httpx.HTTPStatusError):
        return exception.response.status_code == 429
    if isinstance(exception, httpx.RequestError):
        return True
    return False

class SemanticScholarClient:
    def __init__(self, limit=10,proxy=None):
        self.__proxy = proxy
        self.limit = limit
        self.search_url = f"http://api.semanticscholar.org/graph/v1/paper/search"

    def get_articles(self, query, year="2023-"):
        try:
            return self.__get_articles_with_retry(query, year)
        except RetryError:
            logger.warning("Все попытки исчерпаны. Пропускаем поиск по api.semanticscholar.org.")
            return []
        
    @retry(
        stop=stop_after_attempt(5),                   
        wait=wait_exponential(multiplier=1, min=1, max=10),  
        retry=retry_if_exception(is_http_429_or_network_error),
        before_sleep=lambda retry_state: logger.warning(f"Повтор запроса на api.semanticscholar.org ... Попытка {retry_state.attempt_number}")
    )
    def __get_articles_with_retry(self,query,year):
        params = {"query": query,"fields":"title,year,authors,abstract","year":year, "limit":self.limit}
        try:
            logger.info('Ищем статьи через api.semanticscholar.org...')
            with httpx.Client(proxy=self.__proxy, timeout=30) as client:
                response = client.get(self.search_url, params=params, follow_redirects=True)
                response.raise_for_status()
                results = response.json()
                proccessed_papers = self.__process_papers(results=results,query=query)
                return proccessed_papers
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 403:
                logger.error("Ошибка 403: Доступ запрещён. Попробуйте сменить proxy для поиска по api.semanticscholar.org")
                logger.warning("Пропускаем поиск по данному источнику")
                return []
            else:
                raise
            
        
    def __process_papers(self,results:dict,query:str):
        papers = results.get("data", [])
        proccessed_papers = []
        if not papers:
                logger.warning(f'Статьи по данному запросу: {query}  не были найдены через api.semanticscholar.org')
                return proccessed_papers
        for paper in papers:
            title = paper.get("title")
            openAccessPdf = paper.get("openAccessPdf","")
            link = ""
            if openAccessPdf:
                disclaimer = openAccessPdf.get("disclaimer","")
                all_urls = re.findall(r'https://[^\s,]+', disclaimer)
                valid_urls = [url for url in all_urls if 'email=' not in url]
                if valid_urls:
                    link = valid_urls[0] 
            authors_list = [author.get("name", "") for author in paper.get("authors", [])]
            authors = "; ".join(authors_list) 
            abstract = paper.get("abstract", "")
            proccessed_papers.append({"link":link,"title":title, "authors":authors,"abstract":abstract})
        return proccessed_papers
