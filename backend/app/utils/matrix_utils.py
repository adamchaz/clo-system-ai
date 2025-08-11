"""
Matrix Mathematics Utilities

Converted from VBA MatrixMath.bas module - provides matrix operations
for correlation analysis, portfolio optimization, and risk calculations.

This module provides:
- Matrix multiplication, inversion, addition, subtraction
- Matrix decomposition (Cholesky, LU)
- Special matrix operations (QOM, matrix square root)
- Utility functions for matrix manipulation
"""

from typing import List, Tuple, Optional, Union
import numpy as np
import scipy.linalg
from scipy.linalg import cholesky, inv, solve
import logging

logger = logging.getLogger(__name__)

ArrayType = Union[List[List[float]], np.ndarray]


class MatrixUtils:
    """Matrix mathematics utilities converted from VBA MatrixMath.bas"""
    
    @staticmethod
    def to_numpy(matrix: ArrayType) -> np.ndarray:
        """Convert input to numpy array"""
        if isinstance(matrix, np.ndarray):
            return matrix
        return np.array(matrix, dtype=float)
    
    @staticmethod
    def to_list(matrix: np.ndarray) -> List[List[float]]:
        """Convert numpy array to list of lists"""
        return matrix.tolist()
    
    # Basic Matrix Operations
    @staticmethod
    def matrix_identity(order: int) -> np.ndarray:
        """Create identity matrix of given order"""
        return np.eye(order)
    
    @staticmethod
    def matrix_multiply(mat1: ArrayType, mat2: ArrayType) -> np.ndarray:
        """Multiply two matrices"""
        arr1 = MatrixUtils.to_numpy(mat1)
        arr2 = MatrixUtils.to_numpy(mat2)
        
        try:
            return np.dot(arr1, arr2)
        except ValueError as e:
            logger.error(f"Matrix multiplication error: {e}")
            raise ValueError(f"Cannot multiply matrices with shapes {arr1.shape} and {arr2.shape}")
    
    @staticmethod
    def matrix_inverse(matrix: ArrayType) -> np.ndarray:
        """Calculate matrix inverse using LU decomposition"""
        arr = MatrixUtils.to_numpy(matrix)
        
        if arr.shape[0] != arr.shape[1]:
            raise ValueError("Matrix must be square for inversion")
        
        try:
            return inv(arr)
        except np.linalg.LinAlgError as e:
            logger.error(f"Matrix inversion error: {e}")
            raise ValueError("Matrix is singular and cannot be inverted")
    
    @staticmethod
    def matrix_add(mat1: ArrayType, mat2: ArrayType) -> np.ndarray:
        """Add two matrices"""
        arr1 = MatrixUtils.to_numpy(mat1)
        arr2 = MatrixUtils.to_numpy(mat2)
        
        if arr1.shape != arr2.shape:
            raise ValueError(f"Matrix shapes must match: {arr1.shape} vs {arr2.shape}")
        
        return arr1 + arr2
    
    @staticmethod
    def matrix_subtract(mat1: ArrayType, mat2: ArrayType) -> np.ndarray:
        """Subtract two matrices"""
        arr1 = MatrixUtils.to_numpy(mat1)
        arr2 = MatrixUtils.to_numpy(mat2)
        
        if arr1.shape != arr2.shape:
            raise ValueError(f"Matrix shapes must match: {arr1.shape} vs {arr2.shape}")
        
        return arr1 - arr2
    
    @staticmethod
    def matrix_multiply_scalar(matrix: ArrayType, scalar: float) -> np.ndarray:
        """Multiply matrix by scalar"""
        arr = MatrixUtils.to_numpy(matrix)
        return arr * scalar
    
    # Matrix Norms and Properties
    @staticmethod
    def matrix_abs(matrix: ArrayType) -> float:
        """Calculate matrix absolute value (Frobenius norm)"""
        arr = MatrixUtils.to_numpy(matrix)
        return np.linalg.norm(arr, 'fro')
    
    @staticmethod
    def matrix_determinant(matrix: ArrayType) -> float:
        """Calculate matrix determinant"""
        arr = MatrixUtils.to_numpy(matrix)
        
        if arr.shape[0] != arr.shape[1]:
            raise ValueError("Matrix must be square for determinant calculation")
        
        return np.linalg.det(arr)
    
    # Advanced Matrix Operations
    @staticmethod
    def matrix_cholesky(matrix: ArrayType) -> np.ndarray:
        """
        Calculate Cholesky decomposition of positive definite matrix
        Returns lower triangular matrix L such that matrix = L * L.T
        """
        arr = MatrixUtils.to_numpy(matrix)
        
        if arr.shape[0] != arr.shape[1]:
            raise ValueError("Matrix must be square for Cholesky decomposition")
        
        try:
            # SciPy returns upper triangular by default, we want lower
            return cholesky(arr, lower=True)
        except np.linalg.LinAlgError as e:
            logger.error(f"Cholesky decomposition error: {e}")
            raise ValueError("Matrix is not positive definite for Cholesky decomposition")
    
    @staticmethod
    def matrix_sqrt(matrix: ArrayType, max_iterations: int = 500, 
                   tolerance: float = 1e-15) -> np.ndarray:
        """
        Calculate matrix square root using Denman-Beavers iteration
        Converted from VBA MatrixSQRT function
        """
        arr = MatrixUtils.to_numpy(matrix)
        
        if arr.shape[0] != arr.shape[1]:
            raise ValueError("Matrix must be square for square root calculation")
        
        n = arr.shape[0]
        Y = arr.copy()
        Z = np.eye(n)
        
        for i in range(max_iterations):
            try:
                inv_Y = MatrixUtils.matrix_inverse(Y)
                inv_Z = MatrixUtils.matrix_inverse(Z)
                
                Z_new = 0.5 * (Z + inv_Y)
                Y_new = 0.5 * (Y + inv_Z)
                
                # Check convergence
                diff = MatrixUtils.matrix_abs(
                    MatrixUtils.matrix_subtract(
                        MatrixUtils.matrix_multiply(Y_new, Y_new), 
                        arr
                    )
                )
                
                if diff < tolerance * n:
                    return Y_new
                
                Y = Y_new
                Z = Z_new
                
            except ValueError as e:
                logger.error(f"Matrix square root iteration {i} failed: {e}")
                break
        
        logger.warning(f"Matrix square root did not converge after {max_iterations} iterations")
        return Y
    
    @staticmethod
    def lu_decomposition(matrix: ArrayType) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        LU decomposition with partial pivoting
        Returns P, L, U such that P*A = L*U
        """
        arr = MatrixUtils.to_numpy(matrix)
        
        if arr.shape[0] != arr.shape[1]:
            raise ValueError("Matrix must be square for LU decomposition")
        
        try:
            P, L, U = scipy.linalg.lu(arr)
            return P, L, U
        except Exception as e:
            logger.error(f"LU decomposition error: {e}")
            raise ValueError("LU decomposition failed")
    
    @staticmethod
    def matrix_qom(matrix: ArrayType) -> np.ndarray:
        """
        Quadratic Optimization Method (QOM) for correlation matrix adjustment
        Converted from VBA MatrixQOM function
        
        This method adjusts correlation matrices to ensure they are valid
        (all eigenvalues non-negative) while preserving as much structure as possible.
        """
        arr = MatrixUtils.to_numpy(matrix)
        n = arr.shape[0]
        
        if arr.shape[0] != arr.shape[1]:
            raise ValueError("Matrix must be square for QOM")
        
        result = arr.copy()
        
        for i in range(n):
            # Calculate row adjustment
            row_sum = np.sum(result[i, :])
            lambda_adj = (row_sum - 1.0) / n
            
            # Apply adjustment
            adjusted_row = result[i, :] - lambda_adj
            
            # Check for negative values
            negative_mask = adjusted_row < 0
            
            if np.any(negative_mask):
                # Sort values and apply QOM correction
                sorted_indices = np.argsort(adjusted_row)
                sorted_values = adjusted_row[sorted_indices]
                
                # Find optimal cutoff point
                for k in range(1, n + 1):
                    cumsum = np.sum(sorted_values[:k])
                    c_k = (1.0 - cumsum) / k
                    
                    if c_k + sorted_values[k - 1] > 0:
                        if k < n and c_k + sorted_values[k] <= 0:
                            break
                
                # Apply correction
                c_final = (1.0 - np.sum(sorted_values[:k])) / k
                
                for j in range(n):
                    idx = sorted_indices[j]
                    if j < k:
                        result[i, idx] = sorted_values[j] + c_final
                    else:
                        result[i, idx] = 0.0
            else:
                result[i, :] = adjusted_row
        
        return result
    
    # Eigenvalue and Eigenvector Operations
    @staticmethod
    def eigenvalues_eigenvectors(matrix: ArrayType) -> Tuple[np.ndarray, np.ndarray]:
        """
        Calculate eigenvalues and eigenvectors
        Returns (eigenvalues, eigenvectors)
        """
        arr = MatrixUtils.to_numpy(matrix)
        
        if arr.shape[0] != arr.shape[1]:
            raise ValueError("Matrix must be square for eigenvalue calculation")
        
        try:
            eigenvals, eigenvecs = np.linalg.eig(arr)
            # Sort by eigenvalue magnitude (descending)
            idx = np.argsort(np.abs(eigenvals))[::-1]
            return eigenvals[idx], eigenvecs[:, idx]
        except np.linalg.LinAlgError as e:
            logger.error(f"Eigenvalue calculation error: {e}")
            raise ValueError("Eigenvalue calculation failed")
    
    @staticmethod
    def is_positive_definite(matrix: ArrayType) -> bool:
        """Check if matrix is positive definite"""
        arr = MatrixUtils.to_numpy(matrix)
        
        if arr.shape[0] != arr.shape[1]:
            return False
        
        try:
            # Try Cholesky decomposition
            cholesky(arr, lower=True)
            return True
        except np.linalg.LinAlgError:
            return False
    
    @staticmethod
    def is_positive_semidefinite(matrix: ArrayType, tolerance: float = 1e-10) -> bool:
        """Check if matrix is positive semidefinite"""
        arr = MatrixUtils.to_numpy(matrix)
        
        if arr.shape[0] != arr.shape[1]:
            return False
        
        try:
            eigenvals, _ = MatrixUtils.eigenvalues_eigenvectors(arr)
            return np.all(eigenvals >= -tolerance)
        except ValueError:
            return False
    
    # Matrix Conditioning and Regularization
    @staticmethod
    def condition_number(matrix: ArrayType) -> float:
        """Calculate matrix condition number"""
        arr = MatrixUtils.to_numpy(matrix)
        
        if arr.shape[0] != arr.shape[1]:
            raise ValueError("Matrix must be square for condition number calculation")
        
        return np.linalg.cond(arr)
    
    @staticmethod
    def regularize_correlation_matrix(matrix: ArrayType, 
                                    min_eigenvalue: float = 1e-8) -> np.ndarray:
        """
        Regularize correlation matrix to ensure positive definiteness
        
        This method adjusts eigenvalues to ensure they are above the minimum threshold
        while preserving the overall structure of the correlation matrix.
        """
        arr = MatrixUtils.to_numpy(matrix)
        
        if arr.shape[0] != arr.shape[1]:
            raise ValueError("Matrix must be square")
        
        # Get eigendecomposition
        eigenvals, eigenvecs = MatrixUtils.eigenvalues_eigenvectors(arr)
        
        # Adjust negative or very small eigenvalues
        adjusted_eigenvals = np.maximum(eigenvals, min_eigenvalue)
        
        # Reconstruct matrix
        regularized = eigenvecs @ np.diag(adjusted_eigenvals) @ eigenvecs.T
        
        # Ensure diagonal is 1 (for correlation matrix)
        diag_vals = np.diag(regularized)
        scaling = np.sqrt(np.outer(diag_vals, diag_vals))
        regularized = regularized / scaling
        np.fill_diagonal(regularized, 1.0)
        
        return regularized
    
    # Utility Functions
    @staticmethod
    def is_symmetric(matrix: ArrayType, tolerance: float = 1e-10) -> bool:
        """Check if matrix is symmetric"""
        arr = MatrixUtils.to_numpy(matrix)
        
        if arr.shape[0] != arr.shape[1]:
            return False
        
        return np.allclose(arr, arr.T, atol=tolerance)
    
    @staticmethod
    def make_symmetric(matrix: ArrayType) -> np.ndarray:
        """Make matrix symmetric by averaging with its transpose"""
        arr = MatrixUtils.to_numpy(matrix)
        
        if arr.shape[0] != arr.shape[1]:
            raise ValueError("Matrix must be square")
        
        return 0.5 * (arr + arr.T)
    
    @staticmethod
    def matrix_rank(matrix: ArrayType, tolerance: float = None) -> int:
        """Calculate matrix rank"""
        arr = MatrixUtils.to_numpy(matrix)
        
        if tolerance is None:
            tolerance = np.finfo(arr.dtype).eps * max(arr.shape) * np.max(np.abs(arr))
        
        return np.linalg.matrix_rank(arr, tol=tolerance)
    
    @staticmethod
    def trace(matrix: ArrayType) -> float:
        """Calculate matrix trace (sum of diagonal elements)"""
        arr = MatrixUtils.to_numpy(matrix)
        
        if arr.shape[0] != arr.shape[1]:
            raise ValueError("Matrix must be square for trace calculation")
        
        return np.trace(arr)
    
    @staticmethod
    def frobenius_norm(matrix: ArrayType) -> float:
        """Calculate Frobenius norm of matrix"""
        arr = MatrixUtils.to_numpy(matrix)
        return np.linalg.norm(arr, 'fro')
    
    # Matrix Conversion Utilities
    @staticmethod
    def convert_to_correlation_matrix(covariance_matrix: ArrayType) -> np.ndarray:
        """Convert covariance matrix to correlation matrix"""
        cov = MatrixUtils.to_numpy(covariance_matrix)
        
        if cov.shape[0] != cov.shape[1]:
            raise ValueError("Covariance matrix must be square")
        
        std_devs = np.sqrt(np.diag(cov))
        correlation = cov / np.outer(std_devs, std_devs)
        
        # Ensure diagonal is exactly 1
        np.fill_diagonal(correlation, 1.0)
        
        return correlation
    
    @staticmethod
    def nearest_correlation_matrix(matrix: ArrayType, 
                                  max_iterations: int = 1000,
                                  tolerance: float = 1e-6) -> np.ndarray:
        """
        Find nearest correlation matrix using alternating projections
        (Higham's algorithm)
        """
        A = MatrixUtils.to_numpy(matrix)
        
        if A.shape[0] != A.shape[1]:
            raise ValueError("Matrix must be square")
        
        n = A.shape[0]
        
        # Initialize
        Y = A.copy()
        
        for iteration in range(max_iterations):
            # Project onto positive semidefinite matrices
            eigenvals, eigenvecs = np.linalg.eigh(Y)
            eigenvals = np.maximum(eigenvals, 0)
            X = eigenvecs @ np.diag(eigenvals) @ eigenvecs.T
            
            # Project onto matrices with unit diagonal
            np.fill_diagonal(X, 1.0)
            
            # Check convergence
            diff = np.linalg.norm(X - Y, 'fro')
            if diff < tolerance:
                return X
            
            Y = X
        
        logger.warning(f"Nearest correlation matrix did not converge after {max_iterations} iterations")
        return Y


# Module-level convenience functions
def matrix_multiply(mat1: ArrayType, mat2: ArrayType) -> np.ndarray:
    """Convenience function for matrix multiplication"""
    return MatrixUtils.matrix_multiply(mat1, mat2)

def matrix_inverse(matrix: ArrayType) -> np.ndarray:
    """Convenience function for matrix inversion"""
    return MatrixUtils.matrix_inverse(matrix)

def matrix_cholesky(matrix: ArrayType) -> np.ndarray:
    """Convenience function for Cholesky decomposition"""
    return MatrixUtils.matrix_cholesky(matrix)

def matrix_sqrt(matrix: ArrayType) -> np.ndarray:
    """Convenience function for matrix square root"""
    return MatrixUtils.matrix_sqrt(matrix)

def regularize_correlation_matrix(matrix: ArrayType) -> np.ndarray:
    """Convenience function for correlation matrix regularization"""
    return MatrixUtils.regularize_correlation_matrix(matrix)