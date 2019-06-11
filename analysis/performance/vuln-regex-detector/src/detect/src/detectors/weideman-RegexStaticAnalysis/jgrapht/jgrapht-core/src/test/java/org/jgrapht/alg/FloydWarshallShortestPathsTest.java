/* ==========================================
 * JGraphT : a free Java graph-theory library
 * ==========================================
 *
 * Project Info:  http://jgrapht.sourceforge.net/
 * Project Creator:  Barak Naveh (http://sourceforge.net/users/barak_naveh)
 *
 * (C) Copyright 2003-2009, by Barak Naveh and Contributors.
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
 * FloydWarshallShortestPathsTest.java
 * -------------------------
 * (C) Copyright 2009-2009, by Tom Larkworthy and Contributors
 *
 * Original Author:  Tom Larkworthy
 * Contributors:  Andrea Pagani
 *
 * $Id: FloydWarshallShortestPathsTest.java 715 2010-06-13 01:25:00Z perfecthash $
 *
 * Changes
 * -------
 * 29-Jun-2009 : Initial revision (TL);
 *
 */
package org.jgrapht.alg;

import java.util.*;

import junit.framework.*;

import org.jgrapht.*;
import org.jgrapht.generate.*;
import org.jgrapht.graph.*;


/**
 * @author Tom Larkworthy
 * @version $Id: FloydWarshallShortestPathsTest.java 715 2010-06-13 01:25:00Z perfecthash $
 */
public class FloydWarshallShortestPathsTest
    extends TestCase
{
    //~ Methods ----------------------------------------------------------------

    public void testCompareWithDijkstra()
    {
        RandomGraphGenerator<Integer, DefaultWeightedEdge> gen =
                new RandomGraphGenerator<>(
                        10,
                        15);
        VertexFactory<Integer> f =
            new VertexFactory<Integer>() {
                int gid;

                @Override
                public Integer createVertex()
                {
                    return gid++;
                }
            };

        for (int i = 0; i < 10; i++) {
            //Generate directed graph
            SimpleDirectedGraph<Integer, DefaultWeightedEdge> directed = new SimpleDirectedGraph<>(DefaultWeightedEdge.class);
            gen.generateGraph(directed, f, new HashMap<>());

            // setup our shortest path measurer
            FloydWarshallShortestPaths<Integer, DefaultWeightedEdge> fw = new FloydWarshallShortestPaths<>(directed);

            for (Integer v1 : directed.vertexSet()) {
                for (Integer v2 : directed.vertexSet()) {
                    double fwSp = fw.shortestDistance(v1, v2);
                    double dijSp =
                            new DijkstraShortestPath<>(
                                    directed,
                                    v1,
                                    v2).getPathLength();
                    assertTrue( (Math.abs(dijSp - fwSp) < .01) || (Double.isInfinite(fwSp) && Double.isInfinite(dijSp)));
                    GraphPath<Integer, DefaultWeightedEdge> path=fw.getShortestPath(v1, v2);
                    if(path != null)
                        this.verifyPath(directed, path, fw.shortestDistance(v1, v2));
                }
            }

            //Generate Undirected graph
            SimpleGraph<Integer, DefaultWeightedEdge> undirected = new SimpleGraph<>(DefaultWeightedEdge.class);
            gen.generateGraph(undirected, f, new HashMap<>());

            // setup our shortest path measurer
            fw = new FloydWarshallShortestPaths<>(
                    undirected);

            for (Integer v1 : undirected.vertexSet()) {
                for (Integer v2 : undirected.vertexSet()) {
                    double fwSp = fw.shortestDistance(v1, v2);
                    double dijSp =
                            new DijkstraShortestPath<>(
                                    undirected,
                                    v1,
                                    v2).getPathLength();
                    assertTrue((Math.abs(dijSp - fwSp) < .01) || (Double.isInfinite(fwSp) && Double.isInfinite(dijSp)));
                    GraphPath<Integer, DefaultWeightedEdge> path=fw.getShortestPath(v1, v2);
                    if(path != null)
                        this.verifyPath(undirected, path, fw.shortestDistance(v1, v2));
                }
            }
        }
    }

    /**
     * Verify whether the path calculated by FloydWarshallShortestPaths is an actual valid path.
     */
    private <V,E> void verifyPath(Graph<V,E> graph, GraphPath<V,E> path, double pathCost){
        assertEquals(pathCost, path.getWeight(), .00000001);
        double verifiedEdgeCost=0;
        for (E e : path.getEdgeList()) {
            assertNotNull(e);
            verifiedEdgeCost+=graph.getEdgeWeight(e);
        }
        assertEquals(pathCost, verifiedEdgeCost, .00000001);
        try{
            Graphs.getPathVertexList(path);
        }catch (IllegalArgumentException e){
            fail("Invalid path encountered: the sequence of edges does not present a valid path through the graph");
        }
    }

    private static UndirectedGraph<String, DefaultEdge> createStringGraph()
    {
        UndirectedGraph<String, DefaultEdge> g =
                new SimpleGraph<>(DefaultEdge.class);

        String v1 = "v1";
        String v2 = "v2";
        String v3 = "v3";
        String v4 = "v4";

        // add the vertices
        g.addVertex(v1);
        g.addVertex(v2);
        g.addVertex(v3);
        g.addVertex(v4);

        // add edges to create a circuit
        g.addEdge(v1, v2);
        g.addEdge(v2, v3);
        g.addEdge(v3, v1);
        g.addEdge(v3, v4);

        return g;
    }

    public void testDiameter()
    {
        UndirectedGraph<String, DefaultEdge> stringGraph = createStringGraph();
        FloydWarshallShortestPaths<String, DefaultEdge> testFWPath =
                new FloydWarshallShortestPaths<>(stringGraph);
        double diameter = testFWPath.getDiameter();
        assertEquals(2.0, diameter);
    }

    public void testEmptyDiameter() {
        DirectedGraph<String, DefaultEdge> graph =
                new DefaultDirectedGraph<>(DefaultEdge.class);
        FloydWarshallShortestPaths<String, DefaultEdge> fw =
                new FloydWarshallShortestPaths<>(graph);
        double diameter = fw.getDiameter();
        assertEquals(0.0, diameter);
    }

    public void testEdgeLessDiameter() {
        DirectedGraph<String, DefaultEdge> graph =
                new DefaultDirectedGraph<>(DefaultEdge.class);
        String a = "a", b = "b";
        graph.addVertex(a);
        graph.addVertex(b);
        FloydWarshallShortestPaths<String, DefaultEdge> fw =
                new FloydWarshallShortestPaths<>(graph);
        double diameter = fw.getDiameter();
        assertEquals(0.0, diameter);
    }

    public void testWeightedEdges() {
    	SimpleDirectedGraph<String, DefaultWeightedEdge> weighted =
                new SimpleDirectedGraph<>(DefaultWeightedEdge.class);
    	weighted.addVertex("a");
    	weighted.addVertex("b");
        DefaultWeightedEdge edge=weighted.addEdge("a", "b");
    	weighted.setEdgeWeight(edge, 5.0);
    	FloydWarshallShortestPaths<String, DefaultWeightedEdge> fw = new FloydWarshallShortestPaths<>(weighted);
    	double sD = fw.shortestDistance("a", "b");
        assertEquals(5.0, sD, 0.1);
        GraphPath<String, DefaultWeightedEdge> path=fw.getShortestPath("a", "b");
        assertNotNull(path);
        assertEquals(Collections.singletonList(edge), path.getEdgeList());
        assertEquals("a", path.getStartVertex());
        assertEquals("b", path.getEndVertex());
        assertEquals(5.0, path.getWeight());
        assertEquals(weighted, path.getGraph());
        assertNull(fw.getShortestPath("b", "a"));
    }
}

// End FloydWarshallShortestPathsTest.java
