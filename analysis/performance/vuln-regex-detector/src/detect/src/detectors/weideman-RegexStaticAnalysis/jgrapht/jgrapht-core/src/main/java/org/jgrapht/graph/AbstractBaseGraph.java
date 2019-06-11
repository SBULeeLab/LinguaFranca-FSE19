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
/* ----------------------
 * AbstractBaseGraph.java
 * ----------------------
 * (C) Copyright 2003-2008, by Barak Naveh and Contributors.
 *
 * Original Author:  Barak Naveh
 * Contributor(s):   John V. Sichi
 *                   Christian Hammer
 *
 * $Id$
 *
 * Changes
 * -------
 * 24-Jul-2003 : Initial revision (BN);
 * 10-Aug-2003 : General edge refactoring (BN);
 * 06-Nov-2003 : Change edge sharing semantics (JVS);
 * 07-Feb-2004 : Enabled serialization (BN);
 * 11-Mar-2004 : Made generic (CH);
 * 01-Jun-2005 : Added EdgeListFactory (JVS);
 * 07-May-2006 : Changed from List<Edge> to Set<Edge> (JVS);
 * 28-May-2006 : Moved connectivity info from edge to graph (JVS);
 *
 */
package org.jgrapht.graph;

import java.io.*;

import java.util.*;

import org.jgrapht.*;
import org.jgrapht.graph.specifics.FastLookupDirectedSpecifics;
import org.jgrapht.graph.specifics.FastLookupUndirectedSpecifics;
import org.jgrapht.graph.specifics.Specifics;
import org.jgrapht.util.*;


/**
 * The most general implementation of the {@link org.jgrapht.Graph} interface.
 * Its subclasses add various restrictions to get more specific graphs. The
 * decision whether it is directed or undirected is decided at construction time
 * and cannot be later modified (see constructor for details).
 *
 * <p>This graph implementation guarantees deterministic vertex and edge set
 * ordering (via {@link LinkedHashMap} and {@link LinkedHashSet}).</p>
 *
 * @author Barak Naveh
 * @since Jul 24, 2003
 */
public abstract class AbstractBaseGraph<V, E>
    extends AbstractGraph<V, E>
    implements Graph<V, E>,
        Cloneable,
        Serializable
{
    private static final long serialVersionUID = -1263088497616142427L;

    private static final String LOOPS_NOT_ALLOWED = "loops not allowed";

    boolean allowingLoops;

    private EdgeFactory<V, E> edgeFactory;
    private EdgeSetFactory<V, E> edgeSetFactory;
    private Map<E, IntrusiveEdge> edgeMap;
    private transient Set<E> unmodifiableEdgeSet = null;
    private transient Set<V> unmodifiableVertexSet = null;
    private Specifics<V,E> specifics;
    private boolean allowingMultipleEdges;

    private transient TypeUtil<V> vertexTypeDecl = null;

    /**
     * Construct a new graph. The graph can either be directed or undirected,
     * depending on the specified edge factory.
     *
     * @param ef the edge factory of the new graph.
     * @param allowMultipleEdges whether to allow multiple edges or not.
     * @param allowLoops whether to allow edges that are self-loops or not.
     *
     * @throws NullPointerException if the specified edge factory is <code>
     * null</code>.
     */
    protected AbstractBaseGraph(
        EdgeFactory<V, E> ef,
        boolean allowMultipleEdges,
        boolean allowLoops)
    {
        if (ef == null) {
            throw new NullPointerException();
        }

        edgeMap = new LinkedHashMap<>();
        edgeFactory = ef;
        allowingLoops = allowLoops;
        allowingMultipleEdges = allowMultipleEdges;

        this.edgeSetFactory = new ArrayListFactory<>();
        specifics = createSpecifics();

    }

    /**
     * @see Graph#getAllEdges(Object, Object)
     */
    @Override public Set<E> getAllEdges(V sourceVertex, V targetVertex)
    {
        return specifics.getAllEdges(sourceVertex, targetVertex);
    }

    /**
     * Returns <code>true</code> if and only if self-loops are allowed in this
     * graph. A self loop is an edge that its source and target vertices are the
     * same.
     *
     * @return <code>true</code> if and only if graph loops are allowed.
     */
    public boolean isAllowingLoops()
    {
        return allowingLoops;
    }

    /**
     * Returns <code>true</code> if and only if multiple edges are allowed in
     * this graph. The meaning of multiple edges is that there can be many edges
     * going from vertex v1 to vertex v2.
     *
     * @return <code>true</code> if and only if multiple edges are allowed.
     */
    public boolean isAllowingMultipleEdges()
    {
        return allowingMultipleEdges;
    }

    /**
     * @see Graph#getEdge(Object, Object)
     */
    @Override public E getEdge(V sourceVertex, V targetVertex)
    {
        return specifics.getEdge(sourceVertex, targetVertex);
    }

    /**
     * @see Graph#getEdgeFactory()
     */
    @Override public EdgeFactory<V, E> getEdgeFactory()
    {
        return edgeFactory;
    }

    /**
     * Set the {@link EdgeSetFactory} to use for this graph. Initially, a graph
     * is created with a default implementation which always supplies an {@link
     * java.util.ArrayList} with capacity 1.
     *
     * @param edgeSetFactory factory to use for subsequently created edge sets
     * (this call has no effect on existing edge sets)
     */
    public void setEdgeSetFactory(EdgeSetFactory<V, E> edgeSetFactory)
    {
        this.edgeSetFactory = edgeSetFactory;
    }

    /**
     * Returns the {@link EdgeSetFactory} used by this graph. The default is {@link
     * java.util.ArrayList} with capacity 1.
     * @return edgeSetFactory used by this graph
     */
    public EdgeSetFactory<V,E> getEdgeSetFactory()
    {
        return edgeSetFactory;
    }

    /**
     * @see Graph#addEdge(Object, Object)
     */
    @Override public E addEdge(V sourceVertex, V targetVertex)
    {
        assertVertexExist(sourceVertex);
        assertVertexExist(targetVertex);

        if (!allowingMultipleEdges
            && containsEdge(sourceVertex, targetVertex))
        {
            return null;
        }

        if (!allowingLoops && sourceVertex.equals(targetVertex)) {
            throw new IllegalArgumentException(LOOPS_NOT_ALLOWED);
        }

        E e = edgeFactory.createEdge(sourceVertex, targetVertex);

        if (containsEdge(e)) { // this restriction should stay!

            return null;
        } else {
            IntrusiveEdge intrusiveEdge =
                createIntrusiveEdge(e, sourceVertex, targetVertex);

            edgeMap.put(e, intrusiveEdge);
            specifics.addEdgeToTouchingVertices(e);

            return e;
        }
    }

    /**
     * @see Graph#addEdge(Object, Object, Object)
     */
    @Override public boolean addEdge(V sourceVertex, V targetVertex, E e)
    {
        if (e == null) {
            throw new NullPointerException();
        } else if (containsEdge(e)) {
            return false;
        }

        assertVertexExist(sourceVertex);
        assertVertexExist(targetVertex);

        if (!allowingMultipleEdges
            && containsEdge(sourceVertex, targetVertex))
        {
            return false;
        }

        if (!allowingLoops && sourceVertex.equals(targetVertex)) {
            throw new IllegalArgumentException(LOOPS_NOT_ALLOWED);
        }

        IntrusiveEdge intrusiveEdge =
            createIntrusiveEdge(e, sourceVertex, targetVertex);

        edgeMap.put(e, intrusiveEdge);
        specifics.addEdgeToTouchingVertices(e);

        return true;
    }

    private IntrusiveEdge createIntrusiveEdge(
        E e,
        V sourceVertex,
        V targetVertex)
    {
        IntrusiveEdge intrusiveEdge;
        if (e instanceof IntrusiveEdge) {
            intrusiveEdge = (IntrusiveEdge) e;
        } else {
            intrusiveEdge = new IntrusiveEdge();
        }
        intrusiveEdge.source = sourceVertex;
        intrusiveEdge.target = targetVertex;
        return intrusiveEdge;
    }

    /**
     * @see Graph#addVertex(Object)
     */
    @Override public boolean addVertex(V v)
    {
        if (v == null) {
            throw new NullPointerException();
        } else if (containsVertex(v)) {
            return false;
        } else {
            specifics.addVertex(v);

            return true;
        }
    }

    /**
     * @see Graph#getEdgeSource(Object)
     */
    @Override public V getEdgeSource(E e)
    {
        return TypeUtil.uncheckedCast(
            getIntrusiveEdge(e).source,
            vertexTypeDecl);
    }

    /**
     * @see Graph#getEdgeTarget(Object)
     */
    @Override public V getEdgeTarget(E e)
    {
        return TypeUtil.uncheckedCast(
            getIntrusiveEdge(e).target,
            vertexTypeDecl);
    }

    private IntrusiveEdge getIntrusiveEdge(E e)
    {
        if (e instanceof IntrusiveEdge) {
            return (IntrusiveEdge) e;
        }

        return edgeMap.get(e);
    }

    /**
     * Returns a shallow copy of this graph instance. Neither edges nor vertices
     * are cloned.
     *
     * @return a shallow copy of this set.
     *
     * @throws RuntimeException
     *
     * @see java.lang.Object#clone()
     */
    @Override public Object clone()
    {
        try {
            AbstractBaseGraph<V, E> newGraph =
                TypeUtil.uncheckedCast(super.clone(), null);

            newGraph.edgeMap = new LinkedHashMap<>();

            newGraph.edgeFactory = this.edgeFactory;
            newGraph.unmodifiableEdgeSet = null;
            newGraph.unmodifiableVertexSet = null;

            // NOTE:  it's important for this to happen in an object
            // method so that the new inner class instance gets associated with
            // the right outer class instance
            newGraph.specifics = newGraph.createSpecifics();

            Graphs.addGraph(newGraph, this);

            return newGraph;
        } catch (CloneNotSupportedException e) {
            e.printStackTrace();
            throw new RuntimeException();
        }
    }

    /**
     * @see Graph#containsEdge(Object)
     */
    @Override public boolean containsEdge(E e)
    {
        return edgeMap.containsKey(e);
    }

    /**
     * @see Graph#containsVertex(Object)
     */
    @Override public boolean containsVertex(V v)
    {
        return specifics.getVertexSet().contains(v);
    }

    /**
     * @see UndirectedGraph#degreeOf(Object)
     */
    public int degreeOf(V vertex)
    {
        return specifics.degreeOf(vertex);
    }

    /**
     * @see Graph#edgeSet()
     */
    @Override public Set<E> edgeSet()
    {
        if (unmodifiableEdgeSet == null) {
            unmodifiableEdgeSet = Collections.unmodifiableSet(edgeMap.keySet());
        }

        return unmodifiableEdgeSet;
    }

    /**
     * @see Graph#edgesOf(Object)
     */
    @Override public Set<E> edgesOf(V vertex)
    {
        assertVertexExist(vertex);
        return specifics.edgesOf(vertex);
    }

    /**
     * @see DirectedGraph#inDegreeOf(Object)
     */
    public int inDegreeOf(V vertex)
    {
        assertVertexExist(vertex);
        return specifics.inDegreeOf(vertex);
    }

    /**
     * @see DirectedGraph#incomingEdgesOf(Object)
     */
    public Set<E> incomingEdgesOf(V vertex)
    {
        assertVertexExist(vertex);
        return specifics.incomingEdgesOf(vertex);
    }

    /**
     * @see DirectedGraph#outDegreeOf(Object)
     */
    public int outDegreeOf(V vertex)
    {
        assertVertexExist(vertex);
        return specifics.outDegreeOf(vertex);
    }

    /**
     * @see DirectedGraph#outgoingEdgesOf(Object)
     */
    public Set<E> outgoingEdgesOf(V vertex)
    {
        assertVertexExist(vertex);
        return specifics.outgoingEdgesOf(vertex);
    }

    /**
     * @see Graph#removeEdge(Object, Object)
     */
    @Override public E removeEdge(V sourceVertex, V targetVertex)
    {
        E e = getEdge(sourceVertex, targetVertex);

        if (e != null) {
            specifics.removeEdgeFromTouchingVertices(e);
            edgeMap.remove(e);
        }

        return e;
    }

    /**
     * @see Graph#removeEdge(Object)
     */
    @Override public boolean removeEdge(E e)
    {
        if (containsEdge(e)) {
            specifics.removeEdgeFromTouchingVertices(e);
            edgeMap.remove(e);

            return true;
        } else {
            return false;
        }
    }

    /**
     * @see Graph#removeVertex(Object)
     */
    @Override public boolean removeVertex(V v)
    {
        if (containsVertex(v)) {
            Set<E> touchingEdgesList = edgesOf(v);

            // cannot iterate over list - will cause
            // ConcurrentModificationException
            removeAllEdges(new ArrayList<>(touchingEdgesList));

            specifics.getVertexSet().remove(v); // remove the vertex itself

            return true;
        } else {
            return false;
        }
    }

    /**
     * @see Graph#vertexSet()
     */
    @Override public Set<V> vertexSet()
    {
        if (unmodifiableVertexSet == null) {
            unmodifiableVertexSet =
                Collections.unmodifiableSet(specifics.getVertexSet());
        }

        return unmodifiableVertexSet;
    }

    /**
     * @see Graph#getEdgeWeight(Object)
     */
    @Override public double getEdgeWeight(E e)
    {
        if (e instanceof DefaultWeightedEdge) {
            return ((DefaultWeightedEdge) e).getWeight();
        } else if (e == null) {
            throw new NullPointerException();
        } else {
            return WeightedGraph.DEFAULT_EDGE_WEIGHT;
        }
    }

    /**
     * @see WeightedGraph#setEdgeWeight(Object, double)
     */
    public void setEdgeWeight(E e, double weight)
    {
        assert (e instanceof DefaultWeightedEdge) : e.getClass();
        ((DefaultWeightedEdge) e).weight = weight;
    }

    private Specifics<V,E> createSpecifics()
    {
        if (this instanceof DirectedGraph<?, ?>) {
            return createDirectedSpecifics();
        } else if (this instanceof UndirectedGraph<?, ?>) {
            return createUndirectedSpecifics();
        } else {
            throw new IllegalArgumentException(
                "must be instance of either DirectedGraph or UndirectedGraph");
        }
    }

    protected Specifics<V,E> createUndirectedSpecifics()
    {
        return new FastLookupUndirectedSpecifics<>(this);
    }

    protected Specifics<V,E> createDirectedSpecifics()
    {
        return new FastLookupDirectedSpecifics<>(this);
    }

    private static class ArrayListFactory<VV, EE>
        implements EdgeSetFactory<VV, EE>,
            Serializable
    {
        private static final long serialVersionUID = 5936902837403445985L;

        /**
         * @see EdgeSetFactory
         */
        @Override public Set<EE> createEdgeSet(VV vertex)
        {
            // NOTE:  use size 1 to keep memory usage under control
            // for the common case of vertices with low degree
            return new ArrayUnenforcedSet<>(1);
        }
    }

}

// End AbstractBaseGraph.java
