# -*- encoding: utf-8 -*-
## begin license ##
#
# "Meresco Lucene" is a set of components and tools to integrate Lucene (based on PyLucene) into Meresco
#
# Copyright (C) 2013-2015 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2013-2014 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
# Copyright (C) 2015 Koninklijke Bibliotheek (KB) http://www.kb.nl
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


from os.path import join

from cqlparser import parseString as parseCql

from weightless.core import consume, retval

from meresco.lucene import Lucene, DrilldownField, LuceneSettings
from meresco.lucene._lucene import IDFIELD
from meresco.lucene.hit import Hit
from meresco.lucene.fieldregistry import NO_TERMS_FREQUENCY_FIELD, FieldRegistry, INTFIELD, STRINGFIELD_STORED
from meresco.lucene.lucenequerycomposer import LuceneQueryComposer

from org.apache.lucene.search import MatchAllDocsQuery, TermQuery, TermRangeQuery, BooleanQuery, BooleanClause, PhraseQuery
from org.apache.lucene.document import Document, TextField, Field, NumericDocValuesField, StringField
from org.apache.lucene.index import Term
from org.apache.lucene.facet import FacetField
from org.meresco.lucene.analysis import MerescoDutchStemmingAnalyzer

from seecr.test.io import stdout_replaced

from lucenetestcase import LuceneTestCase


class LuceneTest(LuceneTestCase):
    def setUp(self):
        super(LuceneTest, self).setUp(FIELD_REGISTRY)

    def hitIds(self, hits):
        return [hit.id for hit in hits]

    def testCreate(self):
        result = retval(self.lucene.executeQuery(MatchAllDocsQuery()))
        self.assertEquals(0, result.total)
        self.assertTrue(hasattr(result, 'times'))

    def testAdd1DocumentWithReadonlyLucene(self):
        settings = LuceneSettings(commitTimeout=1, verbose=False, readonly=True)
        readOnlyLucene = Lucene(
            join(self.tempdir, 'lucene'),
            reactor=self._reactor,
            settings=settings,
        )
        self.assertEquals(['addTimer'], self._reactor.calledMethodNames())
        timer = self._reactor.calledMethods[0]
        document = Document()
        document.add(TextField('title', 'The title', Field.Store.NO))
        retval(self.lucene.addDocument(identifier="identifier", document=document))
        result = retval(readOnlyLucene.executeQuery(MatchAllDocsQuery()))
        self.assertEquals(0, result.total)
        timer.kwargs['callback']()
        result = retval(readOnlyLucene.executeQuery(MatchAllDocsQuery()))
        self.assertEquals(1, result.total)

        readOnlyLucene.close()
        readOnlyLucene = None

    def testAddDocumentWithoutIdentifier(self):
        retval(self.lucene.addDocument(document=Document()))
        retval(self.lucene.addDocument(document=Document()))
        result = retval(self.lucene.executeQuery(MatchAllDocsQuery()))
        self.assertEquals(2, result.total)
        self.assertEquals([None, None], self.hitIds(result.hits))

    def testForceCommit(self):
        self.lucene.close()
        self._defaultSettings.commitTimeout = 42
        self._defaultSettings.commitCount = 3
        self.lucene = Lucene(join(self.tempdir, 'lucene'), reactor=self._reactor, settings=self._defaultSettings)
        retval(self.lucene.addDocument(identifier="id:0", document=Document()))
        self.assertEquals(['addTimer'], self._reactor.calledMethodNames())
        self.assertEquals(42, self._reactor.calledMethods[0].kwargs['seconds'])
        self._reactor.calledMethods.reset()
        result = retval(self.lucene.executeQuery(MatchAllDocsQuery()))
        self.assertEquals(0, result.total)
        self.lucene.forceCommit()
        self.assertEquals(['removeTimer'], self._reactor.calledMethodNames())
        result = retval(self.lucene.executeQuery(MatchAllDocsQuery()))
        self.assertEquals(1, result.total)

    def testFacetsInMultipleFields(self):
        retval(self.lucene.addDocument(identifier="id:0", document=createDocument([('field1', 'id:0')], facets=[('facet-field2', 'first item0'), ('facet-field3', 'second item')])))
        retval(self.lucene.addDocument(identifier="id:1", document=createDocument([('field1', 'id:1')], facets=[('facet-field2', 'first item1'), ('facet-field3', 'other value')])))
        retval(self.lucene.addDocument(identifier="id:2", document=createDocument([('field1', 'id:2')], facets=[('facet-field2', 'first item2'), ('facet-field3', 'second item')])))
        retval(self.lucene.addDocument(identifier="id:2", document=createDocument([('field1', 'id:2')], facets=[('field_other', 'first item1'), ('facet-field3', 'second item')])))

        self.assertEquals(set([u'$facets', u'other', u'__id__', u'field1']), set(self.lucene._index.fieldnames()))

    def testFacetsWithMultipleFields(self):
        retval(self.lucene.addDocument(identifier="id:0", document=createDocument([('field1', 'id:0')], facets=[('facet-field3', 'value')])))
        retval(self.lucene.addDocument(identifier="id:1", document=createDocument([('field1', 'id:1')], facets=[('field_other', 'other_value')])))

        result = retval(self.lucene.executeQuery(MatchAllDocsQuery(), facets=[dict(maxTerms=10, fieldname='facet-field3'), dict(maxTerms=10, fieldname='field_other')]))

        self.assertEquals([
                {   'path': [],
                    'terms': [{'count': 1, 'term': 'value'}],
                    'fieldname': 'facet-field3'
                }, {
                    'path': [],
                    'terms': [{'count': 1, 'term': 'other_value'}],
                    'fieldname': 'field_other'
                }
            ],result.drilldownData)

    def testFacetsWithMultipleFieldsWillOnlyUseNecessaryOrdinalReaders(self):
        retval(self.lucene.addDocument(identifier="id:0", document=createDocument([('field1', 'id:0')], facets=[('facet-field3', 'value')])))
        retval(self.lucene.addDocument(identifier="id:1", document=createDocument([('field1', 'id:1')], facets=[('field_other', 'other_value')])))

        self.observer.calledMethods.reset()
        consume(self.lucene.executeQuery(MatchAllDocsQuery(), facets=[dict(maxTerms=10, fieldname='facet-field3'), dict(maxTerms=10, fieldname='field_other')]))
        self.assertEquals(['log'], self.observer.calledMethodNames())
        self.assertEquals('[LuceneIndex] lucene: FacetSuperCollector with 2 ordinal readers.\n', self.observer.calledMethods[0].kwargs['message'])

        self.observer.calledMethods.reset()
        consume(self.lucene.executeQuery(MatchAllDocsQuery(), facets=[dict(maxTerms=10, fieldname='field_other')]))
        self.assertEquals(['log'], self.observer.calledMethodNames())
        self.assertEquals('[LuceneIndex] lucene: FacetSuperCollector with 1 ordinal readers.\n', self.observer.calledMethods[0].kwargs['message'])


    def testFacetsWithUnsupportedSortBy(self):
        try:
            retval(self.lucene.executeQuery(MatchAllDocsQuery(), facets=[dict(maxTerms=10, fieldname='facet-field2', sortBy='incorrectSort')]))
        except ValueError, e:
            self.assertEquals("""Value of "sortBy" should be in ['count']""", str(e))

    def testFacetsOnUnknownField(self):
        result = retval(self.lucene.executeQuery(MatchAllDocsQuery(), facets=[dict(maxTerms=10, fieldname='fieldUnknonw')]))
        self.assertEquals([], result.drilldownData)

    def testFacetsMaxTerms0(self):
        self.lucene._index._commitCount = 3
        retval(self.lucene.addDocument(identifier="id:0", document=createDocument([('field1', 'id:0')], facets=[('facet-field2', 'first item0'), ('facet-field3', 'second item')])))
        retval(self.lucene.addDocument(identifier="id:1", document=createDocument([('field1', 'id:1')], facets=[('facet-field2', 'first item1'), ('facet-field3', 'other value')])))
        retval(self.lucene.addDocument(identifier="id:2", document=createDocument([('field1', 'id:2')], facets=[('facet-field2', 'first item2'), ('facet-field3', 'second item')])))

        result = retval(self.lucene.executeQuery(MatchAllDocsQuery(), facets=[dict(maxTerms=0, fieldname='facet-field3')]))
        self.assertEquals([{
                'fieldname': 'facet-field3',
                'path': [],
                'terms': [
                    {'term': 'second item', 'count': 2},
                    {'term': 'other value', 'count': 1},
                ],
            }],result.drilldownData)

    def testFacetsWithCategoryPathHierarchy(self):
        retval(self.lucene.addDocument(identifier="id:0", document=createDocument([('field1', 'id:0')], facets=[('fieldHier', ['item0', 'item1'])])))
        retval(self.lucene.addDocument(identifier="id:1", document=createDocument([('field1', 'id:1')], facets=[('fieldHier', ['item0', 'item2'])])))
        retval(self.lucene.addDocument(identifier="id:2", document=createDocument([('field1', 'id:2')], facets=[('fieldHier', ['item3', 'item4'])])))
        result = retval(self.lucene.executeQuery(MatchAllDocsQuery(), facets=[dict(maxTerms=10, path=[], fieldname='fieldHier')]))
        self.assertEquals([{
                'fieldname': 'fieldHier',
                'path': [],
                'terms': [
                    {
                        'term': 'item0',
                        'count': 2,
                        'subterms': [
                            {'term': 'item1', 'count': 1},
                            {'term': 'item2', 'count': 1},
                        ]
                    },
                    {
                        'term': 'item3',
                        'count': 1,
                        'subterms': [
                            {'term': 'item4', 'count': 1},
                        ]
                    }
                ],
            }], result.drilldownData)

        result = retval(self.lucene.executeQuery(MatchAllDocsQuery(), facets=[dict(maxTerms=10, fieldname='fieldHier', path=['item0'])]))
        self.assertEquals([{
                'fieldname': 'fieldHier',
                'path': ['item0'],
                'terms': [
                    {'term': 'item1', 'count': 1},
                    {'term': 'item2', 'count': 1},
                ],
            }], result.drilldownData)

    def XX_testFacetsWithIllegalCharacters(self):
        categories = createCategories([('field', 'a/b')])
        # The following print statement causes an error to be printed to stderr.
        # It keeps on working.
        self.assertEquals('[<CategoryPath: class org.apache.lucene.facet.taxonomy.CategoryPath>]', str(categories))
        retval(self.lucene.addDocument(identifier="id:0", document=createDocument([]), categories=categories))
        result = retval(self.lucene.executeQuery(MatchAllDocsQuery(), facets=[dict(maxTerms=10, fieldname='field')]))
        self.assertEquals([{
                'fieldname': 'field',
                'terms': [
                    {'term': 'a/b', 'count': 1},
                ],
            }],result.drilldownData)

    def testEscapeFacets(self):
        retval(self.lucene.addDocument(identifier="id:0", document=createDocument([('field1', 'id:0')], facets=[('facet-field3', 'first/item0')])))
        result = retval(self.lucene.executeQuery(MatchAllDocsQuery(), facets=[dict(maxTerms=10, fieldname='facet-field3')]))
        self.assertEquals([{
                'terms': [{'count': 1, 'term': u'first/item0'}],
                'path': [],
                'fieldname': u'facet-field3'
            }],result.drilldownData)

    def testDiacritics(self):
        retval(self.lucene.addDocument(identifier='hendrik', document=createDocument([('title', 'Waar is Morée vandaag?')])))
        result = retval(self.lucene.executeQuery(TermQuery(Term('title', 'moree'))))
        self.assertEquals(1, result.total)
        query = LuceneQueryComposer(unqualifiedTermFields=[], luceneSettings=LuceneSettings()).compose(parseCql("title=morée"))
        result = retval(self.lucene.executeQuery(query))
        self.assertEquals(1, result.total)

    def testFilterQueries(self):
        for i in xrange(10):
            retval(self.lucene.addDocument(identifier="id:%s" % i, document=createDocument([
                    ('mod2', 'v%s' % (i % 2)),
                    ('mod3', 'v%s' % (i % 3))
                ])))
        # id     0  1  2  3  4  5  6  7  8  9
        # mod2  v0 v1 v0 v1 v0 v1 v0 v1 v0 v1
        # mod3  v0 v1 v2 v0 v1 v2 v0 v1 v2 v0
        result = retval(self.lucene.executeQuery(MatchAllDocsQuery(), filterQueries=[TermQuery(Term('mod2', 'v0'))]))
        self.assertEquals(5, result.total)
        self.assertEquals(set(['id:0', 'id:2', 'id:4', 'id:6', 'id:8']), set(self.hitIds(result.hits)))
        result = retval(self.lucene.executeQuery(MatchAllDocsQuery(), filterQueries=[
                TermQuery(Term('mod2', 'v0')),
                TermQuery(Term('mod3', 'v0')),
            ]))
        self.assertEquals(2, result.total)
        self.assertEquals(set(['id:0', 'id:6']), set(self.hitIds(result.hits)))

    def testPrefixSearchForIntField(self):
        retval(self.lucene.addDocument(identifier='id:0', document=createDocument([('intField', 1)])))
        for i in xrange(5):
            retval(self.lucene.addDocument(identifier='id:%s' % (i+20), document=createDocument([('intField', i+20)])))
        response = retval(self.lucene.prefixSearch(fieldname='intField', prefix=None))
        self.assertEquals([0, 0, 0, 24, 23, 22, 21, 20, 1], response.hits) # No fix for the 0's yet

    def testRangeQuery(self):
        for f in ['aap', 'noot', 'mies', 'vis', 'vuur', 'boom']:
            retval(self.lucene.addDocument(identifier="id:%s" % f, document=createDocument([('field', f)])))
        # (field, lowerTerm, upperTerm, includeLower, includeUpper)
        luceneQuery = TermRangeQuery.newStringRange('field', None, 'mies', False, False) # <
        response = retval(self.lucene.executeQuery(luceneQuery=luceneQuery))
        self.assertEquals(set(['id:aap', 'id:boom']), set(self.hitIds(response.hits)))
        luceneQuery = TermRangeQuery.newStringRange('field', None, 'mies', False, True) # <=
        response = retval(self.lucene.executeQuery(luceneQuery=luceneQuery))
        self.assertEquals(set(['id:aap', 'id:boom', 'id:mies']), set(self.hitIds(response.hits)))
        luceneQuery = TermRangeQuery.newStringRange('field', 'mies', None, False, True) # >
        response = retval(self.lucene.executeQuery(luceneQuery=luceneQuery))
        self.assertEquals(set(['id:noot', 'id:vis', 'id:vuur']), set(self.hitIds(response.hits)))
        luceneQuery = LuceneQueryComposer(unqualifiedTermFields=[], luceneSettings=LuceneSettings()).compose(parseCql('field >= mies'))
        response = retval(self.lucene.executeQuery(luceneQuery=luceneQuery))
        self.assertEquals(set(['id:mies', 'id:noot', 'id:vis', 'id:vuur']), set(self.hitIds(response.hits)))

    def testHandleShutdown(self):
        document = Document()
        document.add(TextField('title', 'The title', Field.Store.NO))
        retval(self.lucene.addDocument(identifier="identifier", document=document))
        with stdout_replaced():
            self.lucene.handleShutdown()
        lucene = Lucene(join(self.tempdir, 'lucene'), reactor=self._reactor, settings=self._defaultSettings)
        response = retval(lucene.executeQuery(luceneQuery=MatchAllDocsQuery()))
        self.assertEquals(1, response.total)

    def testDutchStemming(self):
        self.lucene.close()
        settings = LuceneSettings(commitCount=1, analyzer=MerescoDutchStemmingAnalyzer(), verbose=False)
        self.lucene = Lucene(join(self.tempdir, 'lucene'), reactor=self._reactor, settings=settings)
        doc = document(field0='katten en honden')
        consume(self.lucene.addDocument(identifier="urn:1", document=doc))
        self.lucene.commit()

        result = retval(self.lucene.executeQuery(TermQuery(Term("field0", 'katten'))))
        self.assertEquals(1, result.total)

        result = retval(self.lucene.executeQuery(TermQuery(Term("field0", 'kat'))))
        self.assertEquals(1, result.total)

        q = self.createPhraseQuery("field0", "katten", "en", "honden")
        result = retval(self.lucene.executeQuery(q))
        self.assertEquals(1, result.total)

        q = self.createPhraseQuery("field0", "kat", "en", "honden")
        result = retval(self.lucene.executeQuery(q))
        self.assertEquals(1, result.total)

        q = self.createPhraseQuery("field0", "katten", "en", "hond")
        result = retval(self.lucene.executeQuery(q))
        self.assertEquals(1, result.total)

        q = self.createPhraseQuery("field0", "kat", "en", "hond")
        result = retval(self.lucene.executeQuery(q))
        self.assertEquals(1, result.total)

    def createPhraseQuery(self, field, *args):
        q = PhraseQuery()
        for term in args:
            q.add(Term(field, term))
        return q

    def testDrilldownQuery(self):
        doc = createDocument(fields=[("field0", 'v1')], facets=[("cat", "cat-A")])
        consume(self.lucene.addDocument(identifier="urn:1", document=doc))
        doc = createDocument(fields=[("field0", 'v2')], facets=[("cat", "cat-B")])
        consume(self.lucene.addDocument(identifier="urn:2", document=doc))

        result = retval(self.lucene.executeQuery(MatchAllDocsQuery()))
        self.assertEquals(2, result.total)

        result = retval(self.lucene.executeQuery(MatchAllDocsQuery(), drilldownQueries=[("cat", ["cat-A"])]))
        self.assertEquals(1, result.total)

        result = retval(self.lucene.executeQuery(TermQuery(Term("field0", "v2")), drilldownQueries=[("cat", ["cat-A"])]))
        self.assertEquals(0, result.total)

    def testMultipleDrilldownQueryOnSameField(self):
        doc = createDocument(fields=[("field0", 'v1')], facets=[("cat", "cat-A"), ("cat", "cat-B")])
        consume(self.lucene.addDocument(identifier="urn:1", document=doc))
        doc = createDocument(fields=[("field0", 'v1')], facets=[("cat", "cat-B",)])
        consume(self.lucene.addDocument(identifier="urn:2", document=doc))
        doc = createDocument(fields=[("field0", 'v1')], facets=[("cat", "cat-C",)])
        consume(self.lucene.addDocument(identifier="urn:3", document=doc))

        result = retval(self.lucene.executeQuery(MatchAllDocsQuery()))
        self.assertEquals(3, result.total)

        result = retval(self.lucene.executeQuery(MatchAllDocsQuery(), drilldownQueries=[("cat", ["cat-A"]), ("cat", ["cat-B"])]))
        self.assertEquals(1, result.total)

    def testNoTermFrequency(self):
        factory = FieldRegistry()
        factory.register("no.term.frequency", NO_TERMS_FREQUENCY_FIELD)
        factory.register("no.term.frequency2", NO_TERMS_FREQUENCY_FIELD)
        doc = Document()
        doc.add(factory.createField("no.term.frequency", "aap noot noot noot vuur"))
        consume(self.lucene.addDocument(identifier="no.term.frequency", document=doc))

        doc = createDocument(fields=[('term.frequency', "aap noot noot noot vuur")])
        consume(self.lucene.addDocument(identifier="term.frequency", document=doc))

        doc = Document()
        doc.add(factory.createField("no.term.frequency2", "aap noot"))
        doc.add(factory.createField("no.term.frequency2", "noot noot"))
        doc.add(factory.createField("no.term.frequency2", "vuur"))
        consume(self.lucene.addDocument(identifier="no.term.frequency2", document=doc))

        result1 = retval(self.lucene.executeQuery(TermQuery(Term("no.term.frequency", "aap"))))
        result2 = retval(self.lucene.executeQuery(TermQuery(Term("no.term.frequency", "noot"))))
        self.assertEquals(result1.hits[0].score, result2.hits[0].score)

        result1 = retval(self.lucene.executeQuery(TermQuery(Term("term.frequency", "aap"))))
        result2 = retval(self.lucene.executeQuery(TermQuery(Term("term.frequency", "noot"))))
        self.assertNotEquals(result1.hits[0].score, result2.hits[0].score)
        self.assertTrue(result1.hits[0].score < result2.hits[0].score)

        result1 = retval(self.lucene.executeQuery(TermQuery(Term("no.term.frequency2", "aap"))))
        result2 = retval(self.lucene.executeQuery(TermQuery(Term("no.term.frequency2", "noot"))))
        self.assertEquals(result1.hits[0].score, result2.hits[0].score)

        bq = BooleanQuery()
        bq.add(TermQuery(Term('no.term.frequency', 'aap')),BooleanClause.Occur.MUST)
        bq.add(TermQuery(Term('no.term.frequency', 'noot')),BooleanClause.Occur.MUST)
        self.assertEquals(1, len(retval(self.lucene.executeQuery(bq)).hits))

    def testUpdateReaderSettings(self):
        settings = self.lucene.getSettings()
        self.assertEquals({'numberOfConcurrentTasks': 6, 'similarity': u'BM25(k1=1.2,b=0.75)', 'clusterMoreRecords': 100, 'clusteringEps': 0.4, 'clusteringMinPoints': 1}, settings)

        self.lucene.setSettings(similarity=dict(k1=1.0, b=2.0), numberOfConcurrentTasks=10, clusterMoreRecords=200, clusteringEps=1.0, clusteringMinPoints=2)
        settings = self.lucene.getSettings()
        self.assertEquals({'numberOfConcurrentTasks': 10, 'similarity': u'BM25(k1=1.0,b=2.0)', 'clusterMoreRecords': 200, 'clusteringEps': 1.0, 'clusteringMinPoints': 2}, settings)

        self.lucene.setSettings(numberOfConcurrentTasks=None, similarity=None, clusterMoreRecords=None, clusteringEps=None)
        settings = self.lucene.getSettings()
        self.assertEquals({'numberOfConcurrentTasks': 6, 'similarity': u'BM25(k1=1.2,b=0.75)', 'clusterMoreRecords': 100, 'clusteringEps': 0.4, 'clusteringMinPoints': 1}, settings)

    def testStoredFields(self):
        doc = Document()
        doc.add(FIELD_REGISTRY.createField("storedField", "this field is stored"))
        consume(self.lucene.addDocument(identifier='id1', document=doc))

        result = retval(self.lucene.executeQuery(MatchAllDocsQuery(), storedFields=['storedField']))
        self.assertEqual(1, result.total)
        self.assertEqual('id1', result.hits[0].id)
        self.assertEqual(['this field is stored'], result.hits[0].storedField)

def facets(**fields):
    return [dict(fieldname=name, maxTerms=max_) for name, max_ in fields.items()]

def document(**fields):
    return createDocument(fields.items())

FIELD_REGISTRY = FieldRegistry(
    drilldownFields=[
            DrilldownField(name='facet-field2'),
            DrilldownField(name='facet-field3'),
            DrilldownField('field_other', indexFieldName='other'),
            DrilldownField('fieldHier', hierarchical=True),
            DrilldownField('cat'),
        ]
    )
FIELD_REGISTRY.register(fieldname='intField', fieldDefinition=INTFIELD)
FIELD_REGISTRY.register(fieldname='storedField', fieldDefinition=STRINGFIELD_STORED)

def createDocument(fields, facets=None, registry=FIELD_REGISTRY):
    document = Document()
    for name, value in fields:
        document.add(registry.createField(name, value))
    for facet, value in facets or []:
        if hasattr(value, 'extend'):
            path = [str(category) for category in value]
        else:
            path = [str(value)]
        document.add(FacetField(facet, path))
    return document
