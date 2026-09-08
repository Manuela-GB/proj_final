import requests
from bs4 import BeautifulSoup
import pandas as pd

dict_news = {"news": [], "links": [], "views": [], "comments": []}

url = "https://revistapesquisa.fapesp.br/"

pages = [""]  # página principal

for i in pages:
    response = requests.get(url + i)
    bs = BeautifulSoup(response.text, "lxml")

    # Aqui buscamos todos os links das notícias
    temp = bs.select("h2 a")

    for post in temp:
        dict_news["news"].append(post.text.strip())
        dict_news["links"].append(post.get("href"))

        # O site não possui visualizações e comentários visíveis na listagem
        dict_news["views"].append("N/A")
        dict_news["comments"].append("N/A")

df_news = pd.DataFrame(dict_news, columns=["news", "links", "views", "comments"])

df_news.to_csv("./saved_data.csv", index=False)

df_news.head()
