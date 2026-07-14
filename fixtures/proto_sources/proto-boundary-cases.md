# Notation

We write vectors bold, matrices upper-case. That is all.

# Inner Products and Orthogonality

An inner product adds geometry to a vector space: lengths and angles.
Orthogonal vectors have inner product zero, and orthonormal bases make
coordinates trivial to compute via projection.

The Gram–Schmidt process turns any basis into an orthonormal one by
subtracting projections one vector at a time.

## Projections

The projection of v onto u is (⟨v,u⟩/⟨u,u⟩)u. Projection matrices satisfy
P² = P and P^T = P.

## Least Squares

When Ax = b has no solution, minimize ‖Ax − b‖ instead. The normal equations
A^T A x̂ = A^T b characterize the minimizer geometrically: the residual is
orthogonal to the column space.

## The Spectral Connection

Symmetric matrices have orthonormal eigenbases, which is why projections and
least squares diagonalize so cleanly in the right coordinates.

# Summary

Orthogonality turns approximation into geometry.
