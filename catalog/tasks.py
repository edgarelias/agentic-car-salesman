import requests
from celery import shared_task
from openai import OpenAI
from bs4 import BeautifulSoup
from agent_chatbot.settings import OpenAIConfig
from catalog.models import KnowledgeArticle

class KnowledgeArticleProcessor:
    """
    Helper to fetch HTML from URL and clean it via Python lib or LLM.
    """
    def __init__(self):
        self.client = OpenAI(api_key=OpenAIConfig.API_KEY)

    def fetch_html(self, url: str) -> str:
        """Downloads raw HTML from the given URL."""
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        return resp.text

    def clean_html(self, html: str) -> str:
        """
        STEP: Strip HTML tags using BeautifulSoup.
        Returns plain text with tags, scripts, and styles removed.
        """
        soup = BeautifulSoup(html, "html.parser")
        # remove script/style elements
        for tag in soup(["script", "style"]):
            tag.decompose()
        return soup.get_text(separator=" ", strip=True)

    def clean_html_llm(self, html: str) -> str:
        """
        STEP: Use an LLM to further clean or normalize the text extracted from HTML.
        Prompts the model in Spanish to remove any residual noise.
        """
        prompt = [
            {"role": "system", "content": (
                "Eres un asistente que limpia texto de artículos. "
                "Elimina cualquier ruido o caracteres no deseados, dejando solo texto legible en español."
            )},
            {"role": "user", "content": html}
        ]
        response = self.client.chat.completions.create(
            model="gpt-4-turbo",
            messages=prompt,
            temperature=0
        )
        return response.choices[0].message.content.strip()

    def process(self, article_id: str):
        """Fetches, cleans, and updates the KnowledgeArticle text field."""
        article = KnowledgeArticle.objects.filter(id=article_id).first()
        raw_html = self.fetch_html(article.url)
        text = self.clean_html(raw_html)
        article.text = text
        article.save()

@shared_task
def fetch_and_process_article(article_id: str):
    """Celery task: fetch HTML and update the model."""
    processor = KnowledgeArticleProcessor()
    processor.process(article_id)
