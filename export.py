user='hansthen'
password='renkEdus5'

import psycopg2

try:
    conn = psycopg2.connect("dbname='postman' user='hansthen' host='localhost' password='renkEdus5'")
    c = conn.cursor()
    c.execute("""select name, st_length(st_transform(way,3637)) from planet_osm_line""")
    rows = c.fetchall()
    for row in rows:
        print row
except:
    print "I am unable to connect to the database"
