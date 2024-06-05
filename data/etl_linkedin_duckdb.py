import pandas as pd
import os
import duckdb
import re

import warnings
import logging

# Suprimir avisos específicos da openpyxl
warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")

# Configurar logging
logging.basicConfig(level=logging.ERROR)


class EtlLinkedin:
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
        self.con = duckdb.connect(database=":memory:")

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
                                "dir": month_path,
                                "extraction_period": f"{year}_{month}_{i+1}",
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
        print(f"Lendo {len(files)} arquivos...")

        data = [obj for file in files for obj in self.read_excel_file(file)]
        print(f"Encontrado {len(data)} tabelas...")
        return data

    def convert_pandas_to_duck(self, data):
        tables = []
        for dataframe in data:
            table_dict = self.load_data_from_pandas(dataframe)
            tables.append(table_dict)
            # if dataframe["dataframe_name"] == "content_metrics":
            #     self.process_content_metrics(table_name)
        return tables

    def load_data_from_pandas(self, dataframe):
        table_attributes = {
            "content_metrics": {
                "Date": "DATE",  # inferir data diretamente
                "Impressions (organic)": "INT",
                "Impressions (sponsored)": "INT",
                "Impressions (total)": "INT",
                "Unique impressions (organic)": "INT",
                "Clicks (organic)": "INT",
                "Clicks (sponsored)": "INT",
                "Clicks (total)": "INT",
                "Reactions (organic)": "INT",
                "Reactions (sponsored)": "INT",
                "Reactions (total)": "INT",
                "Comments (organic)": "INT",
                "Comments (sponsored)": "INT",
                "Comments (total)": "INT",
                "Shares (organic)": "INT",
                "Shares (sponsored)": "INT",
                "Shares (total)": "INT",
                "Engagement rate (organic)": "DOUBLE",
                "Engagement rate (sponsored)": "DOUBLE",
                "Engagement rate (total)": "DOUBLE",
            },
            "content_posts": {
                "Post Title": "VARCHAR",
                "Post Link": "VARCHAR",
                "Post Type": "VARCHAR",
                "Campaign Name": "VARCHAR",
                "Published by": "VARCHAR",
                "Date": "DATE",  # inferir data diretamente
                "Campaign Start Date": "DATE",  # inferir data diretamente
                "Campaign End Date": "DATE",  # inferir data diretamente
                "Audience": "VARCHAR",
                "Impressions": "INT",
                "Views (excluding off-site video views)": "INT",
                "Off-site Views": "INT",
                "Clicks": "INT",
                "Click-Through Rate (CTR)": "FLOAT",
                "Likes": "INT",
                "Comments": "INT",
                "Shares": "INT",
                "Followers": "INT",
                "Engagement Rate": "FLOAT",
                "Content Type": "VARCHAR",
            },
            "followers_new": {
                "Date": "DATE",  # inferir data diretamente
                "Followers Sponsored": "INT",
                "Followers Organic": "INT",
                "Total Followers": "INT",
            },
            "followers_location": {"Location": "VARCHAR", "Total Followers": "INT"},
            "followers_function": {"Function": "VARCHAR", "Total Followers": "INT"},
            "followers_experience": {
                "Experience Level": "VARCHAR",
                "Total Followers": "INT",
            },
            "followers_industry": {"Industry": "VARCHAR", "Total Followers": "INT"},
            "followers_company_size": {
                "Company Size": "VARCHAR",
                "Total Followers": "INT",
            },
            "visitors_metrics": {
                "Date": "DATE",  # inferir data diretamente
                "Page Views Overview (Desktop)": "INT",
                "Page Views Overview (Mobile Devices)": "INT",
                "Page Views Overview (Total)": "INT",
                "Unique Visitors Overview (Desktop)": "INT",
                "Unique Visitors Overview (Mobile Devices)": "INT",
                "Unique Visitors Overview (Total)": "INT",
                "Page Views Day by Day (Desktop)": "INT",
                "Page Views Day by Day (Mobile Devices)": "INT",
                "Page Views Day by Day (Total)": "INT",
                "Unique Visitors Day by Day (Desktop)": "INT",
                "Unique Visitors Day by Day (Mobile Devices)": "INT",
                "Unique Visitors Day by Day (Total)": "INT",
                "Page Views Jobs (Desktop)": "INT",
                "Page Views Jobs (Mobile Devices)": "INT",
                "Page Views Jobs (Total)": "INT",
                "Unique Visitors Jobs (Desktop)": "INT",
                "Unique Visitors Jobs (Mobile Devices)": "INT",
                "Unique Visitors Jobs (Total)": "INT",
                "Total Page Views (Desktop)": "INT",
                "Total Page Views (Mobile Devices)": "INT",
                "Total Page Views (Total)": "INT",
                "Total Unique Visitors (Desktop)": "INT",
                "Total Unique Visitors (Mobile Devices)": "INT",
                "Total Unique Visitors (Total)": "INT",
            },
            "visitors_location": {"Location": "VARCHAR", "Total Views": "INT"},
            "visitors_function": {"Function": "VARCHAR", "Total Views": "INT"},
            "visitors_experience": {
                "Experience Level": "VARCHAR",
                "Total Views": "INT",
            },
            "visitors_industry": {"Industry": "VARCHAR", "Total Views": "INT"},
            "visitors_company_size": {"Company Size": "VARCHAR", "Total Views": "INT"},
            "competitor": {
                "Page": "VARCHAR",
                "Total Followers": "INT",
                "New Followers": "INT",
                "Total Post Engagements": "FLOAT",
                "Total Posts": "INT",
            },
        }

        db_table_name = (
            f"{dataframe['dataframe_name']}_{dataframe['extraction_period']}"
        )
        table_attribute = table_attributes.get(dataframe["dataframe_name"])

        translated_columns = table_attribute.keys()
        dataframe["df"].columns = list(translated_columns)

        self.con.register("temp_table", dataframe["df"])

        columns_definition = ", ".join(
            [f'"{col}" {dtype}' for col, dtype in table_attribute.items()]
        )
        create_table_query = f"CREATE TABLE {db_table_name} ({columns_definition});"
        self.con.execute(create_table_query)

        insert_query = f"INSERT INTO {db_table_name} SELECT "
        for col, dtype in table_attribute.items():
            if dtype == "DATE":
                insert_query += f'CASE WHEN "{col}" IS NULL OR "{col}" = \'\' THEN NULL ELSE STRPTIME(CAST("{col}" AS VARCHAR), \'%m/%d/%Y\') END AS "{col}", '
            else:
                insert_query += f'"{col}", '

        insert_query = insert_query.rstrip(", ") + " FROM temp_table;"

        self.con.execute(insert_query)

        table_dict = {
            "dataframe_name": dataframe["dataframe_name"],
            "extraction_period": dataframe["extraction_period"],
            "db_table_name": db_table_name,
            "export_dir": dataframe["dir"].replace("raw", "clean"),
        }

        return table_dict

    def process_content_metrics(self, table):
        # TODO: DOCSTRING
        # Criar uma tabela temporária auxiliar

        self.con.execute(
            f"""
            CREATE TABLE {table}_temp AS
            SELECT *,
                CASE WHEN "Reactions (total)" >= 0 THEN "Reactions (total)" ELSE 0 END AS "Reactions (positive)",
                CASE WHEN "Comments (total)" >= 0 THEN "Comments (total)" ELSE 0 END AS "Comments (positive)",
                CASE WHEN "Shares (total)" >= 0 THEN "Shares (total)" ELSE 0 END AS "Shares (positive)",
                CASE WHEN "Clicks (total)" >= 0 THEN "Clicks (total)" ELSE 0 END AS "Clicks (positive)"
            FROM {table}
        """
        )

        # Adicionar colunas para média móvel na tabela temporária auxiliar
        self.con.execute(
            f"""
            ALTER TABLE {table}_temp
            ADD COLUMN "Reactions (moving average)" DOUBLE"""
        )

        self.con.execute(
            f"""
            ALTER TABLE {table}_temp
            ADD COLUMN "Comments (moving average)" DOUBLE"""
        )
        self.con.execute(
            f"""
            ALTER TABLE {table}_temp
            ADD COLUMN "Shares (moving average)" DOUBLE"""
        )
        self.con.execute(
            f"""
            ALTER TABLE {table}_temp
            ADD COLUMN "Clicks (moving average)" DOUBLE"""
        )

        self.con.execute(
            f"""
            ALTER TABLE {table}_temp
            ADD COLUMN "Reactions (final)" DOUBLE"""
        )
        self.con.execute(
            f"""
            ALTER TABLE {table}_temp
            ADD COLUMN "Comments (final)" DOUBLE"""
        )
        self.con.execute(
            f"""
            ALTER TABLE {table}_temp
            ADD COLUMN "Shares (final)" DOUBLE"""
        )
        self.con.execute(
            f"""
            ALTER TABLE {table}_temp
            ADD COLUMN "Clicks (final)" DOUBLE"""
        )

        # Calculando média móvel na tabela temporária auxiliar
        self.con.execute(
            f"""
            UPDATE {table}_temp
            SET "Reactions (moving average)" = (SELECT AVG("Reactions (positive)") FROM {table}_temp t2 WHERE t2."Date" BETWEEN t1."Date" - 2 AND t1."Date"),
                "Comments (moving average)" = (SELECT AVG("Comments (positive)") FROM {table}_temp t2 WHERE t2."Date" BETWEEN t1."Date" - 2 AND t1."Date"),
                "Shares (moving average)" = (SELECT AVG("Shares (positive)") FROM {table}_temp t2 WHERE t2."Date" BETWEEN t1."Date" - 2 AND t1."Date"),
                "Clicks (moving average)" = (SELECT AVG("Clicks (positive)") FROM {table}_temp t2 WHERE t2."Date" BETWEEN t1."Date" - 2 AND t1."Date")
            FROM {table}_temp t1
        """
        )

        # Colunas finais na tabela temporária auxiliar
        self.con.execute(
            f"""
            UPDATE {table}_temp
            SET "Reactions (final)" = CASE WHEN "Reactions (total)" >= 0 THEN "Reactions (total)" ELSE "Reactions (moving average)" END,
                "Comments (final)" = CASE WHEN "Comments (total)" >= 0 THEN "Comments (total)" ELSE "Comments (moving average)" END,
                "Shares (final)" = CASE WHEN "Shares (total)" >= 0 THEN "Shares (total)" ELSE "Shares (moving average)" END,
                "Clicks (final)" = CASE WHEN "Clicks (total)" >= 0 THEN "Clicks (total)" ELSE "Clicks (moving average)" END
        """
        )

        # Copiar os valores finais da tabela temporária auxiliar para a tabela original
        self.con.execute(
            f"""
            UPDATE {table}
            SET "Reactions (total)" = t."Reactions (final)",
                "Comments (total)" = t."Comments (final)",
                "Shares (total)" = t."Shares (final)",
                "Clicks (total)" = t."Clicks (final)"
            FROM {table}_temp t
            WHERE {table}."Date" = t."Date"
        """
        )

        # Deletar a tabela temporária auxiliar
        self.con.execute(f"DROP TABLE {table}_temp")

        return 1

    def add_final_date(self, table):
        """
        TODO: docstrings
        Adiciona uma data final ao DataFrame com base no período de extração.

        Parâmetros:
        dataframe (dict): Dicionário contendo o DataFrame e suas informações.

        Retorno:
        dict: O mesmo dicionário com a data final adicionada.
        """
        map_months_period = {
            "2023_Jan_1": "2023-01-15",
            "2023_Jan_2": "2023-01-31",
            "2023_Fev_1": "2023-02-15",
            "2023_Fev_2": "2023-02-28",
            "2023_Mar_1": "2023-03-15",
            "2023_Mar_2": "2023-03-31",
            "2023_Abr_1": "2023-04-15",
            "2023_Abr_2": "2023-04-30",
            "2023_Mai_1": "2023-05-15",
            "2023_Mai_2": "2023-05-31",
            "2023_Jun_1": "2023-06-15",
            "2023_Jun_2": "2023-06-30",
            "2023_Jul_1": "2023-07-15",
            "2023_Jul_2": "2023-07-31",
            "2023_Ago_1": "2023-08-15",
            "2023_Ago_2": "2023-08-31",
            "2023_Set_1": "2023-09-15",
            "2023_Set_2": "2023-09-30",
            "2023_Out_1": "2023-10-15",
            "2023_Out_2": "2023-10-31",
            "2023_Nov_1": "2023-11-15",
            "2023_Nov_2": "2023-11-30",
            "2023_Dez_1": "2023-12-15",
            "2023_Dez_2": "2023-12-31",
            "2024_Jan_1": "2024-01-15",
            "2024_Jan_2": "2024-01-31",
            "2024_Fev_1": "2024-02-15",
            "2024_Fev_2": "2024-02-29",
            "2024_Mar_1": "2024-03-15",
            "2024_Mar_2": "2024-03-31",
            "2024_Abr_1": "2024-04-15",
            "2024_Abr_2": "2024-04-30",
            "2024_Mai_1": "2024-05-15",
            "2024_Mai_2": "2024-05-31",
            "2024_Jun_1": "2024-06-15",
            "2024_Jun_2": "2024-06-30",
            "2024_Jul_1": "2024-07-15",
            "2024_Jul_2": "2024-07-31",
            "2024_Ago_1": "2024-08-15",
            "2024_Ago_2": "2024-08-31",
            "2024_Set_1": "2024-09-15",
            "2024_Set_2": "2024-09-30",
            "2024_Out_1": "2024-10-15",
            "2024_Out_2": "2024-10-31",
            "2024_Nov_1": "2024-11-15",
            "2024_Nov_2": "2024-11-30",
            "2024_Dez_1": "2024-12-15",
            "2024_Dez_2": "2024-12-31",
        }

        final_date = map_months_period[table["extraction_period"]]
        self.con.execute(
            f"""
            ALTER TABLE {table["db_table_name"]} ADD COLUMN IF NOT EXISTS "Extraction Range" DATE
        """
        )
        self.con.execute(
            f"""
            UPDATE {table["db_table_name"]} SET "Extraction Range" = '{final_date}'
        """
        )

        return 1

    def transform_data(self, tables):
        """
        TODO: Docstring
        Aplica uma série de transformações aos dados extraídos.

        Parâmetros:
        data (list): Lista de dicionários contendo os dados extraídos.

        Retorno:
        list: Lista de dicionários contendo os dados transformados.
        """
        for table in tables:
            if table["dataframe_name"] == "content_metrics":
                self.process_content_metrics(table["db_table_name"])

            self.add_final_date(table)
        return tables

    def load_to_clean(self, tables):
        """
        TODO: docstrings
        Carrega os dados transformados no diretório de dados limpos.

        Parâmetros:
        data (list): Lista de dicionários contendo os dados transformados.

        Retorno:
        int: Retorna 1 se a carga for bem-sucedida.
        """
        for table in tables:
            if not os.path.exists(table["export_dir"]):
                os.makedirs(table["export_dir"])

            export_filename = table["db_table_name"] + ".csv"
            self.con.execute(
                f"COPY {table['db_table_name']} TO '{table['export_dir']}/{export_filename}' (HEADER, DELIMITER ';')"
            )

        return 1

    def concatenate_monthly_tables(self, tables):
        """
        TODO: DOCSTRINGS
        Detecta e retorna uma lista de arquivos limpos a serem concatenados.

        Parâmetros:
        clean_directory (str): Diretório contendo os dados limpos.

        Retorno:
        dict: Dicionário de listas de arquivos a serem concatenados, organizados por categoria.
        """
        monthly_data = {}

        for table in tables:
            year_month = "_".join(table["extraction_period"].split("_")[:2])
            category_year_month = f"{table['dataframe_name']}_{year_month}"

            if category_year_month not in monthly_data:
                monthly_data[category_year_month] = {
                    "category": table["dataframe_name"],
                    "export_dir": table["export_dir"],
                    "tables": [],
                }

            monthly_data[category_year_month]["tables"].append(table["db_table_name"])

        for category_year_month, grouped_data in monthly_data.items():
            table_name = category_year_month
            table_1 = grouped_data["tables"][0]
            table_2 = grouped_data["tables"][1]

            self.con.execute(
                f"""
                CREATE OR REPLACE TABLE "{table_name}" AS
                SELECT * FROM "{table_1}"
                UNION ALL
                SELECT * FROM "{table_2}"
            """
            )

        return monthly_data

    def export_tables(self, tables, export_type):
        """
        TODO: DOCSTRINGS
        Exporta um DataFrame concatenado para um arquivo CSV.

        Parâmetros:
        df (DataFrame): DataFrame a ser exportado.
        category (str): Categoria do DataFrame.
        output_directory (str): Diretório de saída para o arquivo CSV.
        export_type (str): Tipo de exportação (e.g., 'month', 'clean').

        Retorno:
        int: Retorna 1 se a exportação for bem-sucedida.
        """
        for table_name, table_atributes in tables.items():

            if not os.path.exists(table_atributes["export_dir"]):
                os.makedirs(table_atributes["export_dir"])

            export_filename = f"{export_type}_{table_name}.csv"
            self.con.execute(
                f"COPY {table_name} TO '{table_atributes['export_dir']}/{export_filename}' (HEADER, DELIMITER ';')"
            )
        return 1

    def concatenate_category_tables(self, monthly_data):
        """
        TODO:DOCSTRINGS
        Concatena todos os arquivos concatenados mensalmente em arquivos únicos por categoria.

        Parâmetros:
        clean_data (dict): Dicionário de listas de arquivos mensais limpos a serem concatenados.

        Retorno:
        int: Retorna 1 se a concatenação for bem-sucedida.
        """
        monthly_data_t = {
            "competitor_2023_Ago": {
                "category": "competitor",
                "export_dir": "linkedin/clean\\Concorrentes\\2023\\Ago",
                "tables": ["competitor_2023_Ago_1", "competitor_2023_Ago_2"],
            }
        }

        grouped_data_category = {}

        for category_year_month, grouped_data in monthly_data.items():
            if grouped_data["category"] not in grouped_data_category:
                grouped_data_category[grouped_data["category"]] = {
                    "export_dir": re.sub(
                        r"(clean)[\\/].*",
                        r"\1/concatenated_dataframes",
                        grouped_data["export_dir"],
                    ),
                    "tables": [],
                }

            grouped_data_category[grouped_data["category"]]["tables"].append(
                category_year_month
            )

        for category, grouped_data in grouped_data_category.items():
            table_name = category

            # Construir a consulta SQL dinamicamente
            union_all_query = ""
            for table in grouped_data["tables"]:
                union_all_query += f'SELECT * FROM "{table}" UNION ALL '

            union_all_query = union_all_query.rstrip(" UNION ALL ")

            # Executar a consulta
            self.con.execute(
                f"""
                CREATE OR REPLACE TABLE "{table_name}" AS
                {union_all_query}
                """
            )

        return grouped_data_category


def main():
    raw_directory = "data/linkedin/raw"
    clean_directory = "data/linkedin/clean"

    etl = EtlLinkedin(raw_directory, clean_directory)
    pandas_dataframes = etl.extract_data()
    tables = etl.convert_pandas_to_duck(pandas_dataframes)
    etl.transform_data(tables)
    etl.load_to_clean(tables)

    monthly_tables = etl.concatenate_monthly_tables(tables)
    etl.export_tables(monthly_tables, "month")

    category_tables = etl.concatenate_category_tables(monthly_tables)
    etl.export_tables(category_tables, "all_extractions")


if __name__ == "__main__":
    # temp
    # delete clean_dir
    import shutil

    if os.path.exists("data/linkedin/clean"):
        shutil.rmtree("data/linkedin/clean")
    main()