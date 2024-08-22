from flask import Flask, jsonify, render_template, request, g, redirect
import sqlite3
import requests
import math
import os
app = Flask(__name__)
database = 'datafile.db'


def get_db():
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = sqlite3.connect(database)
    return g.sqlite_db


@app.teardown_appcontext
def close_connection(exception):
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()


@app.route('/')
def home():
    conn = get_db()
    cursor = conn.cursor()
    result = cursor.execute("select * from cash")
    cash_result = result.fetchall()
    # print(cash_result)
    # 計算台幣與美金總額
    taiwanese_dollars = 0
    us_dollars = 0
    for data in cash_result:
        # print(type(data))
        taiwanese_dollars += data[1]
        us_dollars += data[2]
    # 獲取匯率資訊
    r = requests.get('https://tw.rter.info/capi.php')
    currency = r.json()
    total = math.floor(taiwanese_dollars + us_dollars *
                       currency['USDTWD']['Exrate'])
    # print(currency)

    # 取得所有股票資訊
    result2 = cursor.execute("select * from stock")
    stock_result = result2.fetchall()
    # print(stock_result)
    # 取得台股多筆相同股的資料,例如買入了好幾次台積電,事實上只有一筆資料
    unique_stock_list = []
    for item in stock_result:
        if item[1] not in unique_stock_list:
            unique_stock_list.append(item[1])
        # 計算單一股票資訊
    stock_info = []
    for stock in unique_stock_list:
        result = cursor.execute(
            "select * from stock where stock_id =?", (stock, ))
        result = result.fetchall()
        # print(result)

        stock_cost = 0  # 單一股票總花費
        shares = 0  # 單一股票股數
        for d in result:
            shares += d[2]
            stock_cost += d[2] * d[3] + d[4] + d[5]
        # 取得目前股價
        url = "https://www.twse.com.tw/exchangeReport/STOCK_DAY?response=json&stockNo=" + stock
        response = requests.get(url)
        data1 = response.json()
        # print(data)
        price_array = data1['data']
        current_price = float(price_array[len(price_array) - 1][6])
        # 單一股票總市值
        total_value = round(current_price * shares)
        total_stock_value = 0
        total_stock_value += total_value
        # 單一股票平均成本
        average_cost = round(stock_cost / shares, 2)
        # 單一股票報酬率
        rate_of_return = round((total_value - stock_cost)
                               * 100 / stock_cost, 2)
        stock_info.append({'stock_id': stock, 'stock_cost': stock_cost,
                           'total_value': total_value, 'average_cost': average_cost,
                           'shares': shares, 'current_price': current_price, 'rate_of_return': rate_of_return})

    for stock in stock_info:
        stock['value_percentage'] = round(
            stock['total_value'] * 100 / total_stock_value, 2)

    # transcation_id = '2'
    # cursor.execute("""delete from stock where transaction_id=?""",
    #                (transcation_id,))
    # result = cursor.execute("select * from stock")
    # result1 = result.fetchall()
    # print(result1)
    # conn.commit()
    # print(data)
    data = {'total': total, 'td': taiwanese_dollars,
            'ud': us_dollars, 'currency': currency['USDTWD']['Exrate'], 'cash_result': cash_result, "stock_info": stock_info}

    return render_template("index.html", data=data)


@app.route('/cash')
def cash_form():
    return render_template('cash.html')


@app.route('/cash', methods=['POST'])
def submit_cash():
    # 取得金額與日期資料
    taiwanese_dollars = 0
    us_dollars = 0
    if request.values['taiwanese-dollars'] != '':
        taiwanese_dollars = request.values['taiwanese-dollars']
    if request.values['us-dollars'] != '':
        us_dollars = request.values['us-dollars']
    note = request.values['note']
    date = request.values['date']

    # 更新數據庫資料
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""insert into cash (taiwanese_dollars, us_dollars, note, date_info) values (?, ?, ?, ?)""",
                   (taiwanese_dollars, us_dollars, note, date))
    conn.commit()
    # 將使用者導回主頁面
    return redirect("/")


@app.route('/cash-delete', methods=['POST'])
def delete():
    transcation_id = request.values['id']
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""delete from cash where transaction_id=?""",
                   (transcation_id,))
    conn.commit()
    return redirect("/")


@app.route("/stock")
def stock():
    return render_template("stock.html")


@app.route('/stock', methods=["POST"])
def stock_form():
    stock_id = request.values['stock-id']
    stock_num = request.values['stock-num']
    stock_price = request.values['stock-price']
    processing_fee = 0
    tax = 0
    if request.values['processing-fee'] != '':
        processing_fee = request.values['processing-fee']
    if request.values['tax'] != '':
        tax = request.values['tax']
    date = request.values['date']
    print(stock_id, stock_num, stock_price, processing_fee, tax)
    # 更新數據庫資料
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""insert into stock (stock_id, stock_num, stock_price, processing_fee, tax, date_info) values (?, ?, ?, ?, ?, ?)""",
                   (stock_id, stock_num, stock_price, processing_fee, tax, date))
    conn.commit()
    # 將使用者導回主頁面
    return redirect('/')


@app.route('/stock', methods=["POST"])
def submit_stock():

    return render_template("stock.html")


@app.route("/test")
@app.route("/test/<name>")
def test(name=None):
    return render_template("test.html", name2=name)


@app.route("/info", methods=["POST"])
def ruturnSomething():
    # JavaScript Object Notation
    return jsonify({"info": "you have successfully make a request"})


if __name__ == '__main__':
    app.run(debug=True)
