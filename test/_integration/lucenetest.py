## begin license ##
#
# "Meresco Lucene" is a set of components and tools to integrate Lucene (based on PyLucene) into Meresco
#
# Copyright (C) 2013 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2013 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
#
# This file is part of "Meresco Lucene"
#
# "Meresco Lucene" is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# "Meresco Lucene" is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with "Meresco Lucene"; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
## end license ##

from seecr.test import IntegrationTestCase
from seecr.test.utils import getRequest
from meresco.xml.namespaces import xpathFirst
from meresco.components import lxmltostring

class LuceneTest(IntegrationTestCase):

    def testQuery(self):
        self.assertEquals(10, self.numberOfRecords(query='field2=value2'))
        self.assertEquals(2, self.numberOfRecords(query='field1=value1'))
        self.assertEquals(100, self.numberOfRecords(query='*'))

    def doSruQuery(self, query):
        header, body = getRequest(port=self.httpPort, path='/sru', arguments={'version': '1.2', 'operation': 'searchRetrieve', 'query': query})
        return body

    def numberOfRecords(self, query):
        body = self.doSruQuery(query)
        result = xpathFirst(body, '/srw:searchRetrieveResponse/srw:numberOfRecords/text()')
        return None if result is None else int(result)