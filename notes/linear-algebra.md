# Linear Algebra — Essentials

## Vectors
A vector is a quantity with both magnitude and direction.
- **In 2D:** v = (x, y)
- **In 3D:** v = (x, y, z)
- **Magnitude:** |v| = √(x² + y²)
- **Unit vector:** v̂ = v / |v|

## Matrices
A matrix is a rectangular array of numbers.
- **Addition:** element-wise (same dimensions required)
- **Multiplication:** (A × B)ᵢⱼ = Σ Aᵢₖ × Bₖⱼ
- Note: Matrix multiplication is NOT commutative (AB ≠ BA in general)

## Determinant
- For 2×2 matrix: det(A) = ad - bc  where A = [[a,b],[c,d]]
- det(A) ≠ 0 → matrix is invertible

## Inverse Matrix
A⁻¹ such that A × A⁻¹ = I (Identity matrix)
For 2×2: A⁻¹ = (1/det(A)) × [[d, -b], [-c, a]]

## Eigenvalues and Eigenvectors
For matrix A: Av = λv
- λ = eigenvalue (scalar)
- v = eigenvector (non-zero vector)
- Found by solving: det(A - λI) = 0

**Application:** PCA (Principal Component Analysis), Google PageRank

## Systems of Linear Equations
Ax = b
Solve with:
1. **Gaussian elimination** (row reduction)
2. **Matrix inversion:** x = A⁻¹b
3. **Cramer's rule** (for small systems)

## Dot Product & Cross Product
- **Dot product:** a · b = |a||b|cos(θ) = Σ aᵢbᵢ  → gives a scalar
- **Cross product:** a × b → gives a vector perpendicular to both (3D only)
