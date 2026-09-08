import requests
from bs4 import BeautifulSoup
import pandas as pd

# DICIONÁRIO
dict_news = {
    "news": [],
    "links": [],
    "category": [],
    "author": [],
    "date": [],
    "summary": []
}

# PÁGINA DA REVSITA
url = "https://periodicos.upe.br/index.php/revistaescripturas"

response = requests.get(url)
response.raise_for_status()

bs = BeautifulSoup(response.text, "lxml")

# INÍCIO DA TABELA

# 1: LINKS
links = bs.select('a[href*="/article/view/"]')

article_links = []

for link in links:
    href = link.get("href")

    if href and href not in article_links:
        article_links.append(href)

print("Quantidade de artigos encontrados:",
      len(article_links))

# PEGAR CADA ARTIGO
for link in article_links:
    if link.startswith("/"):
        article_url = "https://periodicos.upe.br" + link
    else:
        article_url = link

    # página do artigo
    article_response = requests.get(article_url)
    article_response.raise_for_status()

    article_bs = BeautifulSoup(
        article_response.text,
        "lxml"
    )

    # 3: TÍTULO
    title = article_bs.select_one("h1")

    if title:
        title = title.get_text(" ", strip=True)
    else:
        title = "N/A"

    # 4: AUTORES
    authors = article_bs.select(".authors .name")

    if authors:
        author = ", ".join(
            a.get_text(" ", strip=True)
            for a in authors
        )
    else:
        author = "N/A"

    # 5: RESUMO
    resumo = article_bs.select_one(".resumo")

    if resumo:
        summary = resumo.get_text(" ", strip=True)
    else:
        summary = "N/A"

    # 6: DATA
    date = article_bs.select_one(
        ".item.published .value"
    )
    if date:
        date = date.get_text(" ", strip=True)
    else:
        date = "N/A"

    # 7: CATEGORIA
    category = article_bs.select_one(
        ".item.section .value"
    )

    if category:
        category = category.get_text(" ", strip=True)
    else:
        category = "N/A"

    # DICIONÁRIO (ADD)
    dict_news["news"].append(title)
    dict_news["links"].append(article_url)
    dict_news["category"].append(category)
    dict_news["author"].append(author)
    dict_news["date"].append(date)
    dict_news["summary"].append(summary)


# DATAFRAME
df_news = pd.DataFrame(
    dict_news,
    columns=[
        "news",
        "links",
        "category",
        "author",
        "date",
        "summary"
    ]
)

df_news.to_csv(
    "./saved_data.csv",
    index=False
)

# RESULTADOS
df_news.head()
