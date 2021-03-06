/* begin license *
 *
 * "Meresco Lucene" is a set of components and tools to integrate Lucene (based on PyLucene) into Meresco
 *
 * Copyright (C) 2014 Seecr (Seek You Too B.V.) http://seecr.nl
 * Copyright (C) 2014 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
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

package org.meresco.lucene.search;

import java.io.IOException;

import org.apache.lucene.search.Sort;
import org.apache.lucene.search.TopFieldCollector;

public class TopFieldSuperCollector extends TopDocSuperCollector {

    final boolean trackDocScores;
    final boolean trackMaxScore;
    final boolean docsScoredInOrder;

    public TopFieldSuperCollector(Sort sort, int numHits, boolean trackDocScores, boolean trackMaxScore,
            boolean docsScoredInOrder) {
        super(sort, numHits);
        this.trackDocScores = trackDocScores;
        this.trackMaxScore = trackMaxScore;
        this.docsScoredInOrder = docsScoredInOrder;
    }

    @Override
    protected TopDocSubCollector<TopFieldSuperCollector> createSubCollector() throws IOException {
        return new TopDocSubCollector<TopFieldSuperCollector>(TopFieldCollector.create(this.sort,
                this.numHits, /*fillFields*/ true, this.trackDocScores, this.trackMaxScore, this.docsScoredInOrder), this);
    }

    @Override
    public void complete() {
    }

}
