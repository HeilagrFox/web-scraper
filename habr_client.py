import httpx
from lxml import html
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type, RetryError
from loguru import logger

class HabrClient:
    def __init__(self, limit=10):
        self.search_url = "https://habr.com/ru/search/"
        self.limit = limit

    def get_articles(self, query):
        try:
            return self.__get_articles_with_retry(query)
        except RetryError:
            logger.warning("Все попытки исчерпаны. Пропускаем поиск по api.semanticscholar.org.")
            return []
        
    @retry(
        stop=stop_after_attempt(5),                   
        wait=wait_exponential(multiplier=1, min=1, max=10),  
         retry=retry_if_exception_type(httpx.RequestError) | 
              retry_if_exception_type(httpx.HTTPStatusError),
        before_sleep=lambda retry_state: print(f"Повтор запроса... Попытка {retry_state.attempt_number}")
    )  
    def __get_articles_with_retry(self, query):
        params = {
            "q": query,
            "target_type": "posts",
            "order": "relevance"
        }
        logger.info('Ищем статьи через habr.com...')
        with httpx.Client(timeout=30) as client:
            response = client.get(self.search_url, params=params)
            results = response.text
            proccessed_papers = self.__process_papers(results=results,query=query)
            return proccessed_papers

    
    def __process_papers(self,results:str,query:str):
        tree = html.fromstring(results)
        articles = tree.xpath('//article[contains(@class, "tm-articles-list__item")]')
        proccessed_papers = []
        if not articles:
            logger.warn(f'Статьи по данному запросу: {query}  не были найдены через habr.com')
            return proccessed_papers
        for _, article in enumerate(articles[:self.limit]):
            title_elem = article.xpath('.//a[contains(@class, "tm-title__link")]')
            title = ""
            link = ""
            if title_elem:
                title = title_elem[0].text_content().strip() 
                link = "https://habr.com" + title_elem[0].get("href")
            author_elem = article.xpath('.//a[contains(@class, "tm-user-info__username")]')
            authors = ""
            if author_elem:
                authors = author_elem[0].text_content().strip()
            lead_elem = article.xpath('.//div[contains(@class, "tm-article-snippet__lead")]')
            abstract = ""
            if lead_elem:
                abstract = lead_elem[0].text_content().strip()
            proccessed_papers.append({"link":link,"title":title, "authors":authors,"abstract":abstract})
        return proccessed_papers
        

    