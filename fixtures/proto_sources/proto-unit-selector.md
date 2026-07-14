# Vectors and Spaces

Vectors are elements of a vector space closed under addition and scalar
multiplication. The span of a set is every linear combination of it.

A basis is a linearly independent spanning set; its size is the dimension.

# Linear Maps

A linear map T preserves addition and scaling: T(u + v) = T(u) + T(v).

The kernel and image are subspaces; rank-nullity ties their dimensions:
dim V = dim ker T + dim im T.

# Determinants

The determinant measures signed volume scaling.

    det(AB) = det(A) det(B)

A matrix is invertible exactly when its determinant is nonzero.

# Eigentheory

An eigenvector satisfies Av = λv. The characteristic polynomial det(A − λI)
finds the eigenvalues.

## Worked example

For A = [[2,1],[1,2]]: eigenvalues 3 and 1, eigenvectors (1,1) and (1,−1).

# Exercises

1. Show the set of solutions to Ax = 0 forms a subspace.
2. Compute the determinant of [[1,2],[3,4]].
3. Find the eigenvalues of [[0,1],[1,0]].
4. Prove rank-nullity for a 3×2 matrix of rank 2.
