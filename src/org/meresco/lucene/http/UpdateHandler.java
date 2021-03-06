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

package org.meresco.lucene.http;

import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import org.apache.lucene.document.Document;
import org.eclipse.jetty.server.Request;
import org.meresco.lucene.DocumentStringToDocument;
import org.meresco.lucene.Lucene;
import org.meresco.lucene.OutOfMemoryShutdown;
import org.meresco.lucene.numerate.TermNumerator;

public class UpdateHandler extends AbstractMerescoLuceneHandler {
    private Lucene lucene;
    private TermNumerator termNumerator;

    public UpdateHandler(Lucene lucene, TermNumerator termNumerator, OutOfMemoryShutdown shutdown) {
        super(shutdown);
        this.lucene = lucene;
        this.termNumerator = termNumerator;
    }

    @Override
    public void doHandle(String target, Request baseRequest, HttpServletRequest request, HttpServletResponse response) throws Exception {
        request.setCharacterEncoding("UTF-8");
        response.setCharacterEncoding("UTF-8");
        Document document = new DocumentStringToDocument(request.getReader(), termNumerator).convert();
        if (request.getParameterMap().containsKey("identifier"))
            this.lucene.addDocument(request.getParameter("identifier"), document);
        else
            this.lucene.addDocument(document);
        response.setStatus(HttpServletResponse.SC_OK);
    }
}
