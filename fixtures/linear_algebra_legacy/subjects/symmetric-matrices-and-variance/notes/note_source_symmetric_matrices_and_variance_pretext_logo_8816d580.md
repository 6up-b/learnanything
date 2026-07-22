---
schema_version: 1
id: note_source_symmetric_matrices_and_variance_pretext_logo_8816d580
subjects:
  - symmetric-matrices-and-variance
related_los: []
related_concepts: []
source_type: canonical_source
canonical_source:
  kind: website_page
  original_uri: 
    https://understandinglinearalgebra.org/sec-symmetric-matrices.html
  canonical_uri: 
    https://understandinglinearalgebra.org/sec-symmetric-matrices.html
  title: Symmetric matrices and variance PreTeXt logo
  authors: []
  retrieved_at: '2026-05-25T23:49:19Z'
  content_hash: 
    sha256:8816d580916bb0ba3193a12318f1fdc20388189dd48f6074df25b30acb459082
  license_hint:
created_at: '2026-05-25T23:49:19Z'
updated_at: '2026-05-25T23:49:19Z'
---

Skip to main content

# Understanding Linear Algebra

David Austin

\(\newcommand{\avec}{{\mathbf a}} \newcommand{\bvec}{{\mathbf b}} \newcommand{\cvec}{{\mathbf c}} \newcommand{\dvec}{{\mathbf d}} \newcommand{\dtil}{\widetilde{\mathbf d}} \newcommand{\evec}{{\mathbf e}} \newcommand{\fvec}{{\mathbf f}} \newcommand{\nvec}{{\mathbf n}} \newcommand{\pvec}{{\mathbf p}} \newcommand{\qvec}{{\mathbf q}} \newcommand{\svec}{{\mathbf s}} \newcommand{\tvec}{{\mathbf t}} \newcommand{\uvec}{{\mathbf u}} \newcommand{\vvec}{{\mathbf v}} \newcommand{\wvec}{{\mathbf w}} \newcommand{\xvec}{{\mathbf x}} \newcommand{\yvec}{{\mathbf y}} \newcommand{\zvec}{{\mathbf z}} \newcommand{\rvec}{{\mathbf r}} \newcommand{\mvec}{{\mathbf m}} \newcommand{\zerovec}{{\mathbf 0}} \newcommand{\onevec}{{\mathbf 1}} \newcommand{\real}{{\mathbb R}} \newcommand{\twovec}[2]{\left[\begin{array}{r}#1 \\ #2 \end{array}\right]} \newcommand{\ctwovec}[2]{\left[\begin{array}{c}#1 \\ #2 \end{array}\right]} \newcommand{\threevec}[3]{\left[\begin{array}{r}#1 \\ #2 \\ #3 \end{array}\right]} \newcommand{\cthreevec}[3]{\left[\begin{array}{c}#1 \\ #2 \\ #3 \end{array}\right]} \newcommand{\fourvec}[4]{\left[\begin{array}{r}#1 \\ #2 \\ #3 \\ #4 \end{array}\right]} \newcommand{\cfourvec}[4]{\left[\begin{array}{c}#1 \\ #2 \\ #3 \\ #4 \end{array}\right]} \newcommand{\fivevec}[5]{\left[\begin{array}{r}#1 \\ #2 \\ #3 \\ #4 \\ #5 \\ \end{array}\right]} \newcommand{\cfivevec}[5]{\left[\begin{array}{c}#1 \\ #2 \\ #3 \\ #4 \\ #5 \\ \end{array}\right]} \newcommand{\mattwo}[4]{\left[\begin{array}{rr}#1 \amp #2 \\ #3 \amp #4 \\ \end{array}\right]} \newcommand{\laspan}[1]{\text{Span}\left\{#1\right\}} \newcommand{\bcal}{{\cal B}} \newcommand{\ccal}{{\cal C}} \newcommand{\scal}{{\cal S}} \newcommand{\wcal}{{\cal W}} \newcommand{\ecal}{{\cal E}} \newcommand{\coords}[2]{\left\{#1\right\}_{#2}} \newcommand{\gray}[1]{\color{gray}{#1}} \newcommand{\lgray}[1]{\color{lightgray}{#1}} \newcommand{\rank}{\operatorname{rank}} \newcommand{\row}{\text{Row}} \newcommand{\col}{\text{Col}} \renewcommand{\row}{\text{Row}} \newcommand{\nul}{\text{Nul}} \newcommand{\var}{\text{Var}} \newcommand{\corr}{\text{corr}} \newcommand{\len}[1]{\left|#1\right|} \newcommand{\bbar}{\overline{\bvec}} \newcommand{\bhat}{\widehat{\bvec}} \newcommand{\bperp}{\bvec^\perp} \newcommand{\xhat}{\widehat{\xvec}} \newcommand{\vhat}{\widehat{\vvec}} \newcommand{\uhat}{\widehat{\uvec}} \newcommand{\what}{\widehat{\wvec}} \newcommand{\Sighat}{\widehat{\Sigma}} \newcommand{\basis}[2]{#1_1,#1_2,\ldots,#1_{#2}} \newcommand{\lt}{<} \newcommand{\gt}{>} \newcommand{\amp}{&} \definecolor{fillinmathshade}{gray}{0.9} \newcommand{\fillinmath}[1]{\mathchoice{\colorbox{fillinmathshade}{$\displaystyle \phantom{\,#1\,}$}}{\colorbox{fillinmathshade}{$\textstyle \phantom{\,#1\,}$}}{\colorbox{fillinmathshade}{$\scriptstyle \phantom{\,#1\,}$}}{\colorbox{fillinmathshade}{$\scriptscriptstyle\phantom{\,#1\,}$}}} \)

## Section7.1Symmetric matrices and variance

In this section, we will revisit the theory of eigenvalues and eigenvectors for the special class of matrices that aresymmetric, meaning that the matrix equals its transpose. This understanding of symmetric matrices will enable us to form singular value decompositions later in the chapter. We’ll also begin studying variance in this section as it provides an important context that motivates some of our later work.

🔗

To begin, remember that if\(A\)is a square matrix, we say that\(\vvec\)is an eigenvector of\(A\)with associated eigenvalue\(\lambda\)if\(A\vvec=\lambda\vvec\text{.}\)In other words, for these special vectors, the operation of matrix multiplication simplifies to scalar multiplication.

🔗

### Preview Activity7.1.1.

This preview activity reminds us how a basis of eigenvectors can be used to relate a square matrix to a diagonal one.

🔗



A\(1\times1\)standard coordinate grid and set of axes. Both the horizontal and vertical ranges run from\(-5\)to\(5\text{.}\)

🔗



A\(1\times1\)standard coordinate grid and set of axes. Both the horizontal and vertical ranges run from\(-5\)to\(5\text{.}\)

🔗

Figure7.1.1.Use these plots to sketch the vectors requested in the preview activity.

🔗

#### (a)

Suppose that\(D=\begin{bmatrix} 3 \amp 0 \\ 0 \amp -1 \end{bmatrix}\)and that\(\evec_1 = \twovec10\)and\(\evec_2=\twovec01\text{.}\)

-

Sketch the vectors\(\evec_1\)and\(D\evec_1\)on the left side ofFigure 7.1.1.

🔗

🔗

-

Sketch the vectors\(\evec_2\)and\(D\evec_2\)on the left side ofFigure 7.1.1.

🔗

🔗

-

Sketch the vectors\(\evec_1+2\evec_2\)and\(D(\evec_1+2\evec_2)\)on the left side.

🔗

🔗

-

Give a geometric description of the matrix transformation defined by\(D\text{.}\)

🔗

🔗

🔗

🔗

#### (b)

Now suppose we have vectors\(\vvec_1=\twovec11\)and\(\vvec_2=\twovec{-1}1\)and that\(A\)is a\(2\times2\)matrix such that

\begin{equation*} A\vvec_1 = 3\vvec_1, \hspace{24pt} A\vvec_2 = -\vvec_2\text{.} \end{equation*}

That is,\(\vvec_1\)and\(\vvec_2\)are eigenvectors of\(A\)with associated eigenvalues\(3\)and\(-1\text{.}\)

-

Sketch the vectors\(\vvec_1\)and\(A\vvec_1\)on the right side ofFigure 7.1.1.

🔗

🔗

-

Sketch the vectors\(\vvec_2\)and\(A\vvec_2\)on the right side ofFigure 7.1.1.

🔗

🔗

-

Sketch the vectors\(\vvec_1+2\vvec_2\)and\(A(\vvec_1+2\vvec_2)\)on the right side.

🔗

🔗

-

Give a geometric description of the matrix transformation defined by\(A\text{.}\)

🔗

🔗

🔗

🔗

#### (c)

In what ways are the matrix transformations defined by\(D\)and\(A\)related to one another?

🔗

🔗

🔗

The preview activity asks us to compare the matrix transformations defined by two matrices, a diagonal matrix\(D\)and a matrix\(A\)whose eigenvectors are given to us. The transformation defined by\(D\)stretches horizontally by a factor of 3 and reflects in the horizontal axis, as shown inFigure 7.1.2

🔗



On the left is a\(1\times1\)standard coordinate grid, a set of axes, and the unit square whose vertices are at the origin,\((1,0)\text{,}\)\((1,1)\text{,}\)and\((0,1)\text{.}\)

🔗

The diagram on the right shows these features after they have been transformed by the diagonal matrix\(D\text{.}\)The coordinate grid is stretched horizontally by a factor of\(3\text{,}\)and the unit square is transformed into a rectangle whose vertices are at the origin,\((3,0)\text{,}\)\((3,-1)\text{,}\)and\((0,-1)\text{.}\)This rectangle is obtained by stretching the unit square horizontally by a factor of\(3\)and flipping it over the horizontal axis.

🔗

Figure7.1.2.The matrix transformation defined by\(D\text{.}\)

🔗

By contrast, the transformation defined by\(A\)stretches the plane by a factor of 3 in the direction of\(\vvec_1\)and reflects in the line defined by\(\vvec_1\text{,}\)as seen inFigure 7.1.3.

🔗



On the left is a\(1\times1\)coordinate grid that has been rotated counterclockwise by\(45\)degrees so that the grid lines are parallel to the eigenvectors of\(A\text{.}\)The unit square has also been rotated.

🔗

The diagram on the right shows how the grid and square are transformed by the matrix\(A\text{.}\)The grid has been stretched by a factor of\(3\)in the direction of the eigenvector\(\vvec_1\text{.}\)The square has also been stretched by a factor of\(3\)in the direction of\(\vvec_1\)and reflected across the line defined by\(\vvec_1\text{.}\)

🔗

The diagram is much like the previous one only rotated by\(45\)degrees so that the axes have been rotated to align with the eigenvectors.

🔗

Figure7.1.3.The matrix transformation defined by\(A\text{.}\)

🔗

In this way, we see that the matrix transformations defined by these two matrices are equivalent after a\(45^\circ\)rotation. This notion of equivalence is what we calledsimilarityinSection 4.3. There we considered a square\(m\times m\)matrix\(A\)that provided enough eigenvectors to form a basis of\(\real^m\text{.}\)For example, suppose we can construct a basis for\(\real^m\)using eigenvectors\(\vvec_1,\vvec_2,\ldots,\vvec_m\)having associated eigenvalues\(\lambda_1,\lambda_2,\ldots,\lambda_m\text{.}\)Forming the matrices,

\begin{equation*} P = \begin{bmatrix} \vvec_1\amp\vvec_2\amp\ldots\amp\vvec_m \end{bmatrix}, \hspace{24pt} D = \begin{bmatrix} \lambda_1 \amp 0 \amp \ldots \amp 0 \\ 0 \amp \lambda_2 \amp \ldots \amp 0 \\ \vdots\amp\vdots\amp\ddots\amp\vdots\\ 0 \amp 0 \amp \ldots \amp \lambda_m \end{bmatrix}, \end{equation*}

enables us to write\(A = PDP^{-1}\text{.}\)This is what it means for\(A\)to be diagonalizable.

🔗

For the example in the preview activity, we are led to form

\begin{equation*} P = \begin{bmatrix} 1 \amp -1 \\ 1 \amp 1 \end{bmatrix}, \hspace{24pt} D = \begin{bmatrix} 3 \amp 0 \\ 0 \amp - 1 \end{bmatrix} \end{equation*}

which tells us that\(A=PDP^{-1} = \begin{bmatrix} 1 \amp 2 \\ 2 \amp 1 \end{bmatrix} \text{.}\)

🔗

Notice that the matrix\(A\)has eigenvectors\(\vvec_1\)and\(\vvec_2\)that not only form a basis for\(\real^2\)but, in fact, form an orthogonal basis for\(\real^2\text{.}\)Given the prominent role played by orthogonal bases in the last chapter, we would like to understand what conditions on a matrix enable us to form an orthogonal basis of eigenvectors.

🔗

### Subsection7.1.1Symmetric matrices and orthogonal diagonalization

Let’s begin by looking at some examples in the next activity.

🔗

#### Activity7.1.2.

Remember that the Sage commandA.right_eigenmatrix()attempts to find a basis for\(\real^m\)consisting of eigenvectors of\(A\text{.}\)In particular, the assignmentD, P = A.right_eigenmatrix()provides a diagonal matrix\(D\)constructed from the eigenvalues of\(A\)with the columns of\(P\)containing the associated eigenvectors.

-

For each of the following matrices, determine whether there is a basis for\(\real^2\)consisting of eigenvectors of that matrix. When there is such a basis, form the matrices\(P\)and\(D\)and verify that the matrix equals\(PDP^{-1}\text{.}\)

-

\(\begin{bmatrix} 3 \amp -4 \\ 4 \amp 3 \end{bmatrix} \text{.}\)

🔗

🔗

-

\(\begin{bmatrix} 1 \amp 1 \\ -1 \amp 3 \end{bmatrix} \text{.}\)

🔗

🔗

-

\(\begin{bmatrix} 1 \amp 0\\ -1 \amp 2 \end{bmatrix} \text{.}\)

🔗

🔗

-

\(\begin{bmatrix} 9 \amp 2 \\ 2 \amp 6 \end{bmatrix} \text{.}\)

🔗

🔗

🔗

🔗

-

For which of these examples is it possible to form an orthogonal basis for\(\real^2\)consisting of eigenvectors?

🔗

🔗

-

For any such matrix\(A\text{,}\)find an orthonormal basis of eigenvectors and explain why\(A=QDQ^{-1}\)where\(Q\)is an orthogonal matrix.

🔗

🔗

-

Finally, explain why\(A=QDQ^T\)in this case.

🔗

🔗

-

When\(A=QDQ^T\text{,}\)what is the relationship between\(A\)and\(A^T\text{?}\)

🔗

🔗

🔗

🔗

The examples in this activity illustrate a range of possibilities. First, a matrix may have complex eigenvalues, in which case it will not be diagonalizable. Second, even if all the eigenvalues are real, there may not be a basis of eigenvalues if the dimension of one of the eigenspaces is less than the algebraic multiplicity of the associated eigenvalue.

🔗

We are interested in matrices for which there is an orthogonal basis of eigenvectors. When this happens, we can create an orthonormal basis of eigenvectors by scaling each eigenvector in the basis so that its length is 1. Putting these orthonormal vectors into a matrix\(Q\)produces an orthogonal matrix, which means that\(Q^T=Q^{-1}\text{.}\)We then have

\begin{equation*} A = QDQ^{-1} = QDQ^T. \end{equation*}

In this case, we say that\(A\)isorthogonally diagonalizable.

🔗

#### Definition7.1.4.

If there is an orthonormal basis of\(\real^n\)consisting of eigenvectors of the matrix\(A\text{,}\)we say that\(A\)isorthogonally diagonalizable. In particular, we can write\(A=QDQ^T\)where\(Q\)is an orthogonal matrix.

🔗

🔗

When\(A\)is orthogonally diagonalizable, notice that

\begin{equation*} A^T=(QDQ^T)^T = (Q^T)^TD^TQ^T = QDQ^T = A. \end{equation*}

That is, when\(A\)is orthogonally diagonalizable,\(A=A^T\)and we say that\(A\)issymmetric.

🔗

#### Definition7.1.5.

Asymmetricmatrix\(A\)is one for which\(A=A^T\text{.}\)

🔗

🔗

#### Example7.1.6.

Consider the matrix\(A = \begin{bmatrix} -2 \amp 36 \\ 36 \amp -23 \end{bmatrix} \text{,}\)which has eigenvectors\(\vvec_1 = \twovec43\text{,}\)with associated eigenvalue\(\lambda_1=25\text{,}\)and\(\vvec_2=\twovec{3}{-4}\text{,}\)with associated eigenvalue\(\lambda_2=-50\text{.}\)Notice that\(\vvec_1\)and\(\vvec_2\)are orthogonal so we can form an orthonormal basis of eigenvectors:

\begin{equation*} \uvec_1 = \twovec{4/5}{3/5}, \hspace{24pt} \uvec_1 = \twovec{3/5}{-4/5}\text{.} \end{equation*}

🔗

In this way, we construct the matrices

\begin{equation*} Q = \begin{bmatrix} 4/5 \amp 3/5 \\ 3/5 \amp -4/5 \\ \end{bmatrix}, \hspace{24pt} D = \begin{bmatrix} 25 \amp 0 \\ 0 \amp -50 \end{bmatrix} \end{equation*}

and note that\(A = QDQ^T\text{.}\)

🔗

Notice also that, as expected,\(A\)is symmetric; that is,\(A=A^T\text{.}\)

🔗

🔗

#### Example7.1.7.

If\(A = \begin{bmatrix} 1 \amp 2 \\ 2 \amp 1 \\ \end{bmatrix} \text{,}\)then there is an orthogonal basis of eigenvectors\(\vvec_1 = \twovec11\)and\(\vvec_2 = \twovec{-1}1\)with eigenvalues\(\lambda_1=3\)and\(\lambda_2=-1\text{.}\)Using these eigenvectors, we form the orthogonal matrix\(Q\)consisting of eigenvectors and the diagonal matrix\(D\text{,}\)where

\begin{equation*} Q = \begin{bmatrix} 1/\sqrt{2} \amp -1/\sqrt{2} \\ 1/\sqrt{2} \amp 1/\sqrt{2} \end{bmatrix},\hspace{24pt} D = \begin{bmatrix} 3 \amp 0 \\ 0 \amp - 1 \end{bmatrix}. \end{equation*}

Then we have\(A = QDQ^T\text{.}\)

🔗

Notice that the matrix transformation represented by\(Q\)is a\(45^\circ\)rotation while that represented by\(Q^T=Q^{-1}\)is a\(-45^\circ\)rotation. Therefore, if we multiply a vector\(\xvec\)by\(A\text{,}\)we can decompose the multiplication as

\begin{equation*} A\xvec = Q(D(Q^T\xvec)). \end{equation*}

That is, we first rotate\(\xvec\)by\(-45^\circ\text{,}\)then apply the diagonal matrix\(D\text{,}\)which stretches and reflects, and finally rotate by\(45^\circ\text{.}\)We may visualize this factorization as inFigure 7.1.8.

🔗



Our goal is to explain the transformation of the plane by\(A\text{,}\)which was described inFigure 7.1.3, using the orthogonal diagonalization\(A=QDQ^T\text{.}\)There are four diagrams here arranged in a\(2\times2\)array, which will be read from left to right and then top to bottom. The transformation from one diagram to the next is given by one of the factors in the orthogonal diagonalization\(A=QDQ^T\text{.}\)

🔗

The diagram in the upper left shows a\(1\times1\)coordinate grid and unit square rotated counterclockwise by\(45\)degrees. The matrix\(Q^T\text{,}\)the first factor in the orthogonal diagonalization, rotates this diagram clockwise by\(45\)degrees to obtain the diagram in the upper right. Here we see the standard\(1\times1\)coordinate grid and the unit square.

🔗

The diagram in the lower left is the result of applying the next matrix\(D\)in the factorization, which we have already explored. The coordinate grid is stretched horiztonally by a factor of\(3\text{,}\)and the unit square is transformed into a rectangle by stretching horizontally by a factor of\(3\)and flipping across the horizontal axis.

🔗

Finally the diagram in the lower right results from applying the last matrix\(Q\)in the factorization, which rotates the previous diagram counterclockwise by\(45\)degrees.

🔗

Figure7.1.8.The transformation defined by\(A=QDQ^T\)can be interpreted as a sequence of geometric transformations:\(Q^T\)rotates by\(-45^\circ\text{,}\)\(D\)stretches and reflects, and\(Q\)rotates by\(45^\circ\text{.}\)

🔗

In fact, a similar picture holds any time the matrix\(A\)is orthogonally diagonalizable.

🔗

🔗

We have seen that a matrix that is orthogonally diagonalizable must be symmetric. In fact, it turns out that any symmetric matrix is orthogonally diagonalizable. We record this fact in the next theorem.

🔗

#### Theorem7.1.9.The Spectral Theorem.

The matrix\(A\)is orthogonally diagonalizable if and only if\(A\)is symmetric.

🔗

🔗

#### Activity7.1.3.

Each of the following matrices is symmetric so the Spectral Theorem tells us that each is orthogonally diagonalizable. The point of this activity is to find an orthogonal diagonalization for each matrix.

🔗

To begin, find a basis for each eigenspace. Use this basis to find an orthogonal basis for each eigenspace and put these bases together to find an orthogonal basis for\(\real^m\)consisting of eigenvectors. Use this basis to write an orthogonal diagonalization of the matrix.

-

\(\begin{bmatrix} 0 \amp 2 \\ 2 \amp 3 \end{bmatrix} \text{.}\)

🔗

🔗

-

\(\begin{bmatrix} 4 \amp -2 \amp 14 \\ -2 \amp 19 \amp -16 \\ 14 \amp -16 \amp 13 \end{bmatrix} \text{.}\)

🔗

🔗

-

\(\begin{bmatrix} 5 \amp 4 \amp 2 \\ 4 \amp 5 \amp 2 \\ 2 \amp 2 \amp 2 \end{bmatrix} \text{.}\)

🔗

🔗

-

Consider the matrix\(A = B^TB\)where\(B = \begin{bmatrix} 0 \amp 1 \amp 2 \\ 2 \amp 0 \amp 1 \end{bmatrix} \text{.}\)Explain how we know that\(A\)is symmetric and then find an orthogonal diagonalization of\(A\text{.}\)

🔗

🔗

🔗

🔗

As the examples inActivity 7.1.3illustrate, the Spectral Theorem implies a number of things. Namely, if\(A\)is a symmetric\(m\times m\)matrix, then

-

the eigenvalues of\(A\)are real.

🔗

🔗

-

there is a basis of\(\real^m\)consisting of eigenvectors.

🔗

🔗

-

two eigenvectors that are associated to different eigenvalues are orthogonal.

🔗

🔗

🔗

We won’t justify the first two facts here since that would take us rather far afield. However, it will be helpful to explain the third fact. To begin, notice the following:

\begin{equation*} \vvec\cdot(A\wvec) = \vvec^TA\wvec = (A^T\vvec)^T\wvec = (A^T\vvec)\cdot \wvec. \end{equation*}

This is a useful fact that we’ll employ quite a bit in the future so let’s summarize it in the following proposition.

🔗

#### Proposition7.1.10.

For any matrix\(A\text{,}\)we have

\begin{equation*} \vvec\cdot(A\wvec) = (A^T\vvec)\cdot\wvec. \end{equation*}

In particular, if\(A\)is symmetric, then

\begin{equation*} \vvec\cdot(A\wvec) = (A\vvec)\cdot\wvec. \end{equation*}

🔗

🔗

#### Example7.1.11.

Suppose a symmetric matrix\(A\)has eigenvectors\(\vvec_1\text{,}\)with associated eigenvalue\(\lambda_1=3\text{,}\)and\(\vvec_2\text{,}\)with associated eigenvalue\(\lambda_2 = 10\text{.}\)Notice that

\begin{align*} (A\vvec_1)\cdot\vvec_2 \amp = 3\vvec_1\cdot\vvec_2\\ \vvec_1\cdot(A\vvec_2) \amp = 10\vvec_1\cdot\vvec_2. \end{align*}

Since\((A\vvec_1)\cdot\vvec_2 = \vvec_1\cdot(A\vvec_2)\)byProposition 7.1.10, we have

\begin{equation*} 3\vvec_1\cdot\vvec_2 = 10 \vvec_1\cdot\vvec_2, \end{equation*}

which can only happen if\(\vvec_1\cdot\vvec_2 = 0\text{.}\)Therefore,\(\vvec_1\)and\(\vvec_2\)are orthogonal.

🔗

More generally, the same argument shows that two eigenvectors of a symmetric matrix associated to distinct eigenvalues are orthogonal.

🔗

🔗

🔗

### Subsection7.1.2Variance

Many of the ideas we’ll encounter in this chapter, such as orthogonal diagonalizations, can be applied to the study of data. In fact, it can be useful to understand these applications because they provide an important context in which mathematical ideas have a more concrete meaning and their motivation appears more clearly. For that reason, we will now introduce the statistical concept of variance as a way to gain insight into the significance of orthogonal diagonalizations.

🔗

Given a set of data points, their variance measures how spread out the points are. The next activity looks at some examples.

🔗

#### Activity7.1.4.

We’ll begin with a set of three data points

\begin{equation*} \dvec_1=\twovec11, \hspace{24pt} \dvec_2=\twovec21, \hspace{24pt} \dvec_3=\twovec34. \end{equation*}

-

Find the centroid, or mean,\(\overline{\dvec} = \frac1N\sum_j \dvec_j\text{.}\)Then plot the data points and their centroid inFigure 7.1.12.

🔗



A standard\(1\times1\)coordinate grid and set of axes. The horizontal and vertical ranges run from\(-4\)to\(4\text{.}\)

🔗

Figure7.1.12.Plot the data points and their centroid here.

🔗

🔗

-

Notice that the centroid lies in the center of the data so the spread of the data will be measured by how far away the points are from the centroid. To simplify our calculations, find the demeaned data points

\begin{equation*} \dtil_j = \dvec_j - \overline{\dvec} \end{equation*}

and plot them inFigure 7.1.13.

🔗



A standard\(1\times1\)coordinate grid and set of axes. The horizontal and vertical ranges run from\(-4\)to\(4\text{.}\)

🔗

Figure7.1.13.Plot the demeaned data points\(\dtil_j\)here.

🔗

🔗

-

Now that the data has been demeaned, we will define the total variance as the average of the squares of the distances from the origin; that is, the total variance is

\begin{equation*} V = \frac 1N\sum_j~|\dtil_j|^2. \end{equation*}

Find the total variance\(V\)for our set of three points.

🔗

🔗

-

Now plot the projections of the demeaned data onto the\(x\)and\(y\)axes usingFigure 7.1.14and find the variances\(V_x\)and\(V_y\)of the projected points.

🔗



A horizontal number line beginning on the left at\(-4\)and ending on the right at\(4\text{.}\)

🔗



A vertical number line beginning on the bottom at\(-4\)and ending on the top at\(4\text{.}\)

🔗

Figure7.1.14.Plot the projections of the demeaned data onto the\(x\)and\(y\)axes.

🔗

🔗

-

Which of the variances,\(V_x\)and\(V_y\text{,}\)is larger and how does the plot of the projected points explain your response?

🔗

🔗

-

What do you notice about the relationship between\(V\text{,}\)\(V_x\text{,}\)and\(V_y\text{?}\)How does the Pythagorean theorem explain this relationship?

🔗

🔗

-

Plot the projections of the demeaned data points onto the lines defined by vectors\(\vvec_1=\twovec11\)and\(\vvec_2=\twovec{-1}1\)usingFigure 7.1.15and find the variances\(V_{\vvec_1}\)and\(V_{\vvec_2}\)of these projected points.

🔗



A standard\(1\times1\)coordinate grid, a set of axes, and two orthogonal lines parallel to the vectors\(\vvec_1=\twovec11\)and\(\vvec_2=\twovec{-1}1\text{.}\)

🔗

Figure7.1.15.Plot the projections of the deameaned data onto the lines defined by\(\vvec_1\)and\(\vvec_2\text{.}\)

🔗

🔗

-

What is the relationship between the total variance\(V\)and\(V_{\vvec_1}\)and\(V_{\vvec_2}\text{?}\)How does the Pythagorean theorem explain your response?

🔗

🔗

🔗

🔗

Notice that variance enjoys an additivity property. Consider, for instance, the situation where our data points are two-dimensional and suppose that the demeaned points are\(\dtil_j=\twovec{\widetilde{x}_j}{\widetilde{y}_j}\text{.}\)We have

\begin{equation*} |\dtil_j|^2 = \widetilde{x}_j^2 + \widetilde{y}_j^2. \end{equation*}

If we take the average over all data points, we find that the total variance\(V\)is the sum of the variances in the\(x\)and\(y\)directions:

\begin{align*} \frac1N \sum_j~ |\dtil_j|^2 \amp = \frac1N \sum_j~ \widetilde{x}_j^2 + \frac1N \sum_j~ \widetilde{y}_j^2 \\ V \amp = V_x + V_y. \end{align*}

🔗

More generally, suppose that we have an orthonormal basis\(\uvec_1\)and\(\uvec_2\text{.}\)If we project the demeaned points onto the line defined by\(\uvec_1\text{,}\)we obtain the points\((\dtil_j\cdot\uvec_1)\uvec_1\)so that

\begin{equation*} V_{\uvec_1} = \frac1N\sum_j ~|(\dtil_j\cdot\uvec_1)~\uvec_1|^2 = \frac1N\sum_j~(\dtil_j\cdot\uvec_1)^2. \end{equation*}

🔗

For each of our demeaned data points, the Projection Formula tells us that

\begin{equation*} \dtil_j = (\dtil_j\cdot\uvec_1)~\uvec_1 + (\dtil_j\cdot\uvec_2)~\uvec_2. \end{equation*}

We then have

\begin{equation*} |\dtil_j|^2 = \dtil_j\cdot\dtil_j = (\dtil_j\cdot\uvec_1)^2 + (\dtil_j\cdot\uvec_2)^2 \end{equation*}

since\(\uvec_1\cdot\uvec_2 = 0\text{.}\)When we average over all the data points, we find that the total variance\(V\)is the sum of the variances in the\(\uvec_1\)and\(\uvec_2\)directions. This leads to the following proposition, in which this observation is expressed more generally.

🔗

#### Proposition7.1.16.Additivity of Variance.

If\(W\)is a subspace with orthonormal basis\(\uvec_1\text{,}\)\(\uvec_2\text{,}\)\(\ldots\text{,}\)\(\uvec_n\text{,}\)then the variance of the points projected onto\(W\)is the sum of the variances in the\(\uvec_j\)directions:

\begin{equation*} V_W = V_{\uvec_1} + V_{\uvec_2} + \ldots + V_{\uvec_n}. \end{equation*}

🔗

🔗

The next activity demonstrates a more efficient way to find the variance\(V_{\uvec}\)in a particular direction and connects our discussion of variance with symmetric matrices.

🔗

#### Activity7.1.5.

Let’s return to the dataset from the previous activity in which we have demeaned data points:

\begin{equation*} \dtil_1=\twovec{-1}{-1},\hspace{24pt} \dtil_2=\twovec{0}{-1},\hspace{24pt} \dtil_3=\twovec{1}{2}. \end{equation*}

Our goal is to compute the variance\(V_{\uvec}\)in the direction defined by a unit vector\(\uvec\text{.}\)

🔗

To begin, form the demeaned data matrix

\begin{equation*} A = \begin{bmatrix} \dtil_1 \amp \dtil_2 \amp \dtil_3 \end{bmatrix} \end{equation*}

and suppose that\(\uvec\)is a unit vector.

-

Write the vector\(A^T\uvec\)in terms of the dot products\(\dtil_j\cdot\uvec\text{.}\)

🔗

🔗

-

Explain why\(V_{\uvec} = \frac13|A^T\uvec|^2\text{.}\)

🔗

🔗

-

ApplyProposition 7.1.10to explain why

\begin{equation*} V_{\uvec} = \frac13|A^T\uvec|^2 = \frac13 (A^T\uvec)\cdot(A^T\uvec) = \uvec^T\left(\frac13 AA^T\right)\uvec = \uvec\cdot\left(\frac13 AA^T\right)\uvec \end{equation*}

🔗

🔗

-

In general, the matrix\(C=\frac1N~AA^T\)is called thecovariancematrix of the dataset, and it is useful because the variance\(V_{\uvec} = \uvec\cdot(C\uvec)\text{,}\)as we have just seen. Find the matrix\(C\)for our dataset with three points.

🔗

🔗

-

Use the covariance matrix to find the variance\(V_{\uvec_1}\)when\(\uvec_1=\twovec{1/\sqrt{5}}{2/\sqrt{5}}\text{.}\)

🔗

🔗

-

Use the covariance matrix to find the variance\(V_{\uvec_2}\)when\(\uvec_2=\twovec{-2/\sqrt{5}}{1/\sqrt{5}}\text{.}\)Since\(\uvec_1\)and\(\uvec_2\)are orthogonal, verify that the sum of\(V_{\uvec_1}\)and\(V_{\uvec_2}\)gives the total variance.

🔗

🔗

-

Explain why the covariance matrix\(C\)is a symmetric matrix.

🔗

🔗

🔗

🔗

This activity introduced the covariance matrix of a dataset, which is defined to be\(C=\frac1N~AA^T\)where\(A\)is the matrix of demeaned data points. Notice that

\begin{equation*} C^T = \frac1N~(AA^T)^T = \frac1N~AA^T = C, \end{equation*}

which tells us that\(C\)is symmetric. In particular, we know that it is orthogonally diagonalizable, an observation that will play an important role in the future.

🔗

This activity also demonstrates the significance of the covariance matrix, which is recorded in the following proposition.

🔗

#### Proposition7.1.17.

If\(C\)is the covariance matrix associated to a demeaned dataset and\(\uvec\)is a unit vector, then the variance of the demeaned points projected onto the line defined by\(\uvec\)is

\begin{equation*} V_{\uvec} = \uvec\cdot C\uvec. \end{equation*}

🔗

🔗

Our goal in the future will be to find directions\(\uvec\)where the variance is as large as possible and directions where it is as small as possible. The next activity demonstrates why this is useful.

🔗

#### Activity7.1.6.

-

Evaluating the following Sage cell loads a dataset consisting of 100 demeaned data points and provides a plot of them. It also provides the demeaned data matrix\(A\text{.}\)

🔗

What is the shape of the covariance matrix\(C\text{?}\)Find\(C\)and verify your response.

🔗

🔗

-

By visually inspecting the data, determine which is larger,\(V_x\)or\(V_y\text{.}\)Then compute both of these quantities to verify your response.

🔗

🔗

-

What is the total variance\(V\text{?}\)

🔗

🔗

-

In approximately what direction is the variance greatest? Choose a reasonable vector\(\uvec\)that points in approximately that direction and find\(V_{\uvec}\text{.}\)

🔗

🔗

-

In approximately what direction is the variance smallest? Choose a reasonable vector\(\wvec\)that points in approximately that direction and find\(V_{\wvec}\text{.}\)

🔗

🔗

-

How are the directions\(\uvec\)and\(\wvec\)in the last two parts of this problem related to one another? Why does this relationship hold?

🔗

🔗

🔗

🔗

This activity illustrates how variance can identify a line along which the data are concentrated. When the data primarily lie along a line defined by a vector\(\uvec_1\text{,}\)then the variance in that direction will be large while the variance in an orthogonal direction\(\uvec_2\)will be small.

🔗

Remember that variance is additive, according toProposition 7.1.16, so that if\(\uvec_1\)and\(\uvec_2\)are orthogonal unit vectors, then the total variance is

\begin{equation*} V = V_{\uvec_1} + V_{\uvec_2}. \end{equation*}

Therefore, if we choose\(\uvec_1\)to be the direction where\(V_{\uvec_1}\)is a maximum, then\(V_{\uvec_2}\)will be a minimum.

🔗

In the next section, we will use an orthogonal diagonalization of the covariance matrix\(C\)to find the directions having the greatest and smallest variances. In this way, we will be able to determine when data are concentrated along a line or subspace.

🔗

🔗

### Subsection7.1.3Summary

This section explored both symmetric matrices and variance. In particular, we saw that

-

A matrix\(A\)is orthogonally diagonalizable if there is an orthonormal basis of eigenvectors. In particular, we can write\(A=QDQ^T\text{,}\)where\(D\)is a diagonal matrix of eigenvalues and\(Q\)is an orthogonal matrix of eigenvectors.

🔗

🔗

-

The Spectral Theorem tells us that a matrix\(A\)is orthogonally diagonalizable if and only if it is symmetric; that is,\(A=A^T\text{.}\)

🔗

🔗

-

The variance of a dataset can be computed using the covariance matrix\(C=\frac1N~AA^T\text{,}\)where\(A\)is the matrix of demeaned data points. In particular, the variance of the demeaned data points projected onto the line defined by the unit vector\(\uvec\)is\(V_{\uvec} = \uvec\cdot C\uvec\text{.}\)

🔗

🔗

-

Variance is additive so that if\(W\)is a subspace with orthonormal basis\(\uvec_1, \uvec_2,\ldots,\uvec_n\text{,}\)then

\begin{equation*} V_W = V_{\uvec_1} + V_{\uvec_2} + \ldots + V_{\uvec_n}. \end{equation*}

🔗

🔗

🔗

🔗

### Exercises7.1.4Exercises

#### 1.

For each of the following matrices, find the eigenvalues and a basis for each eigenspace. Determine whether the matrix is diagonalizable and, if so, find a diagonalization. Determine whether the matrix is orthogonally diagonalizable and, if so, find an orthogonal diagonalization.

-

\(\displaystyle \begin{bmatrix} 5 \amp 1 \\ -1 \amp 3 \\ \end{bmatrix}\)

🔗

🔗

-

\(\displaystyle \begin{bmatrix} 0 \amp 1 \\ 1 \amp 0 \\ \end{bmatrix}\)

🔗

🔗

-

\(\displaystyle \begin{bmatrix} 1 \amp 0 \amp 0 \\ 2 \amp -2 \amp 0 \\ 0 \amp 1 \amp 4 \\ \end{bmatrix}\)

🔗

🔗

-

\(\displaystyle \begin{bmatrix} 2 \amp 5 \amp -4\\ 5 \amp -7 \amp 5 \\ -4 \amp 5 \amp 2 \\ \end{bmatrix}\)

🔗

🔗

🔗

🔗

#### 2.

Consider the matrix\(A = \begin{bmatrix} 1 \amp 2 \amp 2 \\ 2 \amp 1 \amp 2 \\ 2 \amp 2 \amp 1 \\ \end{bmatrix}\)whose eigenvalues are\(\lambda_1=5\text{,}\)\(\lambda_2=-1\text{,}\)and\(\lambda_3 = -1\text{.}\)

-

Explain why\(A\)is orthogonally diagonalizable.

🔗

🔗

-

Find an orthonormal basis for the eigenspace\(E_5\text{.}\)

🔗

🔗

-

Find a basis for the eigenspace\(E_{-1}\text{.}\)

🔗

🔗

-

Now find an orthonormal basis for\(E_{-1}\text{.}\)

🔗

🔗

-

Find matrices\(D\)and\(Q\)such that\(A=QDQ^T\text{.}\)

🔗

🔗

🔗

🔗

#### 3.

Find an orthogonal diagonalization, if one exists, for the following matrices.

-

\(\begin{bmatrix} 11 \amp 4 \amp 12 \\ 4 \amp -3 \amp -16 \\ 12 \amp -16 \amp 1 \end{bmatrix} \text{.}\)

🔗

🔗

-

\(\begin{bmatrix} 1 \amp 0 \amp 2 \\ 0 \amp 1 \amp 2 \\ -2 \amp -2 \amp 1 \\ \end{bmatrix} \text{.}\)

🔗

🔗

-

\(\begin{bmatrix} 9 \amp 3 \amp 3 \amp 3\\ 3 \amp 9 \amp 3 \amp 3\\ 3 \amp 3 \amp 9 \amp 3\\ 3 \amp 3 \amp 3 \amp 9\\ \end{bmatrix} \text{.}\)

🔗

🔗

🔗

🔗

#### 4.

Suppose that\(A\)is an\(m\times n\)matrix and that\(B=A^TA\text{.}\)

-

Explain why\(B\)is orthogonally diagonalizable.

🔗

🔗

-

Explain why\(\vvec\cdot(B\vvec) = \len{A\vvec}^2\text{.}\)

🔗

🔗

-

Suppose that\(\uvec\)is an eigenvector of\(B\)with associated eigenvalue\(\lambda\)and that\(\uvec\)has unit length. Explain why\(\lambda = \len{A\uvec}^2\text{.}\)

🔗

🔗

-

Explain why the eigenvalues of\(B\)are nonnegative.

🔗

🔗

-

If\(C\)is the covariance matrix associated to a demeaned dataset, explain why the eigenvalues of\(C\)are nonnegative.

🔗

🔗

🔗

🔗

#### 5.

Suppose that you have the data points

\begin{equation*} (2,0), (2,3), (4,1), (3,2), (4,4). \end{equation*}

-

Find the demeaned data points.

🔗

🔗

-

Find the total variance\(V\)of the dataset.

🔗

🔗

-

Find the variance in the direction\(\evec_1 = \twovec10\)and the variance in the direction\(\evec_2=\twovec01\text{.}\)

🔗

🔗

-

Project the demeaned data points onto the line defined by\(\vvec_1=\twovec21\)and find the variance of these projected points.

🔗

🔗

-

Project the demeaned data points onto the line defined by\(\vvec_2=\twovec1{-2}\)and find the variance of these projected points.

🔗

🔗

-

How and why are the results of from the last two parts related to the total variance?

🔗

🔗

🔗

🔗

#### 6.

Suppose you have six 2-dimensional data points arranged in the matrix

\begin{equation*} \begin{bmatrix} 2 \amp 0 \amp 4 \amp 4 \amp 5 \amp 3 \\ 1 \amp 0 \amp 3 \amp 5 \amp 4 \amp 5 \end{bmatrix}. \end{equation*}

-

Find the matrix\(A\)of demeaned data points and plot the points inFigure 7.1.18.



A standard\(1\times1\)coordinate grid and set of axes. The horizontal and vertical ranges run from\(-4\)to\(4\text{.}\)

🔗

Figure7.1.18.A plot for the demeaned data points.

🔗

🔗

🔗

-

Construct the covariance matrix\(C\)and explain why you know that it is orthogonally diagonalizable.

🔗

🔗

-

Find an orthogonal diagonalization of\(C\text{.}\)

🔗

🔗

-

Sketch the lines corresponding to the two eigenvectors on the plot above.

🔗

🔗

-

Find the variances in the directions of the eigenvectors.

🔗

🔗

🔗

🔗

#### 7.

Suppose that\(C\)is the covariance matrix of a demeaned dataset.

-

Suppose that\(\uvec\)is an eigenvector of\(C\)with associated eigenvalue\(\lambda\)and that\(\uvec\)has unit length. Explain why\(V_{\uvec} = \lambda\text{.}\)

🔗

🔗

-

Suppose that the covariance matrix of a demeaned dataset can be written as\(C=QDQ^T\)where

\begin{equation*} Q = \begin{bmatrix} \uvec_1 \amp \uvec_2 \end{bmatrix}, \hspace{24pt} D = \begin{bmatrix} 10 \amp 0 \\ 0 \amp 0 \\ \end{bmatrix}. \end{equation*}

What is\(V_{\uvec_2}\text{?}\)What does this tell you about the demeaned data?

🔗

🔗

-

Explain why the total variance of a dataset equals the sum of the eigenvalues of the covariance matrix.

🔗

🔗

🔗

🔗

#### 8.

Determine whether the following statements are true or false and explain your thinking.

-

If\(A\)is an invertible, orthogonally diagonalizable matrix, then so is\(A^{-1}\text{.}\)

🔗

🔗

-

If\(\lambda=2+i\)is an eigenvalue of\(A\text{,}\)then\(A\)cannot be orthogonally diagonalizable.

🔗

🔗

-

If there is a basis for\(\real^m\)consisting of eigenvectors of\(A\text{,}\)then\(A\)is orthogonally diagonalizable.

🔗

🔗

-

If\(\uvec\)and\(\vvec\)are eigenvectors of a symmetric matrix associated to eigenvalues -2 and 3, then\(\uvec\cdot\vvec=0\text{.}\)

🔗

🔗

-

If\(A\)is a square matrix, then\(\uvec\cdot(A\vvec) = (A\uvec)\cdot\vvec\text{.}\)

🔗

🔗

🔗

🔗

#### 9.

Suppose that\(A\)is a noninvertible, symmetric\(3\times3\)matrix having eigenvectors

\begin{equation*} \vvec_1 = \threevec2{-1}2,\hspace{24pt} \vvec_2 = \threevec141 \end{equation*}

and associated eigenvalues\(\lambda_1 = 20\)and\(\lambda_2 = -4\text{.}\)Find matrices\(Q\)and\(D\)such that\(A = QDQ^T\text{.}\)

🔗

🔗

#### 10.

Suppose that\(W\)is a plane in\(\real^3\)and that\(P\)is the\(3\times3\)matrix that projects vectors orthogonally onto\(W\text{.}\)

-

Explain why\(P\)is orthogonally diagonalizable.

🔗

🔗

-

What are the eigenvalues of\(P\text{?}\)

🔗

🔗

-

Explain the relationship between the eigenvectors of\(P\)and the plane\(W\text{.}\)

🔗

🔗

🔗

🔗

🔗

🔗

PrevTopNext
