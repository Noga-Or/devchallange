import csv
import mysql.connector
import os

db = mysql.connector.connect(  # connect to mysql server
    host="localhost",
    user="formulaone",
    password="1234",
)
cursor = db.cursor()
# create the database
cursor.execute("CREATE DATABASE formulaonedb;")
cursor.execute("use formulaonedb;")

# load data from CSV files into database
path = os.getcwd().replace("\\", "/")
files = os.listdir(path + "/csv")
# the files needed for endpoints
files_needed = ['seasons.csv', 'races.csv', 'circuits.csv', 'pit_stops.csv', 'lap_times.csv', 'drivers.csv',
                'driver_standings.csv', 'results.csv']

for file_name in files:
    if file_name not in files_needed:
        continue
    table_title = file_name.split(".")[0]
    with open(path + "/csv/" + file_name) as data_file:
        columns = []
        reader = csv.reader(data_file)
        columns = next(reader)                      # first line of CSV is columns' names
        types = ["" for x in range(len(columns))]
        formats = []
        row = next(reader)
        # get type for each column
        for i in range(len(row)):
            val = row[i].strip("\"")
            if any(c.isalpha() for c in val) or columns[i] == 'status':
                types[i] = 'varchar(255)'
            elif "year" in columns[i]:
                types[i] = 'year'
            elif "Text" in columns[i]:
                types[i] = 'varchar(255)'
            elif '-' in val[1:]:
                types[i] = 'date'
                formats.append("%Y-%m-%d")
            elif val.isdecimal():
                types[i] = 'decimal'
            else:
                types[i] = 'varchar(255)'

        # creates script that creates table in the db for the CSV file
        create_script = f"create table {table_title} ( "
        for i in range(len(columns)):
            create_script += f"`{columns[i]}` {types[i]}"
            if i != len(columns) - 1:
                create_script += ", "
        create_script += " );"

        # run the create script
        cursor.execute(create_script)

        # creates script that loads the data from the file into the table
        load_script = f"load data infile \"{path}/csv/{file_name}\" into table {table_title} " \
                      "fields terminated by ',' " \
                      "OPTIONALLY ENCLOSED BY '\"' " \
                      "lines terminated by '\n' " \
                      "ignore 1 rows "
        for i in range(len(columns)):
            if types[i] == 'time' or types[i] == 'date':
                columns[i] = '@`' + columns[i] + '`'
            else:
                columns[i] = '`' + columns[i] + '`'
        a = '(' + ','.join(columns) + ')'
        load_script += a
        if 'time' in types:
            b = " set "
            j = 0
            for i in range(len(types)):
                if types[i] == 'date':
                    b += f"{columns[i][1:]} = str_to_date({columns[i]}, '{formats[j]}') "
                    j += 1
            load_script += b
        load_script += ';'
        cursor.execute("commit")

        # run the load script
        cursor.execute(load_script)

        cursor.execute("commit")

# defines primary keys for lap_times for better performance on such big file.
cursor.execute("alter table lap_times "
               "add primary key(raceId, driverId, lap);")
