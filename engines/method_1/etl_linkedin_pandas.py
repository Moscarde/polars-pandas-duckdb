import pandas as pd
import os
import csv
import calendar

import warnings

warnings.simplefilter("ignore")


class EtlLinkedinPandas:
    """
    Classe responsável pelo processamento ETL (Extração, Transformação e Carga) de dados do LinkedIn.
    """

    def __init__(self, raw_directory, clean_directory):
        """
        Inicializa a classe LinkedInETLProcessor com os diretórios de dados brutos e limpos.

        Parâmetros:
        raw_directory (str): Diretório contendo os dados brutos.
        clean_directory (str): Diretório onde os dados limpos serão armazenados.
        """
        self.raw_directory = raw_directory
        self.clean_directory = clean_directory

    def detect_file_category(self, file):
        """
        Detecta a categoria de um arquivo com base em seu nome.

        Parâmetros:
        file (str): Nome do arquivo.

        Retorno:
        str: Categoria do arquivo (competitor, content, followers, visitors) ou 0 se não identificado.
        """
        if "competitor" in file:
            return "competitor"
        elif "content" in file:
            return "content"
        elif "followers" in file:
            return "followers"
        elif "visitors" in file:
            return "visitors"
        return 0

    def get_raw_files(self, raw_directory):
        """
        Detecta e retorna uma lista de arquivos brutos a serem processados.

        Parâmetros:
        raw_directory (str): Diretório contendo os dados brutos.

        Retorno:
        list: Lista de dicionários com informações sobre os arquivos brutos.
        """
        extraction_files = []
        for category in os.listdir(raw_directory):
            category_path = os.path.join(raw_directory, category)

            for year in os.listdir(category_path):
                year_path = os.path.join(category_path, year)

                for month in os.listdir(year_path):
                    month_path = os.path.join(year_path, month)

                    monthly_files = os.listdir(month_path)
                    if not monthly_files:
                        continue

                    for i, file in enumerate(monthly_files):
                        file_path = os.path.join(month_path, file)
                        df_category = self.detect_file_category(file)
                        extraction_files.append(
                            {
                                "category": df_category,
                                "file_path": file_path,
                                "dir": [category, year, month],
                                "extraction_period": f"{year}-{month}-{i+1}",
                            }
                        )
        return extraction_files

    def read_excel_file(self, file):
        """
        Lê um arquivo Excel e retorna seus dados como uma lista de DataFrames.

        Parâmetros:
        file (dict): Dicionário com informações sobre o arquivo, incluindo categoria, caminho e período de extração.

        Retorno:
        list: Lista de dicionários contendo o nome do DataFrame, diretório, período de extração e o DataFrame.
        """
        category_keys = {
            "competitor": [{"sheet_name": "competitor", "sheet_pos": 0, "skiprows": 1}],
            "content": [
                {"sheet_name": "content_metrics", "sheet_pos": 0, "skiprows": 1},
                {"sheet_name": "content_posts", "sheet_pos": 1, "skiprows": 1},
            ],
            "followers": [
                {"sheet_name": "followers_new", "sheet_pos": 0, "skiprows": 0},
                {"sheet_name": "followers_location", "sheet_pos": 1, "skiprows": 0},
                {"sheet_name": "followers_function", "sheet_pos": 2, "skiprows": 0},
                {"sheet_name": "followers_experience", "sheet_pos": 3, "skiprows": 0},
                {"sheet_name": "followers_industry", "sheet_pos": 4, "skiprows": 0},
                {"sheet_name": "followers_company_size", "sheet_pos": 5, "skiprows": 0},
            ],
            "visitors": [
                {"sheet_name": "visitors_metrics", "sheet_pos": 0, "skiprows": 0},
                {"sheet_name": "visitors_location", "sheet_pos": 1, "skiprows": 0},
                {"sheet_name": "visitors_function", "sheet_pos": 2, "skiprows": 0},
                {"sheet_name": "visitors_experience", "sheet_pos": 3, "skiprows": 0},
                {"sheet_name": "visitors_industry", "sheet_pos": 4, "skiprows": 0},
                {"sheet_name": "visitors_company_size", "sheet_pos": 5, "skiprows": 0},
            ],
        }

        sheets_to_read = category_keys[file["category"]]

        dataframes = []
        for sheet in sheets_to_read:

            df = pd.read_excel(
                file["file_path"],
                sheet_name=sheet["sheet_pos"],
                skiprows=sheet["skiprows"],
            )

            dataframes.append(
                {
                    "dataframe_name": sheet["sheet_name"],
                    "dir": file["dir"],
                    "extraction_period": file["extraction_period"],
                    "df": df,
                }
            )

        return dataframes

    def extract_data(self):
        """
        Extrai os dados brutos dos arquivos e retorna uma lista de DataFrames.

        Retorno:
        list: Lista de dicionários contendo os dados extraídos.
        """

        files = self.get_raw_files(self.raw_directory)

        data = [obj for file in files for obj in self.read_excel_file(file)]
        return data

    def translate_cols(self, dataframe):
        """
        Traduza os nomes das colunas de um DataFrame para o inglês.

        Parâmetros:
        dataframe (dict): Dicionário contendo o DataFrame e suas informações.

        Retorno:
        dict: O mesmo dicionário com os nomes das colunas traduzidos.
        """
        translated_columns = {
            "content_metrics": [
                "Date",
                "Impressions (organic)",
                "Impressions (sponsored)",
                "Impressions (total)",
                "Unique impressions (organic)",
                "Clicks (organic)",
                "Clicks (sponsored)",
                "Clicks (total)",
                "Reactions (organic)",
                "Reactions (sponsored)",
                "Reactions (total)",
                "Comments (organic)",
                "Comments (sponsored)",
                "Comments (total)",
                "Shares (organic)",
                "Shares (sponsored)",
                "Shares (total)",
                "Engagement rate (organic)",
                "Engagement rate (sponsored)",
                "Engagement rate (total)",
            ],
            "content_posts": [
                "Post Title",
                "Post Link",
                "Post Type",
                "Campaign Name",
                "Published by",
                "Date",
                "Campaign Start Date",
                "Campaign End Date",
                "Audience",
                "Impressions",
                "Views (excluding off-site video views)",
                "Off-site Views",
                "Clicks",
                "Click-Through Rate (CTR)",
                "Likes",
                "Comments",
                "Shares",
                "Followers",
                "Engagement Rate",
                "Content Type",
            ],
            "followers_new": [
                "Date",
                "Followers Sponsored",
                "Followers Organic",
                "Total Followers",
            ],
            "followers_location": ["Location", "Total Followers"],
            "followers_function": ["Function", "Total Followers"],
            "followers_experience": ["Experience Level", "Total Followers"],
            "followers_industry": ["Industry", "Total Followers"],
            "followers_company_size": ["Company Size", "Total Followers"],
            "visitors_metrics": [
                "Date",
                "Page Views Overview (Desktop)",
                "Page Views Overview (Mobile Devices)",
                "Page Views Overview (Total)",
                "Unique Visitors Overview (Desktop)",
                "Unique Visitors Overview (Mobile Devices)",
                "Unique Visitors Overview (Total)",
                "Page Views Day by Day (Desktop)",
                "Page Views Day by Day (Mobile Devices)",
                "Page Views Day by Day (Total)",
                "Unique Visitors Day by Day (Desktop)",
                "Unique Visitors Day by Day (Mobile Devices)",
                "Unique Visitors Day by Day (Total)",
                "Page Views Jobs (Desktop)",
                "Page Views Jobs (Mobile Devices)",
                "Page Views Jobs (Total)",
                "Unique Visitors Jobs (Desktop)",
                "Unique Visitors Jobs (Mobile Devices)",
                "Unique Visitors Jobs (Total)",
                "Total Page Views (Desktop)",
                "Total Page Views (Mobile Devices)",
                "Total Page Views (Total)",
                "Total Unique Visitors (Desktop)",
                "Total Unique Visitors (Mobile Devices)",
                "Total Unique Visitors (Total)",
            ],
            "visitors_location": ["Location", "Total Views"],
            "visitors_function": ["Function", "Total Views"],
            "visitors_experience": ["Experience Level", "Total Views"],
            "visitors_industry": ["Industry", "Total Views"],
            "visitors_company_size": ["Company Size", "Total Views"],
            "competitor": [
                "Page",
                "Total Followers",
                "New Followers",
                "Total Post Engagements",
                "Total Posts",
            ],
        }

        dataframe["df"].columns = translated_columns.get(dataframe["dataframe_name"])
        return dataframe

    def add_final_date(self, dataframe):
        """
        Adiciona uma data final ao DataFrame com base no período de extração.

        Parâmetros:
        dataframe (dict): Dicionário contendo o DataFrame e suas informações.

        Retorno:
        dict: O mesmo dicionário com a data final adicionada.
        """
        extraction_period = dataframe["extraction_period"]
        year, month, period = extraction_period.split("-")

        month_order_pt = {
            "Jan": 1,
            "Fev": 2,
            "Mar": 3,
            "Abr": 4,
            "Maio": 5,
            "Jun": 6,
            "Jul": 7,
            "Ago": 8,
            "Set": 9,
            "Out": 10,
            "Nov": 11,
            "Dez": 12,
        }
        month = month_order_pt[month]

        if period == "2":
            day = calendar.monthrange(int(year), int(month))[1]
        else:
            day = 15

        final_date = f"{year}-{month}-{day}"

        dataframe["df"]["Extraction Range"] = final_date
        return dataframe

    def convert_column_types(self, dataframe):
        """
        Converte colunas específicas do DataFrame para o tipo de dado adequado.

        Parâmetros:
        dataframe (dict): Dicionário contendo o DataFrame e suas informações.

        Retorno:
        dict: O mesmo dicionário com os tipos de dados das colunas convertidos.
        """
        date_columns = {
            "content_metrics": ["Date"],
            "content_posts": ["Date", "Campaign Start Date", "Campaign End Date"],
            "followers_new": ["Date"],
            "visitors_metrics": ["Date"],
        }

        columns_to_convert = date_columns.get(dataframe["dataframe_name"], [])
        columns_to_convert.append("Extraction Range")

        for column in columns_to_convert:
            dataframe["df"][column] = pd.to_datetime(dataframe["df"][column])

        return dataframe

    def clean_content_metrics_data(self, dataframe):
        """
        Limpa e processa os dados de conteúdo metricas.

        Parâmetros:
        dataframe (dict): Dicionário contendo o DataFrame e suas informações.

        Retorno:
        dict: O mesmo dicionário com os dados de métricas de conteúdo limpos.
        """
        df = dataframe["df"][
            [
                "Date",
                "Impressions (total)",
                "Clicks (total)",
                "Reactions (total)",
                "Comments (total)",
                "Shares (total)",
                "Engagement rate (total)",
                "Extraction Range",
            ]
        ]

        df["Reactions (positive)"] = df["Reactions (total)"][
            df["Reactions (total)"] >= 0
        ]
        df["Comments (positive)"] = df["Comments (total)"][df["Comments (total)"] >= 0]
        df["Shares (positive)"] = df["Shares (total)"][df["Shares (total)"] >= 0]
        df["Clicks (positive)"] = df["Clicks (total)"][df["Clicks (total)"] >= 0]

        df["Reactions (positive)"] = df["Reactions (positive)"].fillna(0)
        df["Comments (positive)"] = df["Comments (positive)"].fillna(0)
        df["Shares (positive)"] = df["Shares (positive)"].fillna(0)
        df["Clicks (positive)"] = df["Clicks (positive)"].fillna(0)

        window = 3

        df["Reactions (moving average)"] = (
            df["Reactions (positive)"].rolling(window=window).mean()
        )
        df["Comments (moving average)"] = (
            df["Comments (positive)"].rolling(window=window).mean()
        )
        df["Shares (moving average)"] = (
            df["Shares (positive)"].rolling(window=window).mean()
        )
        df["Clicks (moving average)"] = (
            df["Clicks (positive)"].rolling(window=window).mean()
        )

        df["Reactions (total)"] = df.apply(
            lambda row: (
                row["Reactions (moving average)"]
                if row["Reactions (total)"] < 0
                else row["Reactions (total)"]
            ),
            axis=1,
        )

        df["Comments (total)"] = df.apply(
            lambda row: (
                row["Comments (moving average)"]
                if row["Comments (total)"] < 0
                else row["Comments (total)"]
            ),
            axis=1,
        )

        df["Shares (total)"] = df.apply(
            lambda row: (
                row["Shares (moving average)"]
                if row["Shares (total)"] < 0
                else row["Shares (total)"]
            ),
            axis=1,
        )

        df["Clicks (total)"] = df.apply(
            lambda row: (
                row["Clicks (moving average)"]
                if row["Clicks (total)"] < 0
                else row["Clicks (total)"]
            ),
            axis=1,
        )

        df["Engagement Rate (total)"] = df.apply(
            lambda row: (
                row["Reactions (total)"]
                + row["Comments (total)"]
                + row["Clicks (total)"]
                + row["Shares (total)"]
            )
            / row["Impressions (total)"],
            axis=1,
        )

        dataframe["df"] = df[
            [
                "Date",
                "Impressions (total)",
                "Clicks (total)",
                "Reactions (total)",
                "Comments (total)",
                "Shares (total)",
                "Engagement Rate (total)",
                "Extraction Range",
            ]
        ]

        return dataframe

    def transform_data(self, data):
        """
        Aplica uma série de transformações aos dados extraídos.

        Parâmetros:
        data (list): Lista de dicionários contendo os dados extraídos.

        Retorno:
        list: Lista de dicionários contendo os dados transformados.
        """
        for dataframe in data:

            dataframe = self.translate_cols(dataframe)
            dataframe = self.add_final_date(dataframe)
            dataframe = self.convert_column_types(dataframe)
            if dataframe["dataframe_name"] == "content_metrics":
                dataframe = self.clean_content_metrics_data(dataframe)

        return data

    def load_to_clean(self, data):
        """
        Carrega os dados transformados no diretório de dados limpos.

        Parâmetros:
        data (list): Lista de dicionários contendo os dados transformados.

        Retorno:
        int: Retorna 1 se a carga for bem-sucedida.
        """
        for dataframe in data:
            dir_export = os.path.join(self.clean_directory, *dataframe["dir"])
            if not os.path.exists(dir_export):
                os.makedirs(dir_export)

            export_filename = (
                dataframe["dataframe_name"]
                + "_"
                + dataframe["extraction_period"].split("-")[-1]
                + ".csv"
            )

            dataframe["df"].to_csv(
                os.path.join(dir_export, export_filename),
                index=False,
                quoting=csv.QUOTE_ALL,
            )

        return 1

    def concatenate_monthly_dataframes(self, data):
        """
        Agrupa e concatena os DataFrames extraídos por mês.

        Parâmetros:
        data (list): Lista de dicionários contendo os dados extraídos.

        Retorno:
        dict: Dicionário com os DataFrames concatenados, categoria e diretório de saída.
        """
        grouped_data_month = {}

        for dataframe in data:
            year_month = "_".join(dataframe["extraction_period"].split("-")[:2])
            tag_month = f"{year_month}_{dataframe['dataframe_name']}"

            if tag_month not in grouped_data_month:
                grouped_data_month[tag_month] = {
                    "category": dataframe["dataframe_name"],
                    "export_dir": os.path.join(self.clean_directory, *dataframe["dir"]),
                    "dfs": [],
                }

            grouped_data_month[tag_month]["dfs"].append(dataframe["df"])

        for tag_month, grouped_data in grouped_data_month.items():
            grouped_data_month[tag_month]["concatenated_df"] = pd.concat(
                grouped_data["dfs"]
            )

        return grouped_data_month

    def export_dataframes(self, data, file_prefix):
        """
        Exporta dataframes concatenados para um arquivo CSV.

        Parâmetros:
        data (dict): Dicionário com os DataFrames concatenados.
        file_prefix (str): Tipo de exportação (e.g., 'month', 'clean').

        Retorno:
        int: Retorna 1 se a exportação for bem-sucedida.
        """
        for key, dataframe in data.items():
            export_dir = dataframe["export_dir"]
            export_filename = f"{file_prefix}_{dataframe['category']}.csv"

            if os.path.exists(export_dir) == False:
                os.makedirs(export_dir)

            full_path = os.path.join(export_dir, export_filename)
            dataframe["concatenated_df"].to_csv(
                full_path, index=False, quoting=csv.QUOTE_ALL
            )
        return 1

    def concatenate_category_dataframes(self, data):
        """
        Concatena todos os arquivos concatenados mensalmente em arquivos únicos por categoria.

        Parâmetros:
        clean_data (dict): Dicionário de listas de arquivos mensais limpos a serem concatenados.

        Retorno:
        int: Retorna 1 se a concatenação for bem-sucedida.
        """
        grouped_data_category = {}

        for key, dataframe in data.items():
            if dataframe["category"] not in grouped_data_category:
                grouped_data_category[dataframe["category"]] = {
                    "category": dataframe["category"],
                    "export_dir": os.path.join(
                        self.clean_directory, "concatenated_dataframes"
                    ),
                    "dfs": [],
                }

            grouped_data_category[dataframe["category"]]["dfs"].append(
                dataframe["concatenated_df"]
            )

        for category, grouped_data in grouped_data_category.items():
            grouped_data_category[category]["concatenated_df"] = pd.concat(
                grouped_data["dfs"]
            )

        return grouped_data_category
    
    ## Metodo 2

    def get_clean_concatenated_data(self, clean_concatenated_path):
        clean_data = []
        for filename in os.listdir(clean_concatenated_path):
            clean_data.append(
                {
                    "filename": filename,
                    "df": pd.read_csv(os.path.join(clean_concatenated_path, filename)),
                }
            )


def main():
    """
    Função principal que executa as operações ETL Linkedin.
    """

    raw_directory = "data/linkedin/raw_2030"
    clean_directory = "data/linkedin/clean/pandas"

    etl = EtlLinkedinPandas(raw_directory, clean_directory)
    data = etl.extract_data()
    data = etl.transform_data(data)
    etl.load_to_clean(data)

    concatenated_monthly_dataframes = etl.concatenate_monthly_dataframes(data)
    etl.export_dataframes(concatenated_monthly_dataframes, file_prefix="month")

    concatenated_category_dataframes = etl.concatenate_category_dataframes(
        concatenated_monthly_dataframes
    )
    etl.export_dataframes(concatenated_category_dataframes, file_prefix="all_extractions")

# def method2():
#     clean_concatenated_path = "data/linkedin/clean/concatenated_dataframes"
#     raw_directory = "data/linkedin/raw_2030"
#     clean_directory = "data/linkedin/clean"

#     etl = EtlLinkedinPandas(raw_directory, clean_directory)

#     clean_data = etl.get_clean_concatenated_data(clean_concatenated_path)

if __name__ == "__main__":
    import shutil
    if os.path.exists("data/linkedin/clean/pandas"):
        shutil.rmtree("data/linkedin/clean/pandas")
    main()
