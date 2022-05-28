# opora-challange

files included:
1. folder CSV       : with all csv files
2. formulaone.py    : creates the database 'formulaonedb' and imports all relevent data from CSV files
3. formulaoneapi.py : runs the API endpoints

dependencies:
1. MySQL including:
  + mysql user: formulaone, password: 1234 with privileges = 
  + in configuration file my.ini \ my.cnf: secure_file_priv = 1 in section [mysqld]
3. FastAPI (installed with pip)
4. uvicorn (installed with pip)

instructions:
1. run formulaone.py 
2. run formulaoneapi.py
3. type 'uvicorn formulaoneapi:app --reload' in cmd from the file's directory
4. go to the url written in the cmd (probably http://127.0.0.1:8000)

endpoints:
1. ranking of drivers in given season at **/driversbyseason/{season}**
2. top 3 drivers of each season at **/alltimeranking**
3. driver profile of driver with given id/reference at **/driver/{driver}**
