import requests
from bs4 import BeautifulSoup

def scrape_url(url):
    try:
        # Hacer una solicitud a la URL
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()  # Lanzar un error si la solicitud falla

        # Analizar el contenido HTML con BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extraer el texto visible
        texts = soup.find_all(text=True)
        visible_texts = filter(tag_visible, texts)
        return " ".join(t.strip() for t in visible_texts if t.strip())

    except requests.exceptions.RequestException as e:
        return f"Error al acceder a la URL: {e}"

def tag_visible(element):
    # Filtrar etiquetas no visibles como scripts, styles, etc.
    from bs4.element import Comment
    if element.parent.name in ['style', 'script', 'head', 'title', 'meta', '[document]']:
        return False
    if isinstance(element, Comment):
        return False
    return True

# URL de ejemplo

