## begin license ##
#
# "Meresco Lucene" is a set of components and tools to integrate Lucene (based on PyLucene) into Meresco
#
# Copyright (C) 2013-2016 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2013-2014 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
# Copyright (C) 2015 Drents Archief http://www.drentsarchief.nl
# Copyright (C) 2015-2016 Koninklijke Bibliotheek (KB) http://www.kb.nl
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

from collections import defaultdict

from cqlparser import cqlToExpression
from cqlparser.cqltoexpression import QueryExpression

from meresco.core import Observable, asyncnoreturnvalue
from meresco.lucene import ComposedQuery
from meresco.lucene.extractfilterqueries import ExtractFilterQueries


class ConvertToComposedQuery(Observable):
    def __init__(self, resultsFrom, matches=None, dedupFieldName=None, dedupSortFieldName=None, dedupByDefault=True, groupingFieldName=None, drilldownFieldnamesTranslate=lambda s: s):
        Observable.__init__(self)
        self._resultsFrom = resultsFrom
        self._matches = matches or []
        self._cores = set(cSpec['core'] for match in self._matches for cSpec in match)
        self._dedupFieldName = dedupFieldName
        self._dedupSortFieldName = dedupSortFieldName
        self._dedupByDefault = dedupByDefault
        self._groupingFieldName = groupingFieldName
        self._drilldownFieldnamesTranslate = drilldownFieldnamesTranslate
        self._groupingEnabled = bool(self._groupingFieldName)
        self._clusteringEnabled = True
        self._extraFilterQueries = ExtractFilterQueries(self._cores)

    @asyncnoreturnvalue
    def updateConfig(self, config, indexConfig=None, **kwargs):
        self._groupingEnabled = bool(self._groupingFieldName) and 'grouping' not in config.get('features_disabled', [])
        self._clusteringEnabled = 'clustering' not in config.get('features_disabled', [])

    def executeQuery(self, query=None, extraArguments=None, facets=None, drilldownQueries=None, filterQueries=None, sortKeys=None, **kwargs):
        if 'cqlAbstractSyntaxTree' in kwargs:
            query = kwargs.pop('cqlAbstractSyntaxTree')
        query = cqlToExpression(query)

        extraArguments = extraArguments or {}
        cq = ComposedQuery(self._resultsFrom)
        for matchTuple in self._matches:
            cq.addMatch(*matchTuple)

        for key in ['start', 'stop', 'suggestionRequest']:
            if key in kwargs:
                setattr(cq, key, kwargs[key])

        coreQuery, filters = self._extraFilterQueries.convert(query, self._resultsFrom)
        if coreQuery:
            cq.setCoreQuery(core=self._resultsFrom, query=coreQuery)
        for core, aFilter in ((core, aFilter) for core, filters in filters.items() for aFilter in filters):
            cq.addFilterQuery(core, aFilter)

        for sortKey in sortKeys or []:
            core, sortBy = self._parseCorePrefix(sortKey['sortBy'], self._cores)
            cq.addSortKey(dict(sortKey, core=core, sortBy=sortBy))

        filters = extraArguments.get('x-filter', [])
        for f in filters:
            core, filterQuery = self._coreQuery(query=f, cores=self._cores)
            cq.addFilterQuery(core=core, query=filterQuery)
        for core, filterQuery in filterQueries or []:
            cq.addFilterQuery(core=core, query=cqlToExpression(filterQuery))

        rankQueries = extraArguments.get('x-rank-query', [])
        if rankQueries:
            queries = defaultdict(list)
            for rankQuery in rankQueries:
                core, rankQuery = self._parseCorePrefix(rankQuery, self._cores)
                queries[core].append(rankQuery)
            for core, q in queries.items():
                cq.setRankQuery(core=core, query=cqlToExpression(' OR '.join(q)))

        if self._dedupFieldName:
            if 'true' == extraArguments.get('x-filter-common-keys', ['true' if self._dedupByDefault else 'false'])[0]:
                setattr(cq, "dedupField", self._dedupFieldName)
                setattr(cq, "dedupSortField", self._dedupSortFieldName)

        if self._groupingEnabled and 'true' == extraArguments.get('x-grouping', [None])[0]:
            if coreQuery != QueryExpression.searchterm(term='*'):
                setattr(cq, "groupingField", self._groupingFieldName)

        if self._clusteringEnabled and 'true' == extraArguments.get('x-clustering', [None])[0]:
            setattr(cq, "clustering", True)

        facetOrder = []
        fieldTranslations = {}
        for drilldownField in (facets or []):
            path = drilldownField['fieldname'].split('>')
            fieldname, path = path[0], path[1:]
            facetOrder.append((fieldname, path))
            core, newFieldname = self._coreFacet(fieldname, self._cores)
            newFieldname = self._drilldownFieldnamesTranslate(newFieldname)
            fieldTranslations[newFieldname] = fieldname
            cq.addFacet(core=core, facet=dict(fieldname=newFieldname, path=path, maxTerms=drilldownField['maxTerms']))

        for drilldownQuery in (drilldownQueries or []):
            core, fieldname = self._coreDrilldownQuery(drilldownQuery[0], self._cores)
            fieldname = self._drilldownFieldnamesTranslate(fieldname)
            cq.addDrilldownQuery(core=core, drilldownQuery=(fieldname, drilldownQuery[1]))

        result = yield self.any.executeComposedQuery(query=cq)

        drilldownData = getattr(result, "drilldownData", None)
        if drilldownData:
            for facet in drilldownData:
                fieldname = facet['fieldname']
                facet['fieldname'] = fieldTranslations.get(fieldname, fieldname)
            result.drilldownData = sorted(
                drilldownData,
                key=lambda d: facetOrder.index((d['fieldname'], d.get('path', [])))
            )

        raise StopIteration(result)

    def _coreQuery(self, query, cores):
        core, query = self._parseCorePrefix(query, cores)
        return core, cqlToExpression(query)

    def _coreFacet(self, fieldname, cores):
        return self._parseCorePrefix(fieldname, cores)

    def _coreDrilldownQuery(self, drilldownQueryField, cores):
        return self._parseCorePrefix(drilldownQueryField, cores)

    def _parseCorePrefix(self, value, cores):
        if value.startswith(self._resultsFrom):
            return self._resultsFrom, value
        core = self._resultsFrom
        try:
            tmpcore, tail = value.split('.', 1)
            if tmpcore in cores:
                core = tmpcore
                value = tail
        except ValueError:
            pass
        return core, value
