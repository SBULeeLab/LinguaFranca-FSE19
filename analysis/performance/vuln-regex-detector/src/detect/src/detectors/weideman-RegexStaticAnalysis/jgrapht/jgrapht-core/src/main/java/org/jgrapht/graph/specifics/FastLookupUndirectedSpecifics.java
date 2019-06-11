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
 * FastLookupUndirectedSpecifics.java
 * -----------------
 * (C) Copyright 2015-2015, by Joris Kinable and Contributors.
 *
 * Original Author:  Joris Kinable
 * Contributor(s):
 *
 * $Id$
 *
 * Changes
 * -------
 */
package org.jgrapht.graph.specifics;

import org.jgrapht.Graph;
import org.jgrapht.graph.AbstractBaseGraph;
import org.jgrapht.util.ArrayUnenforcedSet;
import org.jgrapht.util.UnorderedVertexPair;
import org.jgrapht.util.VertexPair;

import java.io.Serializable;
import java.util.*;

/**
 * Fast implementation of UndirectedSpecifics. This class uses additional data structures to improve the performance of methods which depend
 * on edge retrievals, e.g. getEdge(V u, V v), containsEdge(V u, V v),addEdge(V u, V v). A disadvantage is an increase in memory consumption.
 * If memory utilization is an issue, use a {@link DirectedSpecifics} instead.
 *
 * @author Joris Kinable
 */
public class FastLookupUndirectedSpecifics<V,E>
    extends UndirectedSpecifics<V,E>
    implements Serializable
{
    private static final long serialVersionUID = 225772727571597846L;

    /* Maps a pair of vertices <u,v> to a set of edges {(u,v)}. In case of a multigraph, all edges which touch both u,v are included in the set */
    protected Map<VertexPair<V>, ArrayUnenforcedSet<E>> touchingVerticesToEdgeMap;

    public FastLookupUndirectedSpecifics(AbstractBaseGraph<V, E> abstractBaseGraph)
    {
        this(abstractBaseGraph, new LinkedHashMap<>());
    }

    public FastLookupUndirectedSpecifics(AbstractBaseGraph<V, E> abstractBaseGraph, Map<V, UndirectedEdgeContainer<V, E>> vertexMap)
    {
        super(abstractBaseGraph, vertexMap);
        this.touchingVerticesToEdgeMap=new HashMap<>();
    }

    /**
     * @see Graph#getAllEdges(Object, Object)
     */
    @Override public Set<E> getAllEdges(V sourceVertex, V targetVertex)
    {
        if (abstractBaseGraph.containsVertex(sourceVertex)&& abstractBaseGraph.containsVertex(targetVertex)) {
            Set<E> edges = touchingVerticesToEdgeMap.get(new UnorderedVertexPair<>(sourceVertex, targetVertex));
            return edges == null ? Collections.emptySet() : new ArrayUnenforcedSet<>(edges);
        }else{
            return null;
        }
    }

    /**
     * @see Graph#getEdge(Object, Object)
     */
    @Override public E getEdge(V sourceVertex, V targetVertex)
    {
        List<E> edges = touchingVerticesToEdgeMap.get(new UnorderedVertexPair<>(sourceVertex, targetVertex));
        if(edges==null || edges.isEmpty())
            return null;
        else
            return edges.get(0);
    }

    @Override public void addEdgeToTouchingVertices(E e)
    {
        V source = abstractBaseGraph.getEdgeSource(e);
        V target = abstractBaseGraph.getEdgeTarget(e);

        getEdgeContainer(source).addEdge(e);


        //Add edge to touchingVerticesToEdgeMap for the UnorderedPair {u,v}
        VertexPair<V> vertexPair=new UnorderedVertexPair<>(source, target);
        if(!touchingVerticesToEdgeMap.containsKey(vertexPair)) {
            ArrayUnenforcedSet<E> edgeSet=new ArrayUnenforcedSet<>();
            edgeSet.add(e);
            touchingVerticesToEdgeMap.put(vertexPair, edgeSet);
        }else
            touchingVerticesToEdgeMap.get(vertexPair).add(e);

        if (!source.equals(target)) { //If not a self loop
            getEdgeContainer(target).addEdge(e);
        }
    }

    @Override public void removeEdgeFromTouchingVertices(E e)
    {
        V source = abstractBaseGraph.getEdgeSource(e);
        V target = abstractBaseGraph.getEdgeTarget(e);

        getEdgeContainer(source).removeEdge(e);

        if (!source.equals(target))
            getEdgeContainer(target).removeEdge(e);

        //Remove the edge from the touchingVerticesToEdgeMap. If there are no more remaining edges for a pair
        //of touching vertices, remove the pair from the map.
        VertexPair<V> vertexPair=new UnorderedVertexPair<>(source, target);
        if(touchingVerticesToEdgeMap.containsKey(vertexPair)){
            ArrayUnenforcedSet<E> edgeSet=touchingVerticesToEdgeMap.get(vertexPair);
            edgeSet.remove(e);
            if(edgeSet.isEmpty())
                touchingVerticesToEdgeMap.remove(vertexPair);
        }
    }

}
