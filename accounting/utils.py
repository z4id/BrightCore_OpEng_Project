#!/user/bin/env python2.7

from datetime import date, datetime
from dateutil.relativedelta import relativedelta

from accounting import db
from models import Contact, Invoice, Payment, Policy

"""
#######################################################
This is the base code for the engineer project.
#######################################################
"""

class PolicyAccounting(object):
    """
     Each policy has its own instance of accounting.
    """
    def __init__(self, policy_id):
        self.policy = Policy.query.filter_by(id=policy_id).one()

        # if invoices for a policy aren't generated only then create those.
        if not self.policy.invoices:
            self.make_invoices()

    def return_account_balance(self, date_cursor=None):
        """
        This method calculates remaining/due balance till a certain date

        Parameters:
        date_cursor (datetime.date): date threhold to filter invoices and payments

        Return:
        due_now: remaining due balance in account
        """
        if not date_cursor:
            # use current date in case date is not provided
            date_cursor = datetime.now().date()

        invoices = Invoice.query.filter_by(policy_id=self.policy.id)\
                                .filter(Invoice.bill_date <= date_cursor)\
                                .order_by(Invoice.bill_date)\
                                .all()
        due_now = 0
        for invoice in invoices:
            due_now += invoice.amount_due

        payments = Payment.query.filter_by(policy_id=self.policy.id)\
                                .filter(Payment.transaction_date <= date_cursor)\
                                .all()
        # balance should be total invoices - total payments
        for payment in payments:
            due_now -= payment.amount_paid

        return due_now

    def make_payment(self, contact_id=None, date_cursor=None, amount=0):
        """
        This method records a payment transaction

        Parameters:
        contact_id: Id of person recording payment
        date_cursor: date when payment was made
        amount: amount of money provided in transaction

        Return:
        payment: Payment object
        """
        if not date_cursor:
            date_cursor = datetime.now().date()

        if not contact_id:
            try:
                contact_id = self.policy.named_insured
            except:
                print "Insured name of policy_id {0} does not exist in Contacts.".format(self.id) 

        payment = Payment(self.policy.id,
                          contact_id,
                          amount,
                          date_cursor)
        db.session.add(payment)
        db.session.commit()

        return payment

    def evaluate_cancellation_pending_due_to_non_pay(self, date_cursor=None):
        """
         If this function returns true, an invoice
         on a policy has passed the due date without
         being paid in full. However, it has not necessarily
         made it to the cancel_date yet.
        """
        pass

    def evaluate_cancel(self, date_cursor=None):
        """
        This method determines if an invoice is cancelled or not

        Parameter(s):
        date_cursor: date against which invoice cancellation should be checked

        """
        if not date_cursor:
            date_cursor = datetime.now().date()

        invoices = Invoice.query.filter_by(policy_id=self.policy.id)\
                                .filter(Invoice.cancel_date <= date_cursor)\
                                .order_by(Invoice.bill_date)\
                                .all()

        for invoice in invoices:
            if not self.return_account_balance(invoice.cancel_date):
                continue
            else:
                print "POLICY with ID {0} SHOULD HAVE CANCELED".format(self.id)
                break
        else:
            print "POLICY with ID {0} SHOULD NOT CANCEL".format(self.id)


    def make_invoices(self):
        """
        This method generates invoices against a policy and stores to database
        """
        for invoice in self.policy.invoices:
            invoice.delete()

        # types of billing
        billing_schedules = {'Annual': None, 'Two-Pay': 2, 'Semi-Annual': 3, 'Quarterly': 4, 'Monthly': 12}

        invoices = []  # list to store generated invoices
        first_invoice = Invoice(self.policy.id,
                                self.policy.effective_date, #bill_date
                                self.policy.effective_date + relativedelta(months=1), #due
                                self.policy.effective_date + relativedelta(months=1, days=14), #cancel
                                self.policy.annual_premium)
        invoices.append(first_invoice)

        if self.policy.billing_schedule == "Annual":
            # no code here since default first invoice is equivalent to implementation of Annual billing
            pass
        elif self.policy.billing_schedule == "Two-Pay":
            # dividing total amount of first generated invoice with number of possible invoices
            first_invoice.amount_due = first_invoice.amount_due / billing_schedules.get(self.policy.billing_schedule)
            # loop will start from 1 to N-1, as first invoice entry has been added already
            for i in range(1, billing_schedules.get(self.policy.billing_schedule)):
                months_after_eff_date = i*6
                bill_date = self.policy.effective_date + relativedelta(months=months_after_eff_date)
                invoice = Invoice(self.policy.id,
                                  bill_date,
                                  bill_date + relativedelta(months=1),
                                  bill_date + relativedelta(months=1, days=14),
                                  self.policy.annual_premium / billing_schedules.get(self.policy.billing_schedule))
                invoices.append(invoice)
        elif self.policy.billing_schedule == "Quarterly":
            # dividing total amount of first generated invoice with number of possible invoices
            first_invoice.amount_due = first_invoice.amount_due / billing_schedules.get(self.policy.billing_schedule)
            # loop will start from 1 to N-1, as first invoice entry has been added already
            for i in range(1, billing_schedules.get(self.policy.billing_schedule)):
                months_after_eff_date = i*3
                bill_date = self.policy.effective_date + relativedelta(months=months_after_eff_date)
                invoice = Invoice(self.policy.id,
                                  bill_date,
                                  bill_date + relativedelta(months=1),
                                  bill_date + relativedelta(months=1, days=14),
                                  self.policy.annual_premium / billing_schedules.get(self.policy.billing_schedule))
                invoices.append(invoice)
        elif self.policy.billing_schedule == "Monthly":
            # dividing total amount of first generated invoice with number of possible invoices
            first_invoice.amount_due = first_invoice.amount_due / billing_schedules.get(self.policy.billing_schedule)
            # loop will start from 1 to N-1, as first invoice entry has been added already
            for i in range(1, billing_schedules.get(self.policy.billing_schedule)):
                months_after_eff_date = i
                bill_date = self.policy.effective_date + relativedelta(months=months_after_eff_date)
                invoice = Invoice(self.policy.id,
                                  bill_date,
                                  bill_date + relativedelta(months=1),
                                  bill_date + relativedelta(months=1, days=14),
                                  self.policy.annual_premium / billing_schedules.get(self.policy.billing_schedule))
                invoices.append(invoice)
        else:
            print "You have chosen a bad billing schedule."

        for invoice in invoices:
            db.session.add(invoice)
        db.session.commit()


def record_a_payment(policy_id=None, amount=0, date=None):
    """
    This function records a payment transaction in database for shell.

    Parameters:
    policy_id: id of policy for which payment is to be made.
    amount: payment amount
    date: payment date in string format "2019-03-12"
    """  
    if policy_id is None or type(policy_id) != int:
        print "Please provide a valid policy id to record this payment"
        return

    pa = PolicyAccounting(policy_id)

    if date is not None:
        date = datetime.strptime(date, '%Y-%m-%d')

    payment = pa.make_payment(date_cursor=date, amount=amount)
    if payment:  # in case of successful payment
        print "Payment Recorded. Info: payment_id: {0}, policy_id: {1}, contact_id: {2},amount_paid: {3}, date: {4}".format(payment.id,
            payment.policy_id, payment.contact_id, payment.amount_paid, payment.transaction_date)
    else:
        print "Payment of {0} against policy id {1} was not successful.".format(amount, policy_id)


################################
# The functions below are for the db and 
# shouldn't need to be edited.
################################
def build_or_refresh_db():
    db.drop_all()
    db.create_all()
    insert_data()
    print "DB Ready!"

def insert_data():
    #Contacts
    contacts = []
    john_doe_agent = Contact('John Doe', 'Agent')
    contacts.append(john_doe_agent)
    john_doe_insured = Contact('John Doe', 'Named Insured')
    contacts.append(john_doe_insured)
    bob_smith = Contact('Bob Smith', 'Agent')
    contacts.append(bob_smith)
    anna_white = Contact('Anna White', 'Named Insured')
    contacts.append(anna_white)
    joe_lee = Contact('Joe Lee', 'Agent')
    contacts.append(joe_lee)
    ryan_bucket = Contact('Ryan Bucket', 'Named Insured')
    contacts.append(ryan_bucket)

    for contact in contacts:
        db.session.add(contact)
    db.session.commit()

    policies = []
    p1 = Policy('Policy One', date(2015, 1, 1), 365)
    p1.billing_schedule = 'Annual'
    p1.named_insured = john_doe_insured.id
    p1.agent = bob_smith.id
    policies.append(p1)

    p2 = Policy('Policy Two', date(2015, 2, 1), 1600)
    p2.billing_schedule = 'Quarterly'
    p2.named_insured = anna_white.id
    p2.agent = joe_lee.id
    policies.append(p2)

    p3 = Policy('Policy Three', date(2015, 1, 1), 1200)
    p3.billing_schedule = 'Monthly'
    p3.named_insured = ryan_bucket.id
    p3.agent = john_doe_agent.id
    policies.append(p3)

    p4 = Policy('Policy Four', date(2015, 1, 2), 500)
    p4.billing_schedule = 'Two-Pay'
    p4.named_insured = ryan_bucket.id
    p4.agent = john_doe_agent.id
    policies.append(p4)

    for policy in policies:
        db.session.add(policy)
    db.session.commit()

    for policy in policies:
        PolicyAccounting(policy.id)

    payment_for_p2 = Payment(p2.id, anna_white.id, 400, date(2015, 2, 1))
    db.session.add(payment_for_p2)
    db.session.commit()

