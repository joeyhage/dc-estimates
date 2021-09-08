from os import environ
from typing import List


class SQLUtil:

    def __init__(self, db):
        self.db = db
        self.job_result_query = '''
            Tbl_Customers.[CustomerID],
            Tbl_Workorders.[JobID],
            Tbl_Customers.[Customer], 
            Tbl_Customers.[CustomerLastName], 
            Tbl_Customers.[CompanyName], 
            Tbl_Workorders.[ContractDate], 
            Tbl_Workorders.[CreateDate], 
            Tbl_Workorders.[JobAddress],
            Tbl_Job_Types.[JobTypeDescription],
            JobContracts.[TotalAmount],
            Payments.[TotalPayments]
        FROM ((( Tbl_Customers 
        LEFT JOIN Tbl_Workorders 
            ON Tbl_Customers.[CustomerID] = Tbl_Workorders.[CustomerID]) 
        LEFT JOIN Tbl_Job_Types 
            ON Tbl_Workorders.JobType = Tbl_Job_Types.JobType) 
        LEFT JOIN (
            SELECT Tbl_JobContracts.[JobID], SUM(Tbl_JobContracts.[JobContractAmount]) AS TotalAmount
            FROM Tbl_JobContracts
            WHERE Tbl_JobContracts.[JobContractAmount] IS NOT NULL
            GROUP BY Tbl_JobContracts.[JobID]
        ) JobContracts ON Tbl_Workorders.[JobID] = JobContracts.[JobID])
        LEFT JOIN ( 
            SELECT Tbl_Payments.[JobID], SUM(Tbl_Payments.[PaymentAmount]) AS TotalPayments
            FROM Tbl_Payments
            WHERE Tbl_Payments.[PaymentAmount] IS NOT NULL
            GROUP BY Tbl_Payments.[JobID]
        ) Payments ON Tbl_Workorders.[JobID] = Payments.[JobID] 
        '''

    def get_db(self):
        return self.db

    def fetch_recent_estimates(self) -> List[dict]:
        return SQLUtil.rows_to_dict_list(
            self.db.session.execute(f'''
                SELECT TOP 25 
                {self.job_result_query}
                ORDER BY Tbl_Workorders.[ContractDate] DESC
            ''').fetchall()
        )

    def fetch_recently_received_jobs(self) -> List[dict]:
        return SQLUtil.rows_to_dict_list(
            self.db.session.execute(f'''
                SELECT TOP 25 
                {self.job_result_query}
                ORDER BY Tbl_Workorders.[CreateDate] DESC
            ''').fetchall()
        )

    def fetch_active_contracts(self) -> List[dict]:
        return SQLUtil.rows_to_dict_list(
            self.db.session.execute(f'''
                SELECT 
                {self.job_result_query}
                WHERE Tbl_Job_Types.[JobTypeDescription] = 'Contract' 
                    AND Tbl_Workorders.[CloseDate] IS NULL 
                ORDER BY Tbl_Workorders.[CreateDate] ASC
            ''').fetchall()
        )

    def search_by_customer_name(self, name) -> List[dict]:
        return SQLUtil.rows_to_dict_list(
            self.db.session.execute(f'''
                SELECT TOP 25 
                {self.job_result_query}
                WHERE Tbl_Customers.[CustomerLastName] IS NOT NULL 
                AND LCASE(Tbl_Customers.[CustomerLastName]) LIKE :query 
                ORDER BY Tbl_Workorders.[ContractDate] DESC
            ''', {'query': f'{name}%'}).fetchall()
        )

    def search_by_company_name(self, name) -> List[dict]:
        return SQLUtil.rows_to_dict_list(
            self.db.session.execute(f'''
                SELECT TOP 25 
                {self.job_result_query}
                WHERE Tbl_Customers.[CompanyName] IS NOT NULL 
                AND LCASE(Tbl_Customers.[CompanyName]) LIKE :query 
                ORDER BY Tbl_Workorders.[ContractDate] DESC
            ''', {'query': f'%{name}%'}).fetchall()
        )

    def search_by_job_address(self, address) -> List[dict]:
        return SQLUtil.rows_to_dict_list(
            self.db.session.execute(f'''
                SELECT
                {self.job_result_query}
                WHERE Tbl_Workorders.[JobAddress] IS NOT NULL 
                AND LCASE(Tbl_Workorders.[JobAddress]) LIKE :query 
                ORDER BY Tbl_Workorders.[ContractDate] DESC
            ''', {'query': f'%{address}%'}).fetchall()
        )

    def get_customer(self, customer_id) -> dict:
        return dict(
            self.db.session.execute(f'''
                SELECT CustomerID,
                       Customer, 
                       CustomerLastName, 
                       CompanyName, 
                       CustomerFirstName2, 
                       CustomerLastName2,
                       BillingContactFirstName,
                       BillingContactLastName,
                       BillingContactCompanyName,
                       BillingAddress, 
                       BillingCity, 
                       BillingState, 
                       BillingZip, 
                       BillingPhone1Type,
                       BillingPhone1, 
                       BillingExt1, 
                       BillingPhone2Type, 
                       BillingPhone2, 
                       BillingExt2, 
                       BillingPhone3Type, 
                       BillingPhone3, 
                       BillingExt3, 
                       BillingPhone4Type, 
                       BillingFax,
                       BillingExt4, 
                       EmailOne, 
                       EmailTwo 
                FROM Tbl_Customers 
                WHERE CustomerID = :customer_id
            ''', {'customer_id': customer_id}).fetchone()
        )

    def get_jobs_by_customer(self, customer_id) -> List[dict]:
        return SQLUtil.rows_to_dict_list(
            self.db.session.execute(f'''
                SELECT 
                {self.job_result_query}
                WHERE Tbl_Workorders.[CustomerID] = :customer_id
                ORDER BY Tbl_Workorders.[ContractDate] DESC
            ''', {'customer_id': customer_id}).fetchall()
        )

    def get_job_details(self, job_id) -> dict:
        return dict(
            self.db.session.execute(f'''
                SELECT Tbl_Workorders.[JobID],
                       Tbl_Workorders.[CustomerID],
                       Tbl_Job_Types.[JobTypeDescription],
                       Tbl_Workorders.[JobCustomer], 
                       Tbl_Workorders.[JobContact],
                       TRIM(Tbl_Workorders.[JobSecondContact]) AS JobContact2,
                       Tbl_Workorders.[JobAddress],
                       Tbl_Workorders.[JobCity],
                       Tbl_Workorders.[JobSt],
                       Tbl_Workorders.[JobZip],
                       Tbl_Workorders.[JobPhone1Type],
                       Tbl_Workorders.[JobContactPhone1],
                       Tbl_Workorders.[JobPhone2Type],
                       Tbl_Workorders.[JobContactPhone2],
                       Tbl_Workorders.[JobPhone3Type],
                       Tbl_Workorders.[JobContactPhone3],
                       Tbl_Workorders.[JobPhone4Type],
                       Tbl_Workorders.[JobContactPhone4],
                       Tbl_Workorders.[ContractDate],
                       Tbl_Workorders.[CreateDate],
                       Tbl_Workorders.[JobStart],
                       Tbl_Workorders.[CloseDate],
                       JobContracts.[TotalAmount],
                       Payments.[TotalPayments] 
                FROM (( Tbl_Workorders 
                LEFT JOIN Tbl_Job_Types 
                    ON Tbl_Workorders.JobType = Tbl_Job_Types.JobType) 
                LEFT JOIN (
                    SELECT Tbl_JobContracts.[JobID], SUM(Tbl_JobContracts.[JobContractAmount]) AS TotalAmount
                    FROM Tbl_JobContracts
                    WHERE Tbl_JobContracts.[JobContractAmount] IS NOT NULL
                    GROUP BY Tbl_JobContracts.[JobID]
                ) JobContracts ON Tbl_Workorders.[JobID] = JobContracts.[JobID]) 
                LEFT JOIN ( 
                    SELECT Tbl_Payments.[JobID], SUM(Tbl_Payments.[PaymentAmount]) AS TotalPayments
                    FROM Tbl_Payments
                    WHERE Tbl_Payments.[PaymentAmount] IS NOT NULL
                    GROUP BY Tbl_Payments.[JobID]
                ) Payments ON Tbl_Workorders.[JobID] = Payments.[JobID] 
                WHERE Tbl_Workorders.[JobID] = :job_id
            ''', {'job_id': job_id}).fetchone()
        )

    def get_work_items_by_job(self, job_id) -> List[dict]:
        return SQLUtil.rows_to_dict_list(
            self.db.session.execute(f'''
                SELECT WorkDescriptionType, 
                       JobContractDescription, 
                       JobContractAmount 
                FROM Tbl_JobContracts 
                WHERE JobID = :job_id
            ''', {'job_id': job_id}).fetchall()
        )

    def get_payments_by_job(self, job_id) -> List[dict]:
        return SQLUtil.rows_to_dict_list(
            self.db.session.execute(f'''
                SELECT PaymentDate,
                       PaymentAmount,
                       PaymentMethod 
                FROM Tbl_Payments 
                WHERE JobID = :job_id
                ORDER BY PaymentDate ASC
            ''', {'job_id': job_id}).fetchall()
        )

    def get_invoices_by_job(self, job_id) -> List[dict]:
        return SQLUtil.rows_to_dict_list(
            self.db.session.execute(f'''
                SELECT Tbl_Invoice.InvoiceDate, 
                       SUM(Tbl_InvoiceDetail.JobContractAmount) AS InvoiceAmount
                FROM Tbl_Invoice 
                INNER JOIN Tbl_InvoiceDetail 
                    ON Tbl_Invoice.InvoiceNumber = Tbl_InvoiceDetail.InvoiceNumber
                WHERE Tbl_Invoice.JobID = :job_id
                GROUP BY Tbl_Invoice.InvoiceDate, Tbl_Invoice.InvoiceNumber
                ORDER BY Tbl_Invoice.InvoiceDate
            ''', {'job_id': job_id}).fetchall()
        )

    @staticmethod
    def rows_to_dict_list(row_proxy) -> List[dict]:
        return list(map(lambda row: dict(row), row_proxy))


# noinspection PyUnresolvedReferences
def init_db(app) -> SQLUtil:
    from flask_sqlalchemy import SQLAlchemy
    import urllib

    app.config['SQLALCHEMY_DATABASE_URI'] = environ['DATABASE_URI']
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    return SQLUtil(SQLAlchemy(app))
