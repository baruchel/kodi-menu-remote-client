#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sqlite3
import sys
import os
import urllib2
import json

database = ".kodi-menu.db"
jsonrpc="2.0"

home = os.getenv("HOME", "")
database = home + "/" + database

def request(host, port, method, params, id=1, jsonrpc=jsonrpc):
    url = "http://" + host + ":" + str(port) + "/jsonrpc"
    v = {
            "jsonrpc":jsonrpc,
            "id":str(id),
            "method":method,
            "params":params
        }
    data = json.dumps(v)
    headers = {"Content-Type":"application/json",}
    req = urllib2.Request(url, data, headers)
    return json.loads(urllib2.urlopen(req).read())

connect = sqlite3.connect(database)
cursor = connect.cursor()

# Check if the table already exists
result = cursor.execute("""
        SELECT name FROM sqlite_master
          WHERE type="table";
          """)

if len(result.fetchall()) == 0:
    result = cursor.execute("""
        CREATE TABLE files(
          keyword CHAR(8),
          file    CHAR(256),
          label   CHAR(128),
          num     INTEGER,
          type    CHAR(64),
          desc    CHAR(256)
        );
        """)
    result = cursor.execute("""
        CREATE TABLE hosts(
          label   CHAR(128) UNIQUE,
          host    CHAR(128),
          port    INTEGER
        );
        """)
    connect.commit()

def error(errname):
    print (errname)
    sys.exit(1)

if sys.argv[1].lower() == "register":
    if len(sys.argv) != 5:
        error("Syntax error")
    result = cursor.execute("""
        SELECT label FROM hosts
          WHERE label LIKE "%s";
        """ % sys.argv[2].lower())
    # Updating existing host
    if len(result.fetchall()) != 0:
        result = cursor.execute("""
            UPDATE hosts
              SET host = "%s",
                  port = %s
              WHERE label LIKE "%s";
            """ % (sys.argv[3], sys.argv[4], sys.argv[2].lower()))
    # Creating new host
    else:
        result = cursor.execute("""
            INSERT INTO hosts
              (label, host, port)
              VALUES ("%s",
                      "%s",
                      %s);
            """ % (sys.argv[2].lower(), sys.argv[3], sys.argv[4]))
    connect.commit()
    sys.exit(0)

if sys.argv[1].lower() == "hosts":
    result = cursor.execute("""
        SELECT label, host, port
          FROM hosts;
        """)
    n = 0
    for row in result:
        n += 1
        print(row)
    if n == 0:
        print "No registered host yet"
    sys.exit(0)

def stop(host, port, id=1):
    r = request(host, port, "Player.GetActivePlayers", {})
    p = r["result"]
    for k in p:
        r = request(host, port, "Player.Stop",
                {"playerid": k["playerid"], })

def getHost(host):
    result = cursor.execute("""
        SELECT host, port FROM hosts
          WHERE label LIKE "%s";
        """ % host.lower())
    r = result.fetchall()
    if len(r) != 1:
        error('No register host called "%s"' % host.lower())
    return r[0]
def getLabel(f):
    if "title" in f and len(f["title"]) > 0:
        return f["title"]
    if "name" in f and len(f["name"]) > 0:
        return f["name"]
    if "label" in f and len(f["label"]) > 0:
        return f["label"]
    return f["file"]

# Display (again) last request
if sys.argv[1].lower() == "last" or sys.argv[1].lower() == "ls":
    result = cursor.execute("""
        SELECT num, label FROM files
          WHERE keyword = "last"
          ORDER BY num ASC;
        """)
    for r in result:
        print("%2d. %s" % (r[0], r[1]))
    sys.exit(0)

# Display recent items
if sys.argv[1].lower() == "recent":
    result = cursor.execute("""
        SELECT num, label, file, type, desc FROM files
          WHERE keyword = "recent"
          ORDER BY num ASC;
        """)
    l = result.fetchall()
    if len(l) > 0:
        result = cursor.execute("""
            DELETE FROM files WHERE keyword = "last";
            """)
    for r in l:
        print("%2d. %s" % (r[0], r[1]))
        _ = cursor.execute("""
            INSERT INTO files
              (keyword, file, label, num, type, desc)
              VALUES ("last", "%s", "%s", %d, "%s", "%s");
            """ % (r[2], r[1], r[0], r[3], r[4]))
    connect.commit()
    sys.exit(0)

# Stop
if sys.argv[2].lower() == "stop":
    host, port = getHost(sys.argv[1])
    stop(host, port)
    sys.exit(0)

# Mute
if sys.argv[2].lower() == "mute":
    host, port = getHost(sys.argv[1])
    r = request(host, port, "Application.SetMute",
            {"mute": "toggle", })
    sys.exit(0)

# Display or set the volume
if sys.argv[2].lower() == "volume":
    host, port = getHost(sys.argv[1])
    if len(sys.argv) == 3:
        r = request(host, port, "Application.GetProperties",
                {"properties": ["volume"], })
        print("Volume: " + str(r["result"]["volume"]))
    else:
        try:
            v = int(sys.argv[3])
            r = request(host, port, "Application.SetVolume",
                {"volume": v, })
        except:
            error("Syntax error")
    sys.exit(0)

# Play again last item
if sys.argv[2].lower() == "again":
    host, port = getHost(sys.argv[1])
    result = cursor.execute("""
        SELECT file, label from files
          WHERE keyword = "recent" and num = 0;
        """)
    r = result.fetchall()
    if len(r) == 1:
        stop(host, port)
        print("Starting " + r[0][1])
        r = request(host, port, "Player.Open",
                { "item":{"file": r[0][0]} })
    else:
        error("No recent item found in the database")
    sys.exit(0)

# Explore addons
if sys.argv[2].lower() == "addons":
    host, port = getHost(sys.argv[1])
    result = cursor.execute("""
        DELETE FROM files WHERE keyword = "last";
        """)
    # List of audio addons
    r0 = request(host, port, "Addons.GetAddons",
            ["xbmc.addon.audio","unknown","all",["name","enabled", "description"]]
            )["result"]
    # List of video addons
    r1 = request(host, port, "Addons.GetAddons",
            ["xbmc.addon.video","unknown","all",["name","enabled", "description"]]
            )["result"]
    r = []
    if "addons" in r0:
        r += r0["addons"]
    if "addons" in r1:
        r += r1["addons"]
    n = 0
    for p in r:
        if p["enabled"] == True:
            result = cursor.execute("""
                INSERT INTO files
                  (keyword, file, label, num, type, desc)
                  VALUES ("last", "%s", "%s", %d, "%s", "%s");
                """ % (
                  "plugin://" + p["addonid"] + "/",
                  getLabel(p), n, "directory", p["description"]))
            print ("%2d. %s" % (n, getLabel(p)))
        n += 1
    connect.commit()
    sys.exit(0)

# Explore sources
if sys.argv[2].lower() == "sources":
    host, port = getHost(sys.argv[1])
    result = cursor.execute("""
        DELETE FROM files WHERE keyword = "last";
        """)
    r0 = request(host, port, "Files.GetSources",
            ["music"])["result"]
    r1 = request(host, port, "Files.GetSources",
            ["video"])["result"]
    r = []
    if "sources" in r0:
        r += r0["sources"]
    if "sources" in r1:
        r += r1["sources"]
    n = 0
    for p in r:
        result = cursor.execute("""
            INSERT INTO files
              (keyword, file, label, num, type, desc)
              VALUES ("last", "%s", "%s", %d, "%s", "%s");
            """ % (
              p["file"],
              getLabel(p), n, "directory", "[source] " + p["file"]))
        print ("%2d. %s" % (n, getLabel(p)))
        n += 1
    connect.commit()
    sys.exit(0)

# Details concerning an item
if sys.argv[1].lower() == "details" or sys.argv[1].lower() == "info":
    result = cursor.execute("""
        SELECT desc FROM files
          WHERE keyword = "last" AND num = %s;
        """ % sys.argv[2])
    desc = result.fetchall()[0][0]
    if len(desc) > 0:
        print(desc)
    sys.exit(0)

# Explore item (number argument)
if len(sys.argv) == 3:
    try:
        n = int(sys.argv[2])
        host, port = getHost(sys.argv[1])
        result = cursor.execute("""
            SELECT file, label, type, desc FROM files
              WHERE keyword = "last" AND num = %d;
            """ % n)
        f, label, t, d = result.fetchall()[0]
        if t == "directory":
            result = cursor.execute("""
                DELETE FROM files WHERE keyword = "last";
                """)
            r = request(host, port, "Files.GetDirectory",
                    [ f,
                      "files",
                      ["title", "description"],
                      {"method":"label", "order":"ascending"} ])
            r = r["result"]["files"]
            n = 0
            for p in r:
                if "description" not in p:
                    p["description"] = ""
                result = cursor.execute("""
                    INSERT INTO files
                      (keyword, file, label, num, type, desc)
                      VALUES ("last", "%s", "%s", %d, "%s", "%s");
                    """ % (
                      p["file"],
                      getLabel(p), n, p["filetype"], p["description"]))
                print ("%2d. %s" % (n, getLabel(p)))
                n += 1
        else:
            stop(host, port)
            r = request(host, port, "Player.Open",
                    { "item":{"file":f} })
            result = cursor.execute("""
                SELECT num FROM files
                  WHERE keyword = "recent" AND file = "%s";
                """ % f)
            r = result.fetchall()
            if len(r) == 0:
                result = cursor.execute("""
                    UPDATE files SET num = num+1
                      WHERE keyword = "recent";
                    """)
                result = cursor.execute("""
                    DELETE FROM files WHERE keyword = "recent" AND num > 19;
                    """)
                result = cursor.execute("""
                    INSERT INTO files
                      (keyword, file, label, type, num, desc)
                      VALUES ("recent", "%s", "%s", "file", 0, "%s");
                    """ % (f, label, d))
            else:
                r = r[0][0]
                result = cursor.execute("""
                    UPDATE files SET num = num + 1
                      WHERE keyword = "recent" AND num < %d;
                    """ % r)
                result = cursor.execute("""
                    UPDATE files SET num = 0
                      WHERE keyword = "recent" AND file = "%s";
                    """ % f)
        connect.commit()
        sys.exit(0)
    except ValueError:
        pass
