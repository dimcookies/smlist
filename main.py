import random
from flask import Flask
from flask import render_template
from flask import send_from_directory
from flask import request
import flask
import os
import psycopg2
from flask import jsonify


DATABASE_URL = os.environ['DATABASE_URL']

#conn = psycopg2.connect(DATABASE_URL, sslmode='require')
conn = psycopg2.connect(DATABASE_URL)
conn.autocommit = True

app = Flask(__name__)


def get_category(req):
    category = request.args.get('c')
    if not category:
        category = request.cookies.get('c')
    
    if not category:
        raise Exception()

    return category

def get_departments(category):
    cur = conn.cursor()
    cur.execute("select distinct convert_to(department, 'utf-8') from items where category = %(cat)s order by 1;", {'cat': category})
    rows = cur.fetchall()
    rows = map(lambda x: str(x[0]), rows)
    cur.close()
    return rows

@app.route('/')
def main():
    try:
        category = get_category(request)
    except:
        return "Category not found", 500

    pending = 'pending' in request.args

    cur = conn.cursor()
    if pending:
        cur.execute("select id, convert_to(title, 'utf-8'), convert_to(department, 'utf-8'), completed,amount,important from items where completed=false and category = %(cat)s order by 3,2;", {'cat': category})
    else:
        search = ""
        if 's' in request.args:
            cur.execute("select id, convert_to(title, 'utf-8'), convert_to(department, 'utf-8'), completed,amount,important from items where category = %(cat)s and upper(title) like %(search)s order by 2;", {'cat': category, 'search':"%" + request.args.get('s').strip().upper() + "%"})
        else:
            cur.execute("select id, convert_to(title, 'utf-8'), convert_to(department, 'utf-8'), completed,amount,important from items where category = %(cat)s order by 2;", {'cat': category})                        
    rows = cur.fetchall()
    rows = map(lambda x: (x[0],str(x[1]), str(x[2]), x[3], x[4],x[5]), rows)
    cur.close()

    vals = {"items":rows, "pending":pending, "deps": get_departments(category)}
    res = flask.make_response(render_template('main.html', **vals))
    res.set_cookie("c", value=category)        
    return res
                                                    
@app.route('/delete')
def delete_item():
    try:
        category = get_category(request)
    except:
        return "Category not found", 500

    id = request.args.get('id')
    if id:
        cur = conn.cursor()
        cur.execute("delete from items where id=%(id)s and category=%(category)s;", {'id': int(id[1:]), "category":category})
        cur.close()

    return jsonify({"status":"ok"})


@app.route('/complete')
def complete_item():
    try:
        category = get_category(request)
    except:
        return "Category not found", 500

    id = request.args.get('id')
    if id:
        cur = conn.cursor()
        cur.execute("update items set completed = NOT completed, amount=1,important=false where id=%(id)s and category=%(category)s;", {'id': int(id[1:]), "category":category})
        cur.close()        
    
    return jsonify({"status":"ok"})

@app.route('/important')
def important_item():
    try:
        category = get_category(request)
    except:
        return "Category not found", 500

    id = request.args.get('id')
    if id:
        cur = conn.cursor()
        cur.execute("update items set important = NOT important where id=%(id)s and category=%(category)s;", {'id': int(id[1:]), "category":category})
        cur.close()        
    
    return jsonify({"status":"ok"})

@app.route('/increment')
def increment_item():
    try:
        category = get_category(request)
    except:
        return "Category not found", 500

    id = request.args.get('id')
    if id:
        cur = conn.cursor()
        cur.execute("update items set  amount=amount+1 where id=%(id)s and category=%(category)s;", {'id': int(id[1:]), "category":category})
        cur.close()        
    
    return jsonify({"status":"ok"})    

@app.route('/add')
def add_item():
    try:
        category = get_category(request)
    except:
        return "Category not found", 500

    title = request.args.get('t')
    department = request.args.get('d')
    if title:
        cur = conn.cursor()
        cur.execute("insert into items (title, department, completed, category) values (%(title)s, %(department)s, false, %(category)s);", {'title': title, "department":department, "category":category})
        cur.close()        
    
    return jsonify({"status":"ok"})


if __name__ == '__main__':
    app.run(host= '0.0.0.0',debug=False, port=5050)