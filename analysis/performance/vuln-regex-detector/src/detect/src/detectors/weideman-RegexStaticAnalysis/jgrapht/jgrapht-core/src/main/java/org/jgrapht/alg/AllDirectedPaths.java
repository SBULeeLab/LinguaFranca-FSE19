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
 * AllDirectedPaths.java
 * -------------------------
 * (C) Copyright 2015-2015, Vera-Licona Research Group and Contributors.
 *
 * Original Author:  Andrew Gainer-Dewar, Ph.D. (Vera-Licona Research Group)
 * Contributor(s):
 *
 * Changes
 * -------
 * Feb-2016 : Initial version;
 *
 */
package org.jgrapht.alg;

import java.util.*;

import org.jgrapht.*;
import org.jgrapht.graph.*;


/**
 * A Dijkstra-like algorithm to find all paths between two sets of nodes in a
 * directed graph, with options to search only simple paths and to limit the
 * path length.
 *
 * @author Andrew Gainer-Dewar
 * @since Feb, 2016
 */

public class AllDirectedPaths<V, E>
{
    private final DirectedGraph<V, E> graph;

    public AllDirectedPaths(DirectedGraph<V, E> graph)
    {
        if (graph == null) {
            throw new IllegalArgumentException("Graph cannot be null!");
        }

        this.graph = graph;
    }

    /**
     * Calculate (and return) all paths from the source vertex to the target
     * vertex.
     *
     * @param sourceVertex the source vertex
     * @param targetVertex the target vertex
     * @param simplePathsOnly if true, only search simple
     * (non-self-intersecting) paths
     * @param maxPathLength maximum number of edges to allow in a path (if null,
     * all paths are considered, which may be very slow due to potentially huge
     * output)
     */
    public List<GraphPath<V, E>> getAllPaths(
        V sourceVertex,
        V targetVertex,
        boolean simplePathsOnly,
        Integer maxPathLength)
    {
        return getAllPaths(
            Collections.singleton(sourceVertex),
            Collections.singleton(targetVertex),
            simplePathsOnly,
            maxPathLength);
    }

    /**
     * Calculate (and return) all paths from the source vertices to the target
     * vertices.
     *
     * @param sourceVertices the source vertices
     * @param targetVertices the target vertices
     * @param simplePathsOnly if true, only search simple
     * (non-self-intersecting) paths
     * @param maxPathLength maximum number of edges to allow in a path (if null,
     * all paths are considered, which may be very slow due to potentially huge
     * output)
     *
     * @return list of all paths from the sources to the targets containing no
     * more than maxPathLength edges
     */
    public List<GraphPath<V, E>> getAllPaths(
        Set<V> sourceVertices,
        Set<V> targetVertices,
        boolean simplePathsOnly,
        Integer maxPathLength)
    {
        if ((maxPathLength != null) && (maxPathLength < 0)) {
            throw new IllegalArgumentException(
                "maxPathLength must be non-negative if defined");
        }

        if (!simplePathsOnly && (maxPathLength == null)) {
            throw new IllegalArgumentException(
                "If search is not restricted to simple paths, a maximum path length must be set to avoid infinite cycles");
        }

        if ((sourceVertices.isEmpty()) || (targetVertices.isEmpty())) {
            return Collections.emptyList();
        }

        // Decorate the edges with the minimum path lengths through them
        Map<E, Integer> edgeMinDistancesFromTargets =
            edgeMinDistancesBackwards(targetVertices, maxPathLength);

        // Generate all the paths

        return generatePaths(
            sourceVertices,
            targetVertices,
            simplePathsOnly,
            maxPathLength,
            edgeMinDistancesFromTargets);
    }

    /**
     * Compute the minimum number of edges in a path to the targets through each
     * edge, so long as it is not greater than a bound.
     *
     * @param targetVertices the target vertices
     * @param maxPathLength maximum number of edges to allow in a path (if null,
     * all edges will be considered, which may be expensive)
     *
     * @return the minimum number of edges in a path from each edge to the
     * targets, encoded in a Map
     */
    private Map<E, Integer> edgeMinDistancesBackwards(
        Set<V> targetVertices,
        Integer maxPathLength)
    {
        /*
         * We walk backwards through the network from the target
         * vertices, marking edges and vertices with their minimum
         * distances as we go.
         */
        Map<E, Integer> edgeMinDistances = new HashMap<>();
        Map<V, Integer> vertexMinDistances = new HashMap<>();
        Queue<V> verticesToProcess = new LinkedList<>();

        // Input sanity checking
        if (maxPathLength != null) {
            if (maxPathLength < 0) {
                throw new IllegalArgumentException(
                    "maxPathLength must be non-negative if defined");
            }
            if (maxPathLength == 0) {
                return edgeMinDistances;
            }
        }

        // Bootstrap the process with the target vertices
        for (V target : targetVertices) {
            vertexMinDistances.put(target, 0);
            verticesToProcess.add(target);
        }

        // Work through the node queue. When it's empty, we're done!
        for (V vertex; (vertex = verticesToProcess.poll()) != null;) {
            assert vertexMinDistances.containsKey(vertex);

            Integer childDistance = vertexMinDistances.get(vertex) + 1;

            // Check whether the incoming edges of this node are correctly
            // decorated
            for (E edge : graph.incomingEdgesOf(vertex)) {
                // Mark the edge if needed
                if (!edgeMinDistances.containsKey(edge)
                    || (edgeMinDistances.get(edge) > childDistance))
                {
                    edgeMinDistances.put(edge, childDistance);
                }

                // Mark the edge's source vertex if needed
                V edgeSource = graph.getEdgeSource(edge);
                if (!vertexMinDistances.containsKey(edgeSource)
                    || (vertexMinDistances.get(edgeSource) > childDistance))
                {
                    vertexMinDistances.put(edgeSource, childDistance);

                    if ((maxPathLength == null)
                        || (childDistance < maxPathLength))
                    {
                        verticesToProcess.add(edgeSource);
                    }
                }
            }
        }

        assert verticesToProcess.isEmpty();
        return edgeMinDistances;
    }

    /**
     * Generate all paths from the sources to the targets, using pre-computed
     * minimum distances.
     *
     * @param sourceVertices the source vertices
     * @param targetVertices the target vertices
     * @param maxPathLength maximum number of edges to allow in a path
     * @param simplePathsOnly if true, only search simple
     * (non-self-intersecting) paths (if null, all edges will be considered,
     * which may be expensive)
     * @param edgeMinDistancesFromTargets the minimum number of edges in a path
     * to a target through each edge, as computed by {@code
     * edgeMinDistancesBackwards}.
     *
     * @return a List of all GraphPaths from the sources to the targets
     * satisfying the given constraints
     */
    private List<GraphPath<V, E>> generatePaths(
        Set<V> sourceVertices,
        Set<V> targetVertices,
        boolean simplePathsOnly,
        Integer maxPathLength,
        Map<E, Integer> edgeMinDistancesFromTargets)
    {
        /*
         * We walk forwards through the network from the source
         * vertices, exploring all outgoing edges whose minimum
         * distances is small enough.
         */
        List<GraphPath<V, E>> completePaths = new ArrayList<>();
        Deque<List<E>> incompletePaths = new LinkedList<>();

        // Input sanity checking
        if (maxPathLength != null) {
            if (maxPathLength < 0) {
                throw new IllegalArgumentException(
                    "maxPathLength must be non-negative if defined");
            }
            if (maxPathLength == 0) {
                return completePaths;
            }
        }

        // Bootstrap the search with the source vertices
        for (V source : sourceVertices) {
            for (E edge : graph.outgoingEdgesOf(source)) {
                assert graph.getEdgeSource(edge).equals(source);

                if (edgeMinDistancesFromTargets.containsKey(edge)) {
                    List<E> path = Collections.singletonList(edge);
                    incompletePaths.add(path);
                }
            }
        }

        // Walk through the queue of incomplete paths
        for (
            List<E> incompletePath;
            (incompletePath = incompletePaths.poll()) != null;)
        {
            Integer lengthSoFar = incompletePath.size();
            assert (maxPathLength == null) || (lengthSoFar < maxPathLength);

            E leafEdge = incompletePath.get(lengthSoFar - 1);
            V leafNode = graph.getEdgeTarget(leafEdge);

            Set<V> pathVertices = new HashSet<>();
            for (E pathEdge : incompletePath) {
                pathVertices.add(graph.getEdgeSource(pathEdge));
                pathVertices.add(graph.getEdgeTarget(pathEdge));
            }

            for (E outEdge : graph.outgoingEdgesOf(leafNode)) {
                // Proceed if the outgoing edge is marked and the mark
                // is sufficiently small
                if (edgeMinDistancesFromTargets.containsKey(outEdge)
                    && ((maxPathLength == null)
                        || ((edgeMinDistancesFromTargets.get(outEdge)
                                + lengthSoFar) <= maxPathLength)))
                {
                    List<E> newPath = new ArrayList<>(incompletePath);
                    newPath.add(outEdge);

                    // If requested, make sure this path isn't self-intersecting
                    if (simplePathsOnly
                        && pathVertices.contains(
                            graph.getEdgeTarget(outEdge)))
                    {
                        continue;
                    }

                    // If this path reaches a target, add it to completePaths
                    if (targetVertices.contains(graph.getEdgeTarget(outEdge))) {
                        GraphPath<V, E> completePath = makePath(newPath);
                        assert sourceVertices.contains(
                            completePath.getStartVertex());
                        assert targetVertices.contains(
                            completePath.getEndVertex());
                        assert (maxPathLength == null)
                            || (completePath.getWeight() <= maxPathLength);
                        completePaths.add(completePath);
                    }

                    // If this path is short enough, consider further
                    // extensions of it
                    if ((maxPathLength == null)
                        || (newPath.size() < maxPathLength))
                    {
                        incompletePaths.addFirst(newPath); // We use
                                                           // incompletePaths in
                                                           // FIFO mode to avoid
                                                           // memory blowup
                    }
                }
            }
        }

        assert incompletePaths.isEmpty();
        return completePaths;
    }

    /**
     * Transform an ordered list of edges into a GraphPath
     *
     * @param edges the edges
     *
     * @return the corresponding GraphPath
     */
    private GraphPath<V, E> makePath(List<E> edges)
    {
        V source = graph.getEdgeSource(edges.get(0));
        V target = graph.getEdgeTarget(edges.get(edges.size() - 1));
        double weight = edges.size();
        return new GraphPathImpl<>(graph, source, target, edges, weight);
    }
}

// End AllDirectedPaths.java
