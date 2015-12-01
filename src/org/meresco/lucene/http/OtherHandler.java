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

package org.meresco.lucene.http;

import java.io.IOException;

import javax.json.Json;
import javax.json.JsonArrayBuilder;
import javax.servlet.ServletException;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import org.eclipse.jetty.server.Request;
import org.eclipse.jetty.server.handler.AbstractHandler;
import org.meresco.lucene.Lucene;

public class OtherHandler extends AbstractHandler {

    private Lucene lucene;

    public OtherHandler(Lucene lucene) {
        this.lucene = lucene;
    }

    @Override
    public void handle(String target, Request baseRequest, HttpServletRequest request, HttpServletResponse response) throws IOException, ServletException {
        try {
            String result = "";
            switch (target) {
                case "/numDocs/":
                    result = String.valueOf(lucene.numDocs());
                    break;
                case "/maxDoc/":
                    result = String.valueOf(lucene.maxDoc());
                    break;
                case "/fieldnames/":
                    JsonArrayBuilder builder = Json.createArrayBuilder();
                    for (String fieldname : lucene.fieldnames())
                        builder.add(fieldname);
                    result = builder.build().toString();
                    break;
                case "/drilldownFieldnames/":
                    String dim = request.getParameter("dim");
                    String[] path = request.getParameterValues("path");
                    if (path == null)
                        path = new String[0];
                    builder = Json.createArrayBuilder();
                    for (String fieldname : lucene.drilldownFieldnames(50, dim, path))
                        builder.add(fieldname);
                    result = builder.build().toString();
                    break;
            }
            response.getWriter().write(result);
        } catch (Exception e) {
            response.setStatus(HttpServletResponse.SC_INTERNAL_SERVER_ERROR);
            response.getWriter().write(Utils.getStackTrace(e));
            baseRequest.setHandled(true);
            return;
        }
        response.setStatus(HttpServletResponse.SC_OK);
        response.setContentType("application/json");
        baseRequest.setHandled(true);
    }
}