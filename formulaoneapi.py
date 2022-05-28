from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import mysql.connector
import datetime

# for rest api endpoints
app = FastAPI()


@app.get("/driversbyseason/{season}", response_class=HTMLResponse)
async def drivers_by_season(season):
    """  first endpoint: returns HTML page with ranking of drivers in given season """
    drivers = get_top_drivers(season)  # returns ranking of all drivers in season

    # build HTML response
    result_list = ""
    for i in range(len(drivers)):
        result_list += f"{i + 1}. {drivers[i][1]} {drivers[i][2]} (id={drivers[i][0]}) <br>"
    result = f"""
            <html>
                <head>
                    <title>Drivers By Season</title>
                </head>
                <body>
                    <h2> {season} </h2>
                    <p>{result_list}</p>
                </body>
            </html>
    """
    return result


@app.get("/alltimeranking", response_class=HTMLResponse)
async def all_time_ranking():
    """ second endpoint: return HTML page with top 3 drivers in each season """
    # get list of seasons
    db = mysql.connector.connect(  # connects to database
        host="localhost",
        user="formulaone",
        password="1234",
        database="formulaonedb"
    )
    cursor = db.cursor()
    cursor.execute("select year from seasons;")  # runs SQL query
    years = cursor.fetchall()  # list of seasons

    # build HTML response
    result = f"""
            <html>
                <head>
                    <title>Drivers By Season</title>
                </head>
                <body>
            """
    for year in years:
        result += f"<h3>{year[0]}:</h3> <p>"
        drivers = get_top_drivers(year[0], 3)  # get top 3 drivers in season = year[0]
        for i in range(len(drivers)):
            result += f"{i + 1}. {drivers[i][1]} {drivers[i][2]} (id={drivers[i][0]}) <br>"
        result += "</p>"
    result += "</body> </html>"
    return result


# third endpoint: returns details of each race of driver with given id/ref, races sorted from newest to oldest
@app.get("/driver/{driver}", response_class=HTMLResponse)
async def driver_profile(driver):
    def driver_id_profile(driver_id: int):
        """ inner function of driver_profile, returns HTML page of driver profile of driver with given id """
        db = mysql.connector.connect(  # connect to database
            host="localhost",
            user="formulaone",
            password="1234",
            database="formulaonedb"
        )
        cursor = db.cursor()

        result = f"""
                    <html>
                        <head>
                            <title> Driver {driver_id}</title>
                        </head>
                        <body>
                    """

        # runs query to get list of driver's races, sorted, alog with position, points and circuit id.
        cursor.execute("select r.raceId, "
                       "r.positionOrder,r.points,t.name as Circuitname "
                       "from results r, races c, circuits t "
                       f"where r.driverId={driver_id} "
                       "and r.raceId=c.raceId "
                       "and c.circuitId=t.circuitId "
                       "order by c.date desc;")
        races = cursor.fetchall()
        for race in races:
            result += f"<h4> Race {race[0]}</h4>"

            # runs query to get number of pit stop of driver in this race, and duration of shortest and longest stops.
            cursor.execute("select count(*), coalesce(max(milliseconds),0) ,"
                           " coalesce(min(milliseconds), 0) from pit_stops "
                           f"where driverId={driver_id} and raceId={race[0]} ;")
            stops = cursor.fetchall()
            longest_stop = [["no data"]]
            shortest_stop = [["no data"]]

            # if there aren't any pit stops, longest and shortest return no data
            if stops[0][0] != 0:  # if there are pit stop
                # gets number of longest pit stop (whose duration matches max)
                cursor.execute("select stop from pit_stops "
                               f"where milliseconds = {stops[0][1]} ;")
                longest_stop = cursor.fetchall()

                # gets number of shortest pit stop (whose duration matches min)
                cursor.execute("select stop from pit_stops "
                               f"where milliseconds = {stops[0][2]};")
                shortest_stop = cursor.fetchall()

            # returns duration (in milliseconds) of average, shortest and longest lap of driver in this race.
            cursor.execute("select avg(milliseconds), min(milliseconds), max(milliseconds) from lap_times "
                           f"where driverId={driver_id} and raceId={race[0]};")
            times = cursor.fetchall()

            if not times[0][1] is None:                 # if there is a shortest lap
                # get duration of shortest lap
                cursor.execute("select time from lap_times "
                               f"where driverId = {driver_id} and raceId = {race[0]} and milliseconds = {times[0][1]};")
                fastest_time = cursor.fetchall()
            else:                                       # if there is no data of laps
                fastest_time = [["no data"]]

            if not times[0][2] is None:                 # if there is a longest lap
                # gets duration of longest lap
                cursor.execute("select time from lap_times "
                               f"where driverId = {driver_id} and raceId = {race[0]} and milliseconds = {times[0][2]};")
                slowest_time = cursor.fetchall()
            else:                                       # if there is no data of laps
                slowest_time = [["no data"]]

            result += f"""
                <p>
                average lap time = {milliseconds_to_minutes(times[0][0])} <br>
                fastest lap time = {fastest_time[0][0]} <br>
                slowest lap time = {slowest_time[0][0]} <br>
                number of pit stops = {stops[0][0]} <br>
                fastest pit stop = {shortest_stop[0][0]} <br>
                slowest pit stop = {longest_stop[0][0]} <br>
                circuit name = {race[3]} <br>
                points = {race[2]} <br>
                position = {race[1]}
            """

        return result + "</p> </body> </html>"

    # if parameter given in url is driverId
    if driver.isnumeric():
        return driver_id_profile(int(driver))

    # if parameter is DriverRef
    else:
        db2 = mysql.connector.connect(          # connect to database
            host="localhost",
            user="formulaone",
            password="1234",
            database="formulaonedb"
        )
        cursor2 = db2.cursor()
        # get driverId of driver with given driverRef
        cursor2.execute(f"select driverId from drivers where "
                        f"driverRef = \"{driver}\";")
        driver = cursor2.fetchall()[0][0]
        return driver_id_profile(driver)


def get_top_drivers(season, n=0):
    """ returns list of n top drivers in given season, if n is not given, returns list of all drivers in season
        ordered by number of wins. for each driver id, forename and surname are returned. """

    # connect to database
    db = mysql.connector.connect(
        host="localhost",
        user="formulaone",
        password="1234",
        database="formulaonedb"
    )
    cursor = db.cursor()
    # gets raceId of last race in each season (where overall wins are in driver_standing)
    cursor.execute("select raceId from races"
                   f" where year={season}"
                   " order by date desc"
                   " limit 1;")
    race_id = cursor.fetchall()[0][0]

    if n == 0:      # return all drivers
        cursor.execute("select s.driverId, d.forename, d.surname from driver_standings s, drivers d"
                       f" where s.raceId = {race_id} and s.driverId = d.driverId"
                       " order by s.wins desc;")
    else:           # return only n drivers
        cursor.execute("select s.driverId, d.forename, d.surname from driver_standings s, drivers d"
                       f" where s.raceId = {race_id} and s.driverId = d.driverId"
                       " order by s.wins desc"
                       f" limit {n};")
    drivers = cursor.fetchall()
    return drivers


def milliseconds_to_minutes(n):
    """ given n milliseconds returns a string representing n in format %M:%S.%f """
    # if n is None:
    #     return "no data"
    # minute = int(n / 60000)
    # seconds = n / 1000 - minute * 60
    # mill = int((seconds * 1000) % 1000)
    # seconds = int(seconds)
    # if seconds < 10:
    #     seconds = "0" + str(seconds)
    #
    # return f"{minute}:{seconds}.{mill}"

    if n is None:
        return 'no data'
    else:
        return datetime.datetime.fromtimestamp(float(n)/1000).strftime("%M:%S.%f")[:-3]

