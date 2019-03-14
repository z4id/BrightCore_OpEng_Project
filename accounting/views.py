# You will probably need more methods from flask but this one is a good start.

# Import things from Flask that we need.
from flask import render_template, request
from flask import jsonify

from datetime import datetime

from accounting import app, db
from accounting.utils import *

# Import our models
from models import Contact, Invoice, Policy

# Routing for the server.
@app.route("/")
def index():
    # You will need to serve something up here.
    return render_template('index.html')

@app.route('/search_invoices', methods=["GET"])
def get_invoices():
    # parse GET request params
    policy_id = int(request.args.get('policy_id'))
    date_cursor = request.args.get('date_cursor')

    # convert string to date back
    date_cursor = datetime.strptime(date_cursor, "%Y-%m-%d")

    pa = PolicyAccounting(policy_id)
    due_balance = pa.return_account_balance(date_cursor)
    invoices = Invoice.query.filter_by(policy_id=policy_id)\
                            .filter(Invoice.bill_date <= date_cursor)\
                            .order_by(Invoice.bill_date)\
                            .all()
    # make data in format to send response to viewModel
    inv = []            
    for invoice in invoices:
        inv.append({"id": invoice.id, "bill_date": invoice.bill_date.strftime("%Y-%m-%d"), 
            "due_date": invoice.due_date.strftime("%Y-%m-%d"), 
            "cancel_date": invoice.cancel_date.strftime("%Y-%m-%d"), 
            "amount_due": invoice.amount_due, "deleted": invoice.deleted})
    return jsonify(invoices=inv, due_balance=due_balance, policy_nnumber=pa.policy.policy_number)