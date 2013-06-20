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

from meresco.core import Observable

from meresco.components.statistics import Logger
from meresco.components.clausecollector import ClauseCollector
from meresco.lucene.lucenequerycomposer import LuceneQueryComposer


class CqlToLuceneQuery(Observable, Logger):
    def __init__(self, unqualifiedFields, name=None):
        Observable.__init__(self, name=name)
        self._cqlComposer = LuceneQueryComposer(unqualifiedFields)

    def executeQuery(self, cqlAbstractSyntaxTree, *args, **kwargs):
        response = yield self.any.executeQuery(luceneQuery=self._convert(cqlAbstractSyntaxTree), *args, **kwargs)
        raise StopIteration(response)

    def _convert(self, ast):
        ClauseCollector(ast, self.log).visit()
        return self._cqlComposer.compose(ast)