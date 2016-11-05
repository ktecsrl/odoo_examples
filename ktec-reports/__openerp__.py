# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 KTec S.r.l.
#    (<http://www.ktec.it>).
#
#    Copyright (C) 2014 Associazione Odoo Italia
#    (<http://www.openerp-italia.org>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    'name': 'KTec Custom Reports',
    'version': '1.0',
    'category': 'general',
    'description': """
KTec Custom reports
===================

This module add special reports for meet the request of KTec

Reports
-------
    * Custom header and footer
    * Custom report for invoice
    * Custom report for sale order
""",
    'author': 'KTec S.r.l.',
    'website': 'http://www.ktec.it',
    'license': 'AGPL-3',
    "depends": ['account','sale'],
    "data": ['reports/header-footer.xml',
             'reports/invoice-report.xml',
             'reports/saleorder-report.xml',
             'reports/website-quote-report.xml'
            ],
    "qweb": [],
    "demo": [],
    "test": [],
    "active": False,
    'installable': False
}
