import requests
from bs4 import BeautifulSoup
import pandas as pd

# ALTERAÇÃO:
# Foi adicionada a função urljoin para transformar
# links relativos encontrados no site em URLs completas.
from urllib.parse import urljoin

# =========================
# CONFIGURAÇÕES
# =========================

BASE_URL = "https://periodicos.upe.br"

URL = "https://periodicos.upe.br/index.php/revistaescripturas"

# ALTERAÇÃO:
# Foi adicionado um User-Agent para que a requisição
# se comporte de forma mais parecida com uma requisição
# feita por um navegador.
headers = {
    "User-Agent": "Mozilla/5.0"
}

# =========================
# DICIONÁRIO
# =========================

dict_news = {
    "news": [],
    "links": [],
    "category": [],
    "author": [],
    "date": [],
    "summary": []
}

# =========================
# ACESSAR A REVISTA
# =========================

response = requests.get(
    URL,
    headers=headers,
    timeout=10
)

response.raise_for_status()

bs = BeautifulSoup(
    response.text,
    "lxml"
)

# =========================
# ENCONTRAR LINKS DOS ARTIGOS
# =========================

links = bs.select(
    'a[href*="/article/view/"]'
)

article_links = []

for link in links:

    href = link.get("href")

    if not href:
        continue

    # ALTERAÇÃO:
    # Antes o link era utilizado diretamente.
    # Agora urljoin transforma links como:
    #
    # /article/view/1354
    #
    # em:
    # https://periodicos.upe.br/index.php/revistaescripturas/article/view/1354
    #
    # Isso deixa os links completos e mais seguros para as requisições.

    article_url = urljoin(
        BASE_URL,
        href
    )

    # ALTERAÇÃO:
    # Remove parâmetros que possam aparecer depois de "?"
    # e remove "/" no final da URL.
    article_url = article_url.split("?")[0]

    article_url = article_url.rstrip("/")

    partes = article_url.split("/")

    # ALTERAÇÃO IMPORTANTE:
    # O seletor encontra tanto o link principal do artigo:
    #
    # /article/view/1354
    #
    # quanto links de recursos relacionados:
    #
    # /article/view/1354/861
    #
    # No código inicial isso fazia o mesmo artigo aparecer
    # mais de uma vez no CSV.
    #
    # Aqui verificamos se "view" é realmente a penúltima
    # parte da URL. Assim aceitamos somente:
    #
    # /article/view/1354
    #
    # e ignoramos:
    #
    # /article/view/1354/861

    if len(partes) >= 2 and partes[-2] == "view":

        # ALTERAÇÃO:
        # Também verificamos se o artigo já foi encontrado.
        # Isso evita URLs duplicadas no resultado final.

        if article_url not in article_links:
            article_links.append(article_url)

print(
    "Quantidade de artigos encontrados:",
    len(article_links)
)

# =========================
# PEGAR CADA ARTIGO
# =========================

for article_url in article_links:

    print(
        "\nColetando:",
        article_url
    )

    try:

        article_response = requests.get(
            article_url,
            headers=headers,
            timeout=10
        )

        article_response.raise_for_status()

        article_bs = BeautifulSoup(
            article_response.text,
            "lxml"
        )

        # =========================
        # TÍTULO
        # =========================

        title = article_bs.select_one("h1")

        if title:

            title = title.get_text(
                " ",
                strip=True
            )

        else:

            title = "N/A"

        # =========================
        # AUTORES
        # =========================

        authors = article_bs.select(
            ".authors .name"
        )

        if authors:

            author = ", ".join(
                a.get_text(
                    " ",
                    strip=True
                )
                for a in authors
            )

        else:

            author = "N/A"

        # =========================
        # RESUMO
        # =========================

        summary = "N/A"

        # ALTERAÇÃO:
        # O seletor utilizado inicialmente para o resumo
        # não correspondia à estrutura atual do site.
        #
        # Agora procuramos diretamente pelo elemento que
        # contém exatamente a palavra "Resumo".

        resumo_title = article_bs.find(
            string=lambda text:
            text and text.strip().lower() == "resumo"
        )

        if resumo_title:

            # ALTERAÇÃO:
            # Depois de encontrar "Resumo", pegamos seu elemento
            # pai para localizar o conteúdo correspondente.

            resumo_parent = resumo_title.parent

            # ALTERAÇÃO:
            # Procuramos o próximo elemento HTML para obter
            # o texto do resumo.

            resumo_element = resumo_parent.find_next()

            if resumo_element:

                summary = resumo_element.get_text(
                    " ",
                    strip=True
                )

        # ALTERAÇÃO:
        # Caso a palavra "Resumo" ainda venha junto com o conteúdo,
        # ela é removida para deixar somente o texto do resumo.

        if summary.startswith("Resumo"):

            summary = summary[
                len("Resumo"):
            ].strip()

        # =========================
        # DATA
        # =========================

        date = "N/A"

        date_element = article_bs.select_one(
            ".item.published .value"
        )

        if date_element:

            date = date_element.get_text(
                " ",
                strip=True
            )

        # =========================
        # CATEGORIA
        # =========================

        category = "N/A"

        # ALTERAÇÃO:
        # O seletor utilizado inicialmente para a categoria
        # não estava encontrando corretamente a seção do artigo.
        #
        # Agora procuramos pelo texto "Seção" diretamente
        # na página.

        section_text = article_bs.find(
            string=lambda text:
            text and text.strip().lower() == "seção"
        )

        if section_text:

            section_parent = section_text.parent

            section_value = section_parent.find_next()

            if section_value:

                category = section_value.get_text(
                    " ",
                    strip=True
                )

        # ALTERAÇÃO:
        # Foi adicionada uma segunda tentativa para encontrar
        # a categoria.
        #
        # Caso "Seção" não seja encontrada, o código procura
        # pelos links que apontam para a edição da revista.

        if category == "N/A":

            section_links = article_bs.select(
                'a[href*="/issue/view/"]'
            )

            if section_links:

                category = section_links[0].get_text(
                    " ",
                    strip=True
                )

        # =========================
        # ADICIONAR AO DICIONÁRIO
        # =========================

        dict_news["news"].append(
            title
        )

        dict_news["links"].append(
            article_url
        )

        dict_news["category"].append(
            category
        )

        dict_news["author"].append(
            author
        )

        dict_news["date"].append(
            date
        )

        dict_news["summary"].append(
            summary
        )

    except requests.RequestException as error:

        print(
            f"Erro ao acessar {article_url}: {error}"
        )

        continue

# =========================
# DATAFRAME
# =========================

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

# =========================
# SALVAR CSV
# =========================

# ALTERAÇÃO:
# Foi utilizado "utf-8-sig" para melhorar a compatibilidade
# do CSV com programas como o Excel, principalmente para
# preservar corretamente caracteres com acentos.

df_news.to_csv(
    "./saved_data.csv",
    index=False,
    encoding="utf-8-sig"
)

# =========================
# RESULTADOS
# =========================

print("\n=========================")
print("DADOS COLETADOS")
print("=========================\n")

print(
    df_news.to_string()
)

print(
    "\nTotal de registros:",
    len(df_news)
)

print(
    "\nArquivo salvo como: saved_data.csv"
)

