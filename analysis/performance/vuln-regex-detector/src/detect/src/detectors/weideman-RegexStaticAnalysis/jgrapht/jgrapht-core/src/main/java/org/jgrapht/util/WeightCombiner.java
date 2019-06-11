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
 * WeightCombiner.java
 * -------------------------
 * (C) Copyright 2009-2009, by Ilya Razenshteyn
 *
 * Original Author:  Ilya Razenshteyn and Contributors.
 *
 * $Id$
 *
 * Changes
 * -------
 * 02-Feb-2009 : Initial revision (IR);
 *
 */
package org.jgrapht.util;

/**
 * Binary operator for edge weights. There are some prewritten operators.
 */
public interface WeightCombiner
{
    /**
     * Sum of weights.
     */
    WeightCombiner SUM =
            (a, b) -> a + b;

    /**
     * Multiplication of weights.
     */
    WeightCombiner MULT =
            (a, b) -> a * b;

    /**
     * Minimum weight.
     */
    WeightCombiner MIN =
            (a, b) -> Math.min(a, b);

    /**
     * Maximum weight.
     */
    WeightCombiner MAX =
            (a, b) -> Math.max(a, b);

    /**
     * First weight.
     */
    WeightCombiner FIRST =
            (a, b) -> a;

    /**
     * Second weight.
     */
    WeightCombiner SECOND =
            (a, b) -> b;

    /**
     * Combines two weights.
     *
     * @param a first weight
     * @param b second weight
     *
     * @return result of the operator
     */
    double combine(double a, double b);
}

// End WeightCombiner.java
