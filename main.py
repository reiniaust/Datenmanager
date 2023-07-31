from flask import Flask, render_template, request, jsonify
import pyodbc
import json
import re

app = Flask(__name__)

with open("config.json") as f:
    config = json.load(f)

conn_str = config["connection_string"]
conn = pyodbc.connect(conn_str)
c = conn.cursor()

relations = config["relations"]


def load_data_from_db():
    with open("config.json") as f:
        config = json.load(f)

    conn_str = config["connection_string"]
    conn = pyodbc.connect(conn_str)
    c = conn.cursor()

    views = config["views"]

    for view_name, view in views.items():

        column_names = ""
        comma = " "
        for key, value in view["columns"].items():
            column_names += comma + view["table"] + "." + value + " as " + key
            comma = ", "

        orderBy = " order by "
        try:
            orderBy += view["columns"]["Name"]
        except:
            orderBy += view["columns"]["ID"] + " desc"

        c.execute("select " + column_names + " from " +
                  view["table"] + orderBy)

        rows = c.fetchall()

        columns = [column[0] for column in c.description]

        data = []
        # Daten in JSON konvertieren
        for row in rows:
            obj = {}
            i = 0
            for column in columns:
                obj[column] = row[i]
                i += 1
            data.append(obj)

        view["data"] = data

        try:
            view["relations"] = {}
            for (key, value) in relations[view_name].items():
                view["relations"][key] = views[value]["data"]
        except:
            view["relations"] = {}

    return views


def save_data_to_db(view_name, data):
    with open("config.json") as f:
        config = json.load(f)

    conn_str = config["connection_string"]
    conn = pyodbc.connect(conn_str)
    c = conn.cursor()

    table_name = config["views"][view_name]["table"]
    id_field = config["views"][view_name]["columns"]["ID"]

    for row in data:
        # Überprüfen, ob die Daten geändert wurden
        if row.get("changed", False):
            set_clause = ""
            comma = " "
            for key, value in row.items():
                if key != "ID" and key != "changed":
                    old_value = config["views"][view_name]["data"][row["ID"]-1][key]
                    if old_value != value:
                        set_clause += comma + \
                            config["views"][view_name]["columns"][key] + \
                            " = '" + str(value) + "'"
                        comma = ", "

            update_query = "update " + table_name + " set " + \
                set_clause + " where " + id_field + " = " + str(row["ID"])
            print(update_query)
            c.execute(update_query)

    conn.commit()


views_and_data = load_data_from_db()


@app.route("/start")
def index():
    # views = load_data_from_db()

    for view_name, view in views_and_data.items():
        view["data_found"] = view["data"]
        return render_template("index.html", view_name=view_name, relations=view["relations"], views=views_and_data)
        break


@app.route('/form', methods=['POST'])
def form():
    # views = load_data_from_db()

    current_view_name = request.form['view_name']
    found_in_current_view = False
    search = request.form['search']

    # Suchtext in Wörter aufteilen
    search_words = search.lower().split()

    views_found = {}
    found_view_name = ""
    found_key = ""
    all_search_words = search_words
    for view_name, view in views_and_data.items():
        found_in_view = False
        view["data_found"] = []

        if len(search_words) != 0:
            if re.compile(r"\b" + all_search_words[0]).search(str(view_name).lower()):
                found_view_name = view_name
                search_words = all_search_words[1:]
            for key, value in view["data"][0].items():
                if re.compile(r"\b" + all_search_words[0]).search(str(key).lower()):
                    found_key = key
                    search_words = all_search_words[1:]

        for item in view["data"]:
            found = False
            search_in = ""
            for key, value in item.items():
                if found_view_name == "" and found_key == "" or found_view_name == view_name or found_key == key:
                    search_in += " " + str(value)
                    try:
                        # Suche in Beziehung
                        foreign_view = relations[view_name][key]
                        foreign_data = views_and_data[foreign_view]["data"]
                        for d in foreign_data:
                            if d["ID"] == value:
                                search_in += " " + str(d["Name"])
                                break
                    except KeyError:
                        pass

                if all(re.compile(r"\b" + word).search(str(search_in).lower()) for word in search_words):
                    # Wenn alle Wörter im Wert gefunden werden, füge das Element zur Ergebnisliste hinzu
                    view["data_found"].append(item)
                    found = True
                    found_in_view = True
                    break

            if not found:
                # Wenn das Element oder seine Beziehungstabellen nicht alle Wörter enthalten, überspringen Sie das Element
                continue
        if found_in_view:
            views_found[view_name] = view
            if view_name == current_view_name:
                found_in_current_view = True

    if len(views_found) == 0:
        views_found = views_and_data
        search = ""
    else:
        if found_in_current_view == False:
            for view_name, view in views_found.items():
                current_view_name = view_name
                break

    return render_template("index.html", view_name=current_view_name, relations=view["relations"], views=views_found, search=search)


@app.route('/save_data', methods=['POST'])
def save_data():
    if request.method == 'POST':
        try:
            view_name = request.json['view_name']
            data = request.json['data']
            old_data = views_and_data[view_name]["data"]

            # Überprüfen, ob die Daten geändert wurden, und das Feld "changed" entsprechend markieren
            for row in data:
                if row != None and row.get("ID", None) != None:
                    # row["changed"] = False
                    for key, value in row.items():
                        if key != "ID" and value != None and value != "":
                            for row_old in old_data:
                                if str(row_old["ID"]) == str(row["ID"]):
                                    old_value = row_old[key]
                                    print(old_value)
                                    print(value)
                                    print(str(old_value) != str(value))
                                    if str(old_value) != str(value):
                                        print(value)
                                        row["changed"] = True
                                    break

            save_data_to_db(view_name, data)
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})


if __name__ == "__main__":
    app.run(debug=True)
