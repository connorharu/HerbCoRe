import requests
import json
import pandas as pd
from pandas import json_normalize
import pymysql
import csv

class species_link():
    def __init__(self, api_key):
        self.apikey = api_key 

    def get_metadata(self, name=None, id=None):
        url = "https://specieslink.net/ws/1.0/info"
        params = {"apikey": self.apikey}
        response = requests.get(url, params=params)
        if name:
            params['name'] = name
        if id:
            params['id'] = id
        

        if (response.status_code == 200):
            data = response.json()
            return data
        else:
            print("error while obtaining metadata")
            return None


    def get_participants(self):
        url = "https://specieslink.net/ws/1.0/participants"
        params = {"apikey": self.apikey}
        response = requests.get(url, params=params) 

        if (response.status_code == 200):
            data = response.json()
            return data
        else:
            print("error obtaining participating collections and instituitions")
            return None


    def get_institution_data(self, acronym=None, lang=None, id=None): 
        if acronym:
            url = f"https://specieslink.net/ws/1.0/ins/{acronym}/" 
        elif id:
            url = f"https://specieslink.net/ws/1.0/ins/{id}/"
        else:
            print("you need to provide either an acronym or an id.")
            return None
        
        params = {"apikey": self.apikey} 

        if (lang):
            params["lang"] = lang

        response = requests.get(url, params=params) 
        if (response.status_code == 200):
            data = response.json()
            return data
        else:
            print("error while obtaining instituition data")
            return None


    def get_collection_data(self, acronym=None, lang=None, id=None): 
        if acronym:
            url = f"https://specieslink.net/ws/1.0/col/{acronym}/" 
        elif id:
            url = f"https://specieslink.net/ws/1.0/col/{id}/"
        else:
            print("you need to provide either an acronym or an id.")
            return None
        
        params = {"apikey": self.apikey} 
        if (lang):
            params["lang"] = lang 

        response = requests.get(url, params=params)  
        if (response.status_code == 200):
            data = response.json()
            return data
        else:
            print("error while obtaining the collection")
            return None
    

    def get_dataset_info(self, id=None):
        if id:
            url = f"https://specieslink.net/ws/1.0/dts/{id}/"
        else:
            print("you need to provide an id.")
            return None

        response = requests.get(url, params={"apikey": self.apikey}) 

        if (response.status_code == 200): 
            data = response.json()
            return data
        else:
            print("error while obtaining the dataset")
            return None
  
    def search_records(self, filters):
        url = "https://specieslink.net/ws/1.0/search"
        offset = 0
        limit = 5000 
        params = {"apikey": self.apikey} 

        params.update(filters) 
        
        numberMatched = 0 
        numberReturned = 0 
        data = None 
        
        while True: 
            params.update({"offset": offset, "limit": limit}) 
            response = requests.get(url, params=params)  
            
            if response.status_code == 200:
                response_data = response.json()
                numberReturned = response_data.get('numberReturned', 0) 
                
                if offset == 0: 
                    numberMatched = response_data.get('numberMatched', 0) 
                    data = {'features': []}
                
                
                if 'features' in response_data:
                    data['features'].extend(response_data['features'])
                
                print(f"data ran until now: {len(data['features'])}") 
                print(f"matching number: {numberMatched}") 
                print(f"returned number: {numberReturned}")
                
                if len(data['features']) >= numberMatched:
                    break
                
                offset += limit
            
            else:
                print("error while obtaining the biodiversity records")
                return None
    
        return data
    
    def insert_into_mysql(self, records, db_config, table):
        conn = None
        try:
            conn = pymysql.connect(**db_config) 

            if conn.open:
                print("succesful connection")
            else:
                print("failure while connecting to the database")
                return
            
            cursor = conn.cursor() 

            df = json_normalize(records, 'features', errors='ignore') 

            df = json_normalize(records, 'features', errors='ignore') 
            df = df.where(pd.notna(df), None)  

            for index, row in df.iterrows():
                print(f"interting record {index+1}...")
                properties = row.replace({pd.NA: None}).to_dict()

                barcode = properties.get('properties.barcode', None)
                collectioncode = properties.get('properties.collectioncode', None)
                catalognumber = properties.get('properties.catalognumber', None)
                scientificname = properties.get('properties.scientificname', None)
                kingdom = properties.get('properties.kingdom', None)
                family = properties.get('properties.family', None)
                genus = properties.get('properties.genus', None)
                yearcollected = properties.get('properties.yearcollected', None)
                monthcollected = properties.get('properties.monthcollected', None)
                daycollected = properties.get('properties.daycollected', None)
                country = properties.get('properties.country', None)
                stateprovince = properties.get('properties.stateprovince', None)
                county = properties.get('properties.county', None)
                locality = properties.get('properties.locality', None)
                institutioncode = properties.get('properties.institutioncode', None)
                phylum = properties.get('properties.phylum', None)
                basisofrecord = properties.get('properties.basisofrecord', None)
                verbatimlatitude = properties.get('properties.verbatimlatitude', None)
                verbatimlongitude = properties.get('properties.verbatimlongitude', None)
                identifiedby = properties.get('properties.identifiedby', None)
                collectionid = properties.get('properties.collectionid', 0)
                specificepithet = properties.get('properties.specificepithet', None)
                recordedby = properties.get('properties.recordedby', None)
                decimallongitude = properties.get('properties.decimallongitude', None)
                decimallatitude = properties.get('properties.decimallatitude', None)
                modified = properties.get('properties.modified', None)
                scientificnameauthorship = properties.get('properties.scientificnameauthorship', None)
                recordnumber = properties.get('properties.recordnumber', None)
                occurrenceremarks = properties.get('properties.occurrenceremarks', None)

                insert_query = f"""
                    INSERT INTO {db_config['database']}.{table}
                    (barcode, collectioncode, catalognumber, scientificname, kingdom, family, genus, 
                     yearcollected, monthcollected, daycollected, country, stateprovince, county, 
                     locality, institutioncode, phylum, basisofrecord, verbatimlatitude, verbatimlongitude, identifiedby,
                     collectionid, specificepithet, recordedby, decimallongitude, decimallatitude, 
                     modified, scientificnameauthorship, recordnumber, occurrenceremarks) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                
                data = (
                    barcode, collectioncode, catalognumber, scientificname, kingdom, family, genus,
                    yearcollected, monthcollected, daycollected, country, stateprovince, county,
                    locality, institutioncode, phylum, basisofrecord, verbatimlatitude, verbatimlongitude, identifiedby,
                    collectionid, specificepithet, recordedby, decimallongitude, decimallatitude,
                    modified, scientificnameauthorship, recordnumber, occurrenceremarks
                ) 

                cursor.execute(insert_query, data) 
                print(f"record {index+1} inserted successfully")

            conn.commit() 
            print(f"record insertion complete - total records: {len(df)}")

        except pymysql.MySQLError as erro:
            print(f"error while connecting: {erro}")
        except Exception as e:
                print(f"unexpected error: {e}")

        finally: 
            if conn and conn.open: 
                conn.close()
                print("connection terminated")

    def export_to_csv(self, filters, db_config, table, columns=None, output_csv_path=None):
        conn = None
        try:
            conn = pymysql.connect(**db_config) 

            if conn.open: 
                print("succesful connection")
            else:
                print("failure while connecting to the database")
                return

            cursor = conn.cursor()

            where_clauses = []
            values = []

            for column, value in filters.items(): 
                where_clauses.append(f"{column} = %s") 
                values.append(value)

            if where_clauses:  
                where_clause = " AND ".join(where_clauses) 
            else:
                where_clause = "1=1" 

            if columns:
                query_columns = columns  
            else:
                query_columns = "*"  

            query = f"""
                SELECT 
                    {query_columns}
                FROM {db_config['database']}.{table}
                WHERE {where_clause}
            """

            print(f"generated query: {query}")

            cursor.execute(query, values)
            results = cursor.fetchall() 

            print(f"number of records found: {len(results)}")

            if results:
                with open(output_csv_path, mode='w', newline=None, encoding='utf-8') as csv_file:
                    writer = csv.writer(csv_file)

                    if columns:  
                        writer.writerow([columns])
                    else:
                        column_names = [desc[0] for desc in cursor.description]
                        writer.writerow(column_names)

                    for row in results:
                        writer.writerow(row)

                print(f"expord concluded. csv save as: {output_csv_path}")
            else:
                print("no record found with the provided filters.")

        except pymysql.MySQLError as erro:
            print(f"error while connecting: {erro}")
        except Exception as e:
                print(f"unexpected error: {e}")
        finally:
            if conn and conn.open:
                conn.close()
                print("connection terminated")

    def update_records(self, filters, update_values, db_config, table):
        conn = None
        try:
            conn = pymysql.connect(**db_config)

            if conn.open:
                print("succesful connection")
            else:
                print("failure while connecting with the database")
                return

            cursor = conn.cursor()
            cursor.execute("SET SQL_SAFE_UPDATES = 0;") 

            where_clauses = []  
            set_clauses = [] 
            values = []  

            for column, value in filters.items(): 
                where_clauses.append(f"{column} = %s") 
                values.append(value) 


            for column, value in update_values.items(): 
                set_clauses.append(f"{column} = %s") 
                values.insert(0, value) 

            if where_clauses: 
                where_clause = " AND ".join(where_clauses) 
            else:
                raise ValueError("no filter provided for the update")

            if set_clauses: 
                set_clause = ", ".join(set_clauses) 
            else:
                raise ValueError("no value provided for the update.")

            query = f"""
                UPDATE {db_config['database']}.{table}
                SET {set_clause}
                WHERE {where_clause}
            """
            print("query gerada para UPDATE:", query)
            print("valores para UPDATE:", values)

            cursor.execute(query, values)
            conn.commit() 

            print(f"{cursor.rowcount} updated record(s).")

        except pymysql.MySQLError as erro:
            print(f"error while connecting: {erro}")
        except Exception as e:
                print(f"unexpected error: {e}")
        finally:
            if conn and conn.open:
                conn.close()
                print("connection terminated")