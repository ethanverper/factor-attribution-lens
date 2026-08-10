"""Covariance matrix estimation with regularization for near-singular inputs.

See decision 0003: sample covariance is used by default, but with a small
number of return observations relative to the number of holdings (or with
near-duplicate/perfectly-correlated holdings), the sample covariance matrix
can be singular or numerically ill-conditioned, which breaks mean-variance
optimization (division by a near-zero eigenvalue). This module detects that
case via the matrix's condition number and, if triggered, regularizes via
eigenvalue clipping: negative/near-zero eigenvalues are floored to a small
positive value (proportional to the largest eigenvalue) and the matrix is
reconstructed, which is a standard, easily-audited "nearest correlation
matrix"-style fix.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

CONDITION_NUMBER_THRESHOLD = 1e8
EIGENVALUE_FLOOR_RATIO = 1e-6  # floor = this * largest eigenvalue


def estimate_covariance(returns: pd.DataFrame) -> tuple[np.ndarray, bool, float]:
    """Sample covariance of `returns` (periodic, not annualized), regularized if needed.

    Returns (cov_matrix, was_regularized, final_condition_number).
    """
    sample_cov = returns.cov().to_numpy()
    condition_number = float(np.linalg.cond(sample_cov))

    eigenvalues = np.linalg.eigvalsh(sample_cov)
    is_psd = eigenvalues.min() > 0

    if is_psd and condition_number <= CONDITION_NUMBER_THRESHOLD:
        return sample_cov, False, condition_number

    regularized = _clip_eigenvalues(sample_cov)
    new_condition_number = float(np.linalg.cond(regularized))
    return regularized, True, new_condition_number


def _clip_eigenvalues(matrix: np.ndarray) -> np.ndarray:
    """Floor small/negative eigenvalues, reconstruct a symmetric PSD matrix."""
    eigenvalues, eigenvectors = np.linalg.eigh(matrix)
    floor = EIGENVALUE_FLOOR_RATIO * max(eigenvalues.max(), 1e-12)
    clipped = np.clip(eigenvalues, a_min=floor, a_max=None)
    reconstructed = eigenvectors @ np.diag(clipped) @ eigenvectors.T
    # Symmetrize to kill float round-trip asymmetry.
    return (reconstructed + reconstructed.T) / 2.0
