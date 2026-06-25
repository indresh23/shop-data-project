import pandas as pd
import numpy as np
import sqlite3


class ShopDataPipeline:

    def __init__(self):
        self.sales_file = "sales_data.csv"
        self.products_file = "products.csv"
        self.stores_file = "stores.csv"

    def load_data(self):
        self.sales_df = pd.read_csv(self.sales_file)
        self.products_df = pd.read_csv(self.products_file)
        self.stores_df = pd.read_csv(self.stores_file)

        print("Sales Shape:", self.sales_df.shape)
        print("Products Shape:", self.products_df.shape)
        print("Stores Shape:", self.stores_df.shape)

        print(self.sales_df.head())

    def clean_data(self):
        self.sales_df = self.sales_df.drop_duplicates()

        self.sales_df["quantity"] = self.sales_df["quantity"].fillna(
            self.sales_df["quantity"].median()
        )

        self.sales_df["amount"] = self.sales_df["amount"].fillna(
            self.sales_df["amount"].median()
        )

        self.sales_df["sale_date"] = pd.to_datetime(
            self.sales_df["sale_date"],
            dayfirst=True,
            errors="coerce"
        )

        self.sales_df = self.sales_df.dropna(subset=["sale_date"])
        self.sales_df["amount"] = self.sales_df["amount"].astype(float)

        print("Cleaned Shape:", self.sales_df.shape)

    def transform_data(self):
        merged_df = pd.merge(
            self.sales_df,
            self.products_df,
            on="product_id",
            how="left"
        )

        merged_df = pd.merge(
            merged_df,
            self.stores_df,
            on="store_id",
            how="left"
        )

        merged_df["total_revenue"] = merged_df["amount"]

        self.final_df = merged_df

        print("\nRevenue Statistics")
        print(self.final_df["total_revenue"].describe())

        print("\nRevenue By City")
        print(
            self.final_df.groupby("city")["total_revenue"]
            .sum()
            .sort_values(ascending=False)
        )

    def load_to_database(self):
        conn = sqlite3.connect("shop_data.db")

        self.final_df.to_sql(
            "retail_sales",
            conn,
            if_exists="replace",
            index=False
        )

        conn.close()

        print("\nData Loaded to SQLite")

    def run_sql_queries(self):
        conn = sqlite3.connect("shop_data.db")

        query1 = """
        SELECT product_name,
               SUM(quantity) AS total_qty
        FROM retail_sales
        GROUP BY product_name
        ORDER BY total_qty DESC
        LIMIT 3;
        """

        print("\nTop 3 Products")
        print(pd.read_sql_query(query1, conn))

        query2 = """
        SELECT store_name,
               DATE(sale_date) AS sale_date,
               SUM(total_revenue) AS revenue
        FROM retail_sales
        GROUP BY store_name, DATE(sale_date)
        ORDER BY revenue DESC;
        """

        print("\nRevenue Per Store Per Day")
        print(pd.read_sql_query(query2, conn))

        conn.close()

    def summary_report(self):
        print("\nFINAL REPORT")
        print("Total Transactions:", len(self.final_df))
        print("Total Revenue:", round(self.final_df["total_revenue"].sum(), 2))

        print(
            "Top City:",
            self.final_df.groupby("city")["total_revenue"].sum().idxmax()
        )

        print(
            "Top Product:",
            self.final_df.groupby("product_name")["quantity"].sum().idxmax()
        )


def run_pipeline():
    pipeline = ShopDataPipeline()

    pipeline.load_data()
    pipeline.clean_data()
    pipeline.transform_data()
    pipeline.load_to_database()
    pipeline.run_sql_queries()
    pipeline.summary_report()

    print("\nPipeline Completed Successfully")


if __name__ == "__main__":
    run_pipeline()