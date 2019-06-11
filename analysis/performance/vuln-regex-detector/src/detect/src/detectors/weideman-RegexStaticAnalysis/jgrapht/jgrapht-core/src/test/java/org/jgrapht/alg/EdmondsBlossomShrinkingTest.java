/* ==========================================
 * JGraphT : a free Java graph-theory library
 * ==========================================
 *
 * Project Info:  http://jgrapht.sourceforge.net/
 * Project Creator:  Barak Naveh (http://sourceforge.net/users/barak_naveh)
 *
 * (C) Copyright 2003-2012, by Barak Naveh and Contributors.
 *
 * This program and the accompanying materials are dual-licensed under
 * either
 *
 * (a) the terms of the GNU Lesser General Public License version 2.1
 * as published by the Free Software Foundation, or (at your option) any
 * later version.
 *
 * or (per the licensee's choosing)
 *
 * (b) the terms of the Eclipse Public License v1.0 as published by
 * the Eclipse Foundation.
 */
/* -------------------------
 * EdmondsBlossomShrinkingTest.java
 * -------------------------
 * (C) Copyright 2012-2012, by Alejandro Ramon Lopez del Huerto and Contributors.
 *
 * Original Author:  Alejandro Ramon Lopez del Huerto
 * Contributor(s):
 *
 * Changes
 * -------
 * 24-Jan-2012 : Initial revision (ARLH);
 *
 */
package org.jgrapht.alg;

import junit.framework.TestCase;
import org.jgrapht.UndirectedGraph;
import org.jgrapht.graph.DefaultEdge;
import org.jgrapht.graph.SimpleGraph;

import java.util.Set;

/**
 * .
 *
 * @author Alejandro R. Lopez del Huerto
 * @since Jan 24, 2012
 */
public final class EdmondsBlossomShrinkingTest extends TestCase
{
    public void testOne()
    {
        // create an undirected graph
        UndirectedGraph<Integer, DefaultEdge> g =
                new SimpleGraph<>(DefaultEdge.class);

        Integer v1 = 1;
        Integer v2 = 2;
        Integer v3 = 3;
        Integer v4 = 4;

        g.addVertex(v1);
        g.addVertex(v2);
        g.addVertex(v3);
        g.addVertex(v4);

        DefaultEdge e12 = g.addEdge(v1, v2);
        DefaultEdge e34 = g.addEdge(v3, v4);

        // compute max match
        EdmondsBlossomShrinking<Integer, DefaultEdge> matcher =
                new EdmondsBlossomShrinking<>(g);
        Set<DefaultEdge> match = matcher.getMatching();
        assertEquals(2, match.size());
        assertTrue(match.contains(e12));
        assertTrue(match.contains(e34));
    }

    public void testCrash()
    {
        UndirectedGraph<Integer, DefaultEdge> g =
                new SimpleGraph<>(DefaultEdge.class);

        Integer v1 = 1;
        Integer v2 = 2;
        Integer v3 = 3;
        Integer v4 = 4;
        Integer v5 = 5;

        g.addVertex(v1);
        g.addVertex(v2);
        g.addVertex(v3);
        g.addVertex(v4);
        g.addVertex(v5);

        DefaultEdge e12 = g.addEdge(v1, v2);
        DefaultEdge e34 = g.addEdge(v3, v4);

        EdmondsBlossomShrinking<Integer, DefaultEdge> matcher =
                new EdmondsBlossomShrinking<>(g);

        Set<DefaultEdge> match = matcher.getMatching();

        assertEquals(2, match.size());

        assertTrue(match.contains(e12));
        assertTrue(match.contains(e34));
    }


    public void testCrash2()
    {
        UndirectedGraph<Integer, DefaultEdge> g =
                new SimpleGraph<>(DefaultEdge.class);

        Integer vs[] = new Integer[] { 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13 };

        for (int i = 1; i < 14; ++i) {
            g.addVertex(vs[i]);
        }

        DefaultEdge e12 = g.addEdge(vs[1], vs[2]);
        DefaultEdge e34 = g.addEdge(vs[3], vs[4]);
        DefaultEdge e56 = g.addEdge(vs[5], vs[6]);
        DefaultEdge e78 = g.addEdge(vs[7], vs[8]);
        DefaultEdge e910 = g.addEdge(vs[9], vs[10]);
        DefaultEdge e1112 = g.addEdge(vs[11], vs[12]);

        EdmondsBlossomShrinking<Integer, DefaultEdge> matcher =
                new EdmondsBlossomShrinking<>(g);

        Set<DefaultEdge> match = matcher.getMatching();

        assertEquals(6, match.size());

        assertTrue(match.contains(e12));
        assertTrue(match.contains(e34));
        assertTrue(match.contains(e56));
        assertTrue(match.contains(e78));
        assertTrue(match.contains(e910));
        assertTrue(match.contains(e1112));
    }
}
