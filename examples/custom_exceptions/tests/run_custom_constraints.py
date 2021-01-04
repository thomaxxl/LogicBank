from decimal import Decimal
import logging, sys, os
from shutil import copyfile

import sqlalchemy

from logic_bank_utils import util as logic_bank_utils

(did_fix_path, sys_env_info) = \
    logic_bank_utils.add_python_path(project_dir="LogicBank", my_file=__file__)
print("\n" + did_fix_path + "\n\n" + sys_env_info + "\n\n")

from logic_bank.logic_bank import LogicBank
from logic_bank.util import row_prt, prt, ConstraintException
from logic_bank.exec_row_logic.logic_row import LogicRow

import examples.custom_exceptions.db.models as models

def copy_db_from_gold():
    """ copy db/database-gold.db over db/database.db"""
    print("\n" + prt("restoring database-gold\n"))

    basedir = os.path.abspath(os.path.dirname(__file__))
    basedir = os.path.dirname(basedir)

    print("\n********************************\n"
          "  IMPORTANT - create database.db from database-gold.db in " + basedir + "/payment_allocation/db/\n" +
          "            - from -- " + prt("") +
          "\n********************************")

    db_loc = os.path.join(basedir, "db/database.db")
    db_source = os.path.join(basedir, "db/database-gold.db")
    copyfile(src=db_source, dst=db_loc)

def setup_logging():
    logic_logger = logging.getLogger('logic_logger')  # for debugging user logic
    logic_logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(message)s - %(asctime)s - %(name)s - %(levelname)s')
    handler.setFormatter(formatter)
    logic_logger.addHandler(handler)

    do_engine_logging = False
    engine_logger = logging.getLogger('engine_logger')  # for internals
    if do_engine_logging:
        engine_logger.setLevel(logging.DEBUG)
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(message)s - %(asctime)s - %(name)s - %(levelname)s')
        handler.setFormatter(formatter)
        engine_logger.addHandler(handler)

setup_logging()
copy_db_from_gold()

basedir = os.path.abspath(os.path.dirname(__file__))
basedir = os.path.dirname(basedir)

db_loc = os.path.join(basedir, "db/database.db")

conn_string = "sqlite:///" + db_loc
engine = sqlalchemy.create_engine(conn_string, echo=False)  # sqlalchemy sqls...

session_maker = sqlalchemy.orm.sessionmaker()
session_maker.configure(bind=engine)
session = session_maker()

class MyConstraintException(ConstraintException):
    pass

def constraint_handler(message: str):
    raise MyConstraintException("Custom constraint_handler for: " + message)


from examples.custom_exceptions.logic.rules_bank import declare_logic
LogicBank.activate(session=session, activator=declare_logic, constraint_event=constraint_handler)
# consider refusing client updates to derivations
# recompute

pre_cust = session.query(models.Customer).filter(models.Customer.Id == "ALFKI").one()
session.expunge(pre_cust)

"""
    Create Order row
"""

cust_alfki = session.query(models.Customer).filter(models.Customer.Id == "ALFKI").one()

amount_total = 1000

new_order = models.Order(AmountTotal=amount_total)
cust_alfki.OrderList.append(new_order)

did_fail_as_expected = False
session.add(new_order)
try:
    session.commit()
except MyConstraintException as ce:
    print("\nExpected constraint: " + str(ce))
    session.rollback()
    did_fail_as_expected = True
except:
    assert False, "Unexpected Exception Type"

if not did_fail_as_expected:
    assert False, "huge order expected to fail, but succeeded"

print("\nrun_customer_constraints, ran to completion\n\n")
