/* begin license *
 *
 * "Meresco Lucene" is a set of components and tools to integrate Lucene (based on PyLucene) into Meresco
 *
 * Copyright (C) 2015 Koninklijke Bibliotheek (KB) http://www.kb.nl
 * Copyright (C) 2015 Seecr (Seek You Too B.V.) http://seecr.nl
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

import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import javax.json.Json;
import javax.json.JsonArrayBuilder;
import javax.json.JsonObject;
import javax.json.JsonObjectBuilder;
import javax.xml.ws.Response;

import org.apache.lucene.facet.LabelAndValue;
import org.apache.lucene.search.spell.SuggestWord;
import org.meresco.lucene.LuceneResponse.Hit;

public class LuceneResponse {
    public int total;
    public int totalWithDuplicates;
    public List<Hit> hits = new ArrayList<>();
    public List<DrilldownData> drilldownData = new ArrayList<>();
    public long queryTime = 0;
    public Map<String,SuggestWord[]> suggestions = new HashMap<>();
    public Map<String, Long> times = new HashMap<>();

    public LuceneResponse(int totalHits) {
        total = totalHits;
    }

    public void addHit(Hit hit) {
        hits.add(hit);
    }

    public static class Hit {
        public String id;
        public float score;
        public String duplicateField;
        public int duplicateCount;
        public List<String> duplicates;
        public String groupingField;

        public Hit(String id, float score) {
            this.id = id;
            this.score = score;
        }

        public Hit() {}
    }

    public static class DrilldownData {
        public String fieldname;
        public String[] path = new String[0];
        public List<Term> terms;

        public DrilldownData(String fieldname) {
            this.fieldname = fieldname;
        }
        
        public boolean equals(Object object) {
            if(object instanceof DrilldownData){
                DrilldownData ddObject = (DrilldownData) object;
                return ddObject.fieldname.equals(fieldname) && Arrays.equals(ddObject.path, path) && ddObject.terms.equals(terms);
            } else {
                return false;
            }
        }
        
        public static class Term {
            public final String label;
            public final int count;
            public List<Term> subTerms;
            
            public Term(String label, int count) {
                this.label = label;
                this.count = count;
            }
        
            public boolean equals(Object object) {
                if(object instanceof Term){
                    Term term = (Term) object;
                    return term.label.equals(label) && term.count == count && ((term.subTerms == null && subTerms == null) || term.subTerms.equals(subTerms));
                } else {
                    return false;
                }
            }
        }
    }

    public JsonObject toJson() {
        JsonObjectBuilder jsonBuilder = Json.createObjectBuilder()
                .add("total", total)
                .add("queryTime", queryTime);

        JsonArrayBuilder hitsArray = Json.createArrayBuilder();
        for (Hit hit : hits) {
            JsonObjectBuilder hitBuilder = Json.createObjectBuilder()
                    .add("id", hit.id)
                    .add("score", hit.score);
            if (hit.duplicateField != null) {
                hitBuilder.add("duplicateCount", Json.createObjectBuilder()
                    .add(hit.duplicateField, hit.duplicateCount));
            }
            if (hit.groupingField != null) {
                JsonArrayBuilder duplicatesBuilder = Json.createArrayBuilder();
                for (String id : hit.duplicates)
                    duplicatesBuilder.add(Json.createObjectBuilder().add("id", id));
                hitBuilder.add("duplicates", Json.createObjectBuilder()
                    .add(hit.groupingField, duplicatesBuilder));
            }
            hitsArray.add(hitBuilder);
        }
        jsonBuilder.add("hits", hitsArray);

        if (drilldownData.size() > 0) {
            JsonArrayBuilder ddArray = Json.createArrayBuilder();
            for (DrilldownData dd : drilldownData) {
                JsonArrayBuilder path = Json.createArrayBuilder();
                for (String p : dd.path)
                    path.add(p);
                ddArray.add(Json.createObjectBuilder()
                        .add("fieldname", dd.fieldname)
                        .add("path", path)
                        .add("terms", jsonTermList(dd.terms)));
            }
            jsonBuilder.add("drilldownData", ddArray);
        }
        
        if (times.size() > 0) {
            JsonObjectBuilder timesDict = Json.createObjectBuilder();
            for (String name : times.keySet())
                timesDict.add(name, times.get(name));
            jsonBuilder.add("times", timesDict);
        }
        if (suggestions.size() > 0) {
            JsonObjectBuilder suggestionsDict = Json.createObjectBuilder();
            for (String suggest : suggestions.keySet()) {
                JsonArrayBuilder suggestionArray = Json.createArrayBuilder();
                for (SuggestWord suggestion : suggestions.get(suggest)) {
                    suggestionArray.add(suggestion.string);
                }
                suggestionsDict.add(suggest, suggestionArray);
            }
            jsonBuilder.add("suggestions", suggestionsDict);
        }
        return jsonBuilder.build();
    }

    private JsonArrayBuilder jsonTermList(List<DrilldownData.Term> terms) {
        JsonArrayBuilder termArray = Json.createArrayBuilder();
        for (DrilldownData.Term term : terms) {
            JsonObjectBuilder termDict = Json.createObjectBuilder()
                    .add("term", term.label)
                    .add("count", term.count);
            if (term.subTerms != null)
                termDict.add("subterms", jsonTermList(term.subTerms));
            termArray.add(termDict);
        }
        return termArray;
    }
}