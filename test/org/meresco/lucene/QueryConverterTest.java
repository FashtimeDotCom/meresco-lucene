/* begin license *
 *
 * "Meresco Lucene" is a set of components and tools to integrate Lucene (based on PyLucene) into Meresco
 *
 * Copyright (C) 2015 Koninklijke Bibliotheek (KB) http://www.kb.nl
 * Copyright (C) 2015-2016 Seecr (Seek You Too B.V.) http://seecr.nl
 *
 * This file is part of "Meresco Lucene"
 *
 * "Meresco Lucene" is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * "Meresco Lucene" is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with "Meresco Lucene"; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 *
 * end license */

package org.meresco.lucene;

import static org.junit.Assert.*;

import java.io.StringReader;
import java.util.List;

import javax.json.Json;
import javax.json.JsonObject;
import javax.json.JsonValue;

import org.apache.lucene.facet.DrillDownQuery;
import org.apache.lucene.facet.FacetsConfig;
import org.apache.lucene.index.Term;
import org.apache.lucene.search.BooleanClause.Occur;
import org.apache.lucene.search.BooleanQuery;
import org.apache.lucene.search.MatchAllDocsQuery;
import org.apache.lucene.search.NumericRangeQuery;
import org.apache.lucene.search.PhraseQuery;
import org.apache.lucene.search.PrefixQuery;
import org.apache.lucene.search.SortField;
import org.apache.lucene.search.TermQuery;
import org.apache.lucene.search.TermRangeQuery;
import org.apache.lucene.search.WildcardQuery;
import org.junit.Test;
import org.meresco.lucene.QueryConverter.FacetRequest;

public class QueryConverterTest {


    private QueryConverter queryConverter = new QueryConverter(new FacetsConfig());

    @Test
    public void testTermQuery() {
        JsonObject json = Json.createObjectBuilder()
                .add("query", Json.createObjectBuilder()
                    .add("type", "TermQuery")
                    .add("term", Json.createObjectBuilder()
                        .add("field", "field")
                        .add("value", "value")))
                .build();
        QueryData q = new QueryData(new StringReader(json.toString()), queryConverter);
        assertEquals(new TermQuery(new Term("field", "value")), q.query);
    }

    @Test
    public void testTermQueryWithBoost() {
        JsonObject json = Json.createObjectBuilder()
                .add("query", Json.createObjectBuilder()
                    .add("type", "TermQuery")
                    .add("boost", 2.1)
                    .add("term", Json.createObjectBuilder()
                        .add("field", "field")
                        .add("value", "value")))
                .build();
        QueryData q = new QueryData(new StringReader(json.toString()), queryConverter);
        TermQuery query = new TermQuery(new Term("field", "value"));
        query.setBoost(2.1f);
        assertEquals(query, q.query);
    }

    @Test
    public void testMatchAllDocsQuery() {
        JsonObject json = Json.createObjectBuilder()
                .add("query", Json.createObjectBuilder()
                        .add("type", "MatchAllDocsQuery"))
                .build();
        QueryData q = new QueryData(new StringReader(json.toString()), queryConverter);
        assertEquals(new MatchAllDocsQuery(), q.query);
    }

    @Test
    public void testBooleanShouldQuery() {
        JsonObject json = Json.createObjectBuilder()
                .add("query", Json.createObjectBuilder()
                    .add("type", "BooleanQuery")
                    .add("clauses", Json.createArrayBuilder()
                            .add(Json.createObjectBuilder()
                                .add("type", "TermQuery")
                                .add("boost", 1.0)
                                .add("occur", "SHOULD")
                                .add("term", Json.createObjectBuilder()
                                    .add("field", "aField")
                                    .add("value", "value")))
                            .add(Json.createObjectBuilder()
                                .add("type", "TermQuery")
                                .add("boost", 2.0)
                                .add("occur", "SHOULD")
                                .add("term", Json.createObjectBuilder()
                                    .add("field", "oField")
                                    .add("value", "value")))))
                .build();
        QueryData q = new QueryData(new StringReader(json.toString()), queryConverter);
        TermQuery aQuery = new TermQuery(new Term("aField", "value"));
        aQuery.setBoost(1.0f);
        TermQuery oQuery = new TermQuery(new Term("oField", "value"));
        oQuery.setBoost(2.0f);
        BooleanQuery query = new BooleanQuery();
        query.add(aQuery, Occur.SHOULD);
        query.add(oQuery, Occur.SHOULD);
        assertEquals(query, q.query);
    }

    @Test
    public void testBooleanMustQuery() {
        JsonObject json = Json.createObjectBuilder()
                .add("query", Json.createObjectBuilder()
                    .add("type", "BooleanQuery")
                    .add("clauses", Json.createArrayBuilder()
                            .add(Json.createObjectBuilder()
                                .add("type", "TermQuery")
                                .add("boost", 1.0)
                                .add("occur", "MUST")
                                .add("term", Json.createObjectBuilder()
                                    .add("field", "aField")
                                    .add("value", "value")))
                            .add(Json.createObjectBuilder()
                                .add("type", "TermQuery")
                                .add("boost", 2.0)
                                .add("occur", "MUST_NOT")
                                .add("term", Json.createObjectBuilder()
                                    .add("field", "oField")
                                    .add("value", "value")))))
                .build();
        QueryData q = new QueryData(new StringReader(json.toString()), queryConverter);
        TermQuery aQuery = new TermQuery(new Term("aField", "value"));
        aQuery.setBoost(1.0f);
        TermQuery oQuery = new TermQuery(new Term("oField", "value"));
        oQuery.setBoost(2.0f);
        BooleanQuery query = new BooleanQuery();
        query.add(aQuery, Occur.MUST);
        query.add(oQuery, Occur.MUST_NOT);
        assertEquals(query, q.query);
    }

    @Test
    public void testWildcardQuery() {
        JsonObject json = Json.createObjectBuilder()
                .add("query", Json.createObjectBuilder()
                    .add("type", "WildcardQuery")
                    .add("term", Json.createObjectBuilder()
                        .add("field", "field")
                        .add("value", "???*")))
                .build();
        QueryData q = new QueryData(new StringReader(json.toString()), queryConverter);
        WildcardQuery query = new WildcardQuery(new Term("field", "???*"));
        assertEquals(query, q.query);
    }

    @Test
    public void testPrefixQuery() {
        JsonObject json = Json.createObjectBuilder()
                .add("query", Json.createObjectBuilder()
                    .add("type", "PrefixQuery")
                    .add("term", Json.createObjectBuilder()
                        .add("field", "field")
                        .add("value", "fiet")))
                .build();
        QueryData q = new QueryData(new StringReader(json.toString()), queryConverter);
        PrefixQuery query = new PrefixQuery(new Term("field", "fiet"));
        assertEquals(query, q.query);
    }

    @Test
    public void testPhraseQuery() {
        JsonObject json = Json.createObjectBuilder()
                .add("query", Json.createObjectBuilder()
                    .add("type", "PhraseQuery")
                    .add("terms", Json.createArrayBuilder()
                        .add(Json.createObjectBuilder()
                            .add("field", "field")
                            .add("value", "phrase"))
                        .add(Json.createObjectBuilder()
                            .add("field", "field")
                            .add("value", "query"))))
                .build();
        QueryData q = new QueryData(new StringReader(json.toString()), queryConverter);
        PhraseQuery query = new PhraseQuery();
        query.add(new Term("field", "phrase"));
        query.add(new Term("field", "query"));
        assertEquals(query, q.query);
    }

    @Test
    public void testTermRangeQueryBigger() {
        JsonObject json = Json.createObjectBuilder()
                .add("query", Json.createObjectBuilder()
                    .add("type", "RangeQuery")
                    .add("rangeType", "String")
                    .add("field", "field")
                    .add("lowerTerm", "value")
                    .add("upperTerm", JsonValue.NULL)
                    .add("includeLower", JsonValue.FALSE)
                    .add("includeUpper", JsonValue.FALSE))
                .build();
        QueryData q = new QueryData(new StringReader(json.toString()), queryConverter);
        TermRangeQuery query = TermRangeQuery.newStringRange("field", "value", null, false, false);
        assertEquals(query, q.query);
    }

    @Test
    public void testTermRangeQueryLower() {
        JsonObject json = Json.createObjectBuilder()
                .add("query", Json.createObjectBuilder()
                    .add("type", "RangeQuery")
                    .add("rangeType", "String")
                    .add("field", "field")
                    .add("lowerTerm", JsonValue.NULL)
                    .add("upperTerm", "value")
                    .add("includeLower", JsonValue.TRUE)
                    .add("includeUpper", JsonValue.TRUE))
                .build();
        QueryData q = new QueryData(new StringReader(json.toString()), queryConverter);
        TermRangeQuery query = TermRangeQuery.newStringRange("field", null, "value", true, true);
        assertEquals(query, q.query);
    }

    @Test
    public void testIntRangeQuery() {
        JsonObject json = Json.createObjectBuilder()
                .add("query", Json.createObjectBuilder()
                    .add("type", "RangeQuery")
                    .add("rangeType", "Int")
                    .add("field", "field")
                    .add("lowerTerm", 1)
                    .add("upperTerm", 5)
                    .add("includeLower", JsonValue.FALSE)
                    .add("includeUpper", JsonValue.TRUE))
                .build();
        QueryData q = new QueryData(new StringReader(json.toString()), queryConverter);
        NumericRangeQuery<Integer> query = NumericRangeQuery.newIntRange("field", 1, 5, false, true);
        assertEquals(query, q.query);
    }

    @Test
    public void testLongRangeQuery() {
        JsonObject json = Json.createObjectBuilder()
                .add("query", Json.createObjectBuilder()
                    .add("type", "RangeQuery")
                    .add("rangeType", "Long")
                    .add("field", "field")
                    .add("lowerTerm", 1L)
                    .add("upperTerm", 5L)
                    .add("includeLower", JsonValue.FALSE)
                    .add("includeUpper", JsonValue.TRUE))
                .build();
        QueryData q = new QueryData(new StringReader(json.toString()), queryConverter);
        NumericRangeQuery<Long> query = NumericRangeQuery.newLongRange("field", 1L, 5L, false, true);
        assertEquals(query, q.query);
    }

    @Test
    public void testDoubleRangeQuery() {
        JsonObject json = Json.createObjectBuilder()
                .add("query", Json.createObjectBuilder()
                    .add("type", "RangeQuery")
                    .add("rangeType", "Double")
                    .add("field", "field")
                    .add("lowerTerm", 1.0)
                    .add("upperTerm", 5.0)
                    .add("includeLower", JsonValue.FALSE)
                    .add("includeUpper", JsonValue.TRUE))
                .build();
        QueryData q = new QueryData(new StringReader(json.toString()), queryConverter);
        NumericRangeQuery<Double> query = NumericRangeQuery.newDoubleRange("field", 1.0, 5.0, false, true);
        assertEquals(query, q.query);
    }

    @Test
    public void testDrilldownQuery() {
        JsonObject json = Json.createObjectBuilder()
                .add("query", Json.createObjectBuilder()
                    .add("type", "TermQuery")
                    .add("term", Json.createObjectBuilder()
                        .add("field", "dd-field")
                        .add("path", Json.createArrayBuilder()
                            .add("value"))
                        .add("type", "DrillDown")))
                .build();
        QueryData q = new QueryData(new StringReader(json.toString()), queryConverter);
        TermQuery query = new TermQuery(DrillDownQuery.term("$facets", "dd-field", "value"));
        assertEquals(query, q.query);
    }

    @Test
    public void testFacets() {
        JsonObject json = Json.createObjectBuilder()
                .add("query", Json.createObjectBuilder()
                        .add("type", "MatchAllDocsQuery"))
                .add("facets", Json.createArrayBuilder()
                        .add(Json.createObjectBuilder()
                                .add("fieldname", "fieldname")
                                .add("path", Json.createArrayBuilder()
                                    .add("value1")
                                    .add("subvalue2"))
                                .add("maxTerms", 10)))
                .build();
        QueryData q = new QueryData(new StringReader(json.toString()), queryConverter);
        assertEquals(new MatchAllDocsQuery(), q.query);
        List<FacetRequest> facets = q.facets;
        assertEquals(1, facets.size());
        assertEquals("fieldname", facets.get(0).fieldname);
        assertEquals(10, facets.get(0).maxTerms);
        assertArrayEquals(new String[] {"value1", "subvalue2"}, facets.get(0).path);
    }

    @Test
    public void testSortKeys() {
        JsonObject json = Json.createObjectBuilder()
                .add("query", Json.createObjectBuilder()
                        .add("type", "MatchAllDocsQuery"))
                .add("sortKeys", Json.createArrayBuilder()
                        .add(Json.createObjectBuilder()
                                .add("sortBy", "fieldname")
                                .add("type", "String")
                                .add("sortDescending", false))
                        .add(Json.createObjectBuilder()
                                .add("sortBy", "score")
                                .add("sortDescending", true))
                        .add(Json.createObjectBuilder()
                                .add("sortBy", "intfield")
                                .add("type", "Int")
                                .add("sortDescending", true))
                        .add(Json.createObjectBuilder()
                                .add("sortBy", "fieldname")
                                .add("type", "String")
                                .add("missingValue", "STRING_FIRST")
                                .add("sortDescending", true))
                        .add(Json.createObjectBuilder()
                                .add("sortBy", "fieldname")
                                .add("type", "String")
                                .add("missingValue", "STRING_LAST")
                                .add("sortDescending", true))
                        .add(Json.createObjectBuilder()
                                .add("sortBy", "longfield")
                                .add("type", "Long")
                                .add("sortDescending", true))
                        .add(Json.createObjectBuilder()
                                .add("sortBy", "doublefield")
                                .add("type", "Double")
                                .add("sortDescending", true)))
                .build();
        QueryData q = new QueryData(new StringReader(json.toString()), queryConverter);
        assertEquals(new MatchAllDocsQuery(), q.query);
        SortField[] sortFields = q.sort.getSort();
        assertEquals(7, sortFields.length);
        assertEquals("fieldname", sortFields[0].getField());
        assertEquals(SortField.Type.STRING, sortFields[0].getType());
        assertEquals(false, sortFields[0].getReverse());
        assertEquals(null, sortFields[0].missingValue);

        assertEquals(null, sortFields[1].getField());
        assertEquals(SortField.Type.SCORE, sortFields[1].getType());
        assertEquals(true, sortFields[1].getReverse());
        assertEquals(null, sortFields[1].missingValue);

        assertEquals("intfield", sortFields[2].getField());
        assertEquals(SortField.Type.INT, sortFields[2].getType());
        assertEquals(true, sortFields[2].getReverse());
        assertEquals(null, sortFields[2].missingValue);

        assertEquals("fieldname", sortFields[3].getField());
        assertEquals(SortField.Type.STRING, sortFields[3].getType());
        assertEquals(true, sortFields[3].getReverse());
        assertEquals(SortField.STRING_FIRST, sortFields[3].missingValue);

        assertEquals("fieldname", sortFields[4].getField());
        assertEquals(SortField.Type.STRING, sortFields[4].getType());
        assertEquals(true, sortFields[4].getReverse());
        assertEquals(SortField.STRING_LAST, sortFields[4].missingValue);

        assertEquals("longfield", sortFields[5].getField());
        assertEquals(SortField.Type.LONG, sortFields[5].getType());
        assertEquals(true, sortFields[5].getReverse());
        assertEquals(null, sortFields[5].missingValue);

        assertEquals("doublefield", sortFields[6].getField());
        assertEquals(SortField.Type.DOUBLE, sortFields[6].getType());
        assertEquals(true, sortFields[6].getReverse());
        assertEquals(null, sortFields[6].missingValue);
    }

    @Test
    public void testSuggestionRequest() {
        JsonObject json = Json.createObjectBuilder()
                .add("query", Json.createObjectBuilder()
                    .add("type", "MatchAllDocsQuery"))
                .add("suggestionRequest", Json.createObjectBuilder()
                    .add("field", "field1")
                    .add("count", 2)
                    .add("suggests", Json.createArrayBuilder()
                        .add("valeu")))
                .build();
        QueryData q = new QueryData(new StringReader(json.toString()), queryConverter);
        assertEquals("field1", q.suggestionRequest.field);
        assertEquals(2, q.suggestionRequest.count);
        assertArrayEquals(new String[] {"valeu"}, q.suggestionRequest.suggests.toArray(new String[0]));
    }

    @Test
    public void testDedup() {
        JsonObject json = Json.createObjectBuilder()
                .add("query", Json.createObjectBuilder()
                    .add("type", "MatchAllDocsQuery"))
                .add("dedupField", "__key__")
                .add("dedupSortField", "__key__.date")
                .build();
        QueryData q = new QueryData(new StringReader(json.toString()), queryConverter);
        assertEquals("__key__", q.dedupField);
        assertEquals("__key__.date", q.dedupSortField);
    }
}
