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
/* -------------------------
 * MaskEdgeSet.java
 * -------------------------
 * (C) Copyright 2007-2008, by France Telecom
 *
 * Original Author:  Guillaume Boulmier and Contributors.
 *
 * $Id$
 *
 * Changes
 * -------
 * 05-Jun-2007 : Initial revision (GB);
 *
 */
package org.jgrapht.graph;

import java.util.*;

import org.jgrapht.*;
import org.jgrapht.util.*;
import org.jgrapht.util.PrefetchIterator.*;


/**
 * Helper for {@link MaskSubgraph}.
 *
 * @author Guillaume Boulmier
 * @since July 5, 2007
 */
class MaskEdgeSet<V, E>
    extends AbstractSet<E>
{
    private Set<E> edgeSet;

    private Graph<V, E> graph;

    private MaskFunctor<V, E> mask;

    private transient TypeUtil<E> edgeTypeDecl = null;

    public MaskEdgeSet(
        Graph<V, E> graph,
        Set<E> edgeSet,
        MaskFunctor<V, E> mask)
    {
        this.graph = graph;
        this.edgeSet = edgeSet;
        this.mask = mask;
    }

    /**
     * @see java.util.Collection#contains(java.lang.Object)
     */
    @Override public boolean contains(Object o)
    {
        // Force a cast to type E. This is nonsense, of course, but
        // it's erased by the compiler anyway.
        E e = (E) o;

        // If o isn't an E, the first check will fail and
        // short-circuit, so we never try to test the mask on non-edge
        // object inputs.
        return edgeSet.contains(e)
            && !mask.isEdgeMasked(e)
            && !mask.isVertexMasked(graph.getEdgeSource(e))
            && !mask.isVertexMasked(graph.getEdgeTarget(e));
    }

    /**
     * @see java.util.Set#iterator()
     */
    @Override public Iterator<E> iterator()
    {
        return new PrefetchIterator<E>(new MaskEdgeSetNextElementFunctor());
    }

    /**
     * @see java.util.Set#size()
     */
    @Override public int size()
    {
        return (int) edgeSet.stream().filter(e -> contains(e)).count();
    }

    private class MaskEdgeSetNextElementFunctor
        implements NextElementFunctor<E>
    {
        private Iterator<E> iter;

        public MaskEdgeSetNextElementFunctor()
        {
            this.iter = MaskEdgeSet.this.edgeSet.iterator();
        }

        @Override public E nextElement()
            throws NoSuchElementException
        {
            E edge = this.iter.next();
            while (isMasked(edge)) {
                edge = this.iter.next();
            }
            return edge;
        }

        private boolean isMasked(E edge)
        {
            return MaskEdgeSet.this.mask.isEdgeMasked(edge)
                || MaskEdgeSet.this.mask.isVertexMasked(
                    MaskEdgeSet.this.graph.getEdgeSource(edge))
                || MaskEdgeSet.this.mask.isVertexMasked(
                    MaskEdgeSet.this.graph.getEdgeTarget(edge));
        }
    }
}

// End MaskEdgeSet.java
