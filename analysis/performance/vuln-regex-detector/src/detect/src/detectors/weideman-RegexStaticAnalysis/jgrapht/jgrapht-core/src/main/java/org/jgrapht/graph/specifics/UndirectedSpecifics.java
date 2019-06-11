/* ==========================================
 * JGraphT : a free Java graph-theory library
 * ==========================================
 *
 * Project Info:  http://jgrapht.sourceforge.net/
 * Project Creator:  Barak Naveh (http://sourceforge.net/users/barak_naveh)
 *
 * (C) Copyright 2003-2008, by Barak Naveh and Contributors.
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
/* -----------------
 * UndirectedSpecifics.java
 * -----------------
 * (C) Copyright 2015-2015, by Barak Naveh and Contributors.
 *
 * Original Author:  Barak Naveh
 * Contributor(s): Joris Kinable
 *
 * $Id$
 *
 * Changes
 * -------
 */
package org.jgrapht.graph.specifics;

import org.jgrapht.DirectedGraph;
import org.jgrapht.Graph;
import org.jgrapht.graph.AbstractBaseGraph;
import org.jgrapht.graph.EdgeSetFactory;
import org.jgrapht.util.ArrayUnenforcedSet;

import java.io.Serializable;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Set;

/**
 * Plain implementation of UndirectedSpecifics. This implementation requires the least amount of memory, at the expense of
 * slow edge retrievals. Methods which depend on edge retrievals, e.g. getEdge(V u, V v), containsEdge(V u, V v),
 * addEdge(V u, V v), etc may be relatively slow when the average degree of a vertex is high (dense graphs). For a fast
 * implementation, use {@link FastLookupUndirectedSpecifics}.
 *
 * @author Barak Naveh
 * @author Joris Kinable
 */
public class UndirectedSpecifics<V,E>
    extends Specifics<V,E>
    implements Serializable
{
    private static final long serialVersionUID = 6494588405178655873L;
    private static final String NOT_IN_UNDIRECTED_GRAPH =
        "no such operation in an undirected graph";

    protected AbstractBaseGraph<V,E> abstractBaseGraph;
    protected Map<V, UndirectedEdgeContainer<V, E>> vertexMapUndirected;
    protected EdgeSetFactory<V, E> edgeSetFactory;

    public UndirectedSpecifics(AbstractBaseGraph<V,E> abstractBaseGraph)
    {
        this(abstractBaseGraph, new LinkedHashMap<>());
    }

    public UndirectedSpecifics(AbstractBaseGraph<V,E> abstractBaseGraph,
                               Map<V, UndirectedEdgeContainer<V, E>> vertexMap)
    {
        this.abstractBaseGraph = abstractBaseGraph;
        this.vertexMapUndirected = vertexMap;
        this.edgeSetFactory=abstractBaseGraph.getEdgeSetFactory();
    }

    @Override public void addVertex(V v)
    {
        // add with a lazy edge container entry
        vertexMapUndirected.put(v, null);
    }

    @Override public Set<V> getVertexSet()
    {
        return vertexMapUndirected.keySet();
    }

    /**
     * @see Graph#getAllEdges(Object, Object)
     */
    @Override public Set<E> getAllEdges(V sourceVertex, V targetVertex)
    {
        Set<E> edges = null;

        if (abstractBaseGraph.containsVertex(sourceVertex)
            && abstractBaseGraph.containsVertex(targetVertex))
        {
            edges = new ArrayUnenforcedSet<>();

            for (E e : getEdgeContainer(sourceVertex).vertexEdges) {
                boolean equal =
                        isEqualsStraightOrInverted(
                                sourceVertex,
                                targetVertex,
                                e);

                if (equal) {
                    edges.add(e);
                }
            }
        }

        return edges;
    }

    /**
     * @see Graph#getEdge(Object, Object)
     */
    @Override public E getEdge(V sourceVertex, V targetVertex)
    {
        if (abstractBaseGraph.containsVertex(sourceVertex)
            && abstractBaseGraph.containsVertex(targetVertex))
        {

            for (E e : getEdgeContainer(sourceVertex).vertexEdges) {
                boolean equal =
                        isEqualsStraightOrInverted(
                                sourceVertex,
                                targetVertex,
                                e);

                if (equal) {
                    return e;
                }
            }
        }

        return null;
    }

    private boolean isEqualsStraightOrInverted(
        Object sourceVertex,
        Object targetVertex,
        E e)
    {
        boolean equalStraight =
            sourceVertex.equals(abstractBaseGraph.getEdgeSource(e))
            && targetVertex.equals(abstractBaseGraph.getEdgeTarget(e));

        boolean equalInverted =
            sourceVertex.equals(abstractBaseGraph.getEdgeTarget(e))
            && targetVertex.equals(abstractBaseGraph.getEdgeSource(e));
        return equalStraight || equalInverted;
    }

    @Override public void addEdgeToTouchingVertices(E e)
    {
        V source = abstractBaseGraph.getEdgeSource(e);
        V target = abstractBaseGraph.getEdgeTarget(e);

        getEdgeContainer(source).addEdge(e);

        if (!source.equals(target)) {
            getEdgeContainer(target).addEdge(e);
        }
    }

    @Override public int degreeOf(V vertex)
    {
        if (abstractBaseGraph.isAllowingLoops()) { // then we must count, and add loops twice

            int degree = 0;
            Set<E> edges = getEdgeContainer(vertex).vertexEdges;

            for (E e : edges) {
                if (abstractBaseGraph.getEdgeSource(e).equals(abstractBaseGraph.getEdgeTarget(e))) {
                    degree += 2;
                } else {
                    degree += 1;
                }
            }

            return degree;
        } else {
            return getEdgeContainer(vertex).edgeCount();
        }
    }

    /**
     * @see Graph#edgesOf(Object)
     */
    @Override public Set<E> edgesOf(V vertex)
    {
        return getEdgeContainer(vertex).getUnmodifiableVertexEdges();
    }

    /**
     * @see DirectedGraph#inDegreeOf(Object)
     */
    @Override public int inDegreeOf(V vertex)
    {
        throw new UnsupportedOperationException(NOT_IN_UNDIRECTED_GRAPH);
    }

    /**
     * @see DirectedGraph#incomingEdgesOf(Object)
     */
    @Override public Set<E> incomingEdgesOf(V vertex)
    {
        throw new UnsupportedOperationException(NOT_IN_UNDIRECTED_GRAPH);
    }

    /**
     * @see DirectedGraph#outDegreeOf(Object)
     */
    @Override public int outDegreeOf(V vertex)
    {
        throw new UnsupportedOperationException(NOT_IN_UNDIRECTED_GRAPH);
    }

    /**
     * @see DirectedGraph#outgoingEdgesOf(Object)
     */
    @Override public Set<E> outgoingEdgesOf(V vertex)
    {
        throw new UnsupportedOperationException(NOT_IN_UNDIRECTED_GRAPH);
    }

    @Override public void removeEdgeFromTouchingVertices(E e)
    {
        V source = abstractBaseGraph.getEdgeSource(e);
        V target = abstractBaseGraph.getEdgeTarget(e);

        getEdgeContainer(source).removeEdge(e);

        if (!source.equals(target)) {
            getEdgeContainer(target).removeEdge(e);
        }
    }

    /**
     * A lazy build of edge container for specified vertex.
     *
     * @param vertex a vertex in this graph.
     *
     * @return EdgeContainer
     */
    protected UndirectedEdgeContainer<V, E> getEdgeContainer(V vertex)
    {
        //abstractBaseGraph.assertVertexExist(vertex); //JK: I don't think we need this here. This should have been verified upstream

        UndirectedEdgeContainer<V, E> ec = vertexMapUndirected.get(vertex);

        if (ec == null) {
            ec = new UndirectedEdgeContainer<>(
                    edgeSetFactory,
                    vertex);
            vertexMapUndirected.put(vertex, ec);
        }

        return ec;
    }
}
