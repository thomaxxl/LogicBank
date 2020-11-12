
import os
import sys
from datetime import datetime

cwd = os.getcwd()   # eg, /Users/val/python/pycharm/logic-bank/nw/tests
required_path_python_rules = cwd  # seeking /Users/val/python/pycharm/Logic-Bank
required_path_python_rules = required_path_python_rules.replace("/nw/tests", "")
required_path_python_rules = required_path_python_rules.replace("\\nw\\tests", "")
required_path_python_rules = required_path_python_rules.replace("\\\\", "\\")  # you cannot be serious

sys_path = ""
required_path_present = False
for each_node in sys.path:
    sys_path += each_node + "\n"
    if each_node == required_path_python_rules:
        required_path_present = True

if not required_path_present:
    print("Fixing path (so can run from terminal)")
    sys.path.append(required_path_python_rules)
    sys_path += required_path_python_rules + "\n"
else:
    pass
    print("NOT Fixing path (default PyCharm, set in VSC Launch Config)")

run_environment_info = "Run Environment info...\n\n"
run_environment_info += " Current Working Directory: " + cwd + "\n\n"
run_environment_info += "sys.path: (Python imports)\n" + sys_path + "\n"
run_environment_info += "From: " + sys.argv[0] + "\n\n"
run_environment_info += "Using Python: " + sys.version + "\n\n"
run_environment_info += "At: " + str(datetime.now()) + "\n\n"

print("\n" + run_environment_info + "\n\n")

from nw.tests import setup_db  # careful - this must follow fix-path, above
setup_db()

import sqlalchemy_utils

import nw.db.models as models
from logic_bank.exec_row_logic.logic_row import LogicRow
from logic_bank.util import row_prt, prt
from nw.logic import session  # opens db, activates logic listener <--

cls = sqlalchemy_utils.functions.get_class_by_table(models.Base, "Product", data=None)

# Add Order - works
pre_cust = session.query(models.Customer).filter(models.Customer.Id == "ALFKI").one()
session.expunge(pre_cust)


"""
    Test 1 - create allocation row
"""

cust_alfki = session.query(models.Customer).filter(models.Customer.Id == "ALFKI").one()

new_payment = models.Payment(Amount=100)
cust_alfki.PaymentList.append(new_payment)

session.add(new_payment)
session.commit()

post_cust = session.query(models.Customer).filter(models.Customer.Id == "ALFKI").one()

print("\nadd_payment, update completed\n\n")
row_prt(new_payment, "\nnew Payment Result")  #
if new_payment.Amount != 56:
    print ("==> ERROR - unexpected AmountTotal: " + str(new_payment.Amount) +
           "... expected 56")

logic_row = LogicRow(row=post_cust, old_row=pre_cust, ins_upd_dlt="*", nest_level=0, a_session=session, row_sets=None)
if post_cust.Balance == pre_cust.Balance + 56:
    logic_row.log("Correct adjusted Customer Result")
    assert True
else:
    logic_row.log("ERROR - incorrect adjusted Customer Result")
    print("\n--> probable cause: Order customer update not written")
    assert False
print("\nadd_payment, ran to completion\n\n")
