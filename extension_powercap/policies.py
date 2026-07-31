"""
Three parameter-matched policy architectures for the study:

  1. ClassicalPolicy      — plain MLP actor-critic, width-tuned to the parameter budget.
  2. HybridPolicy         — encoder -> parameterized quantum circuit (PQC) -> decoder.
  3. AblatedHybridPolicy  — identical encoder/decoder shape, PQC swapped for a
                            same-parameter-count classical block (the "Q-ablated" control:
                            if this matches HybridPolicy, credit goes to the wiring, not quantum).

The PQC is a differentiable statevector simulator written in pure PyTorch
(angle embedding -> L layers of per-qubit RY/RZ rotations + ring of CNOTs -> Pauli-Z
expectation per qubit). 4-8 qubits => 16-256 complex amplitudes: trivially fast,
no external quantum dependency, exact gradients via autograd.
"""
from __future__ import annotations

import math
import torch
import torch.nn as nn


# ------------------------------ PQC simulator ------------------------------ #

def _kron_all(mats):
    out = mats[0]
    for m in mats[1:]:
        out = torch.kron(out, m)
    return out


class PQC(nn.Module):
    """Angle-embedded variational circuit with RY/RZ layers and ring CNOT entanglement.

    forward: x in R^{n_qubits} (features, expected roughly in [-1,1])
             -> z in R^{n_qubits} (Pauli-Z expectations, in [-1,1])
    Trainable parameters: 2 * n_layers * n_qubits rotation angles.
    """

    def __init__(self, n_qubits: int = 6, n_layers: int = 3):
        super().__init__()
        self.nq, self.nl = n_qubits, n_layers
        self.theta = nn.Parameter(0.1 * torch.randn(n_layers, 2, n_qubits))
        self.register_buffer("_cnot_ring", self._build_cnot_ring(), persistent=False)
        zs = []
        for q in range(n_qubits):
            ops = [torch.eye(2)] * n_qubits
            ops[q] = torch.diag(torch.tensor([1.0, -1.0]))
            zs.append(_kron_all(ops))
        self.register_buffer("_z_ops", torch.stack(zs).to(torch.complex64), persistent=False)

    def _build_cnot_ring(self) -> torch.Tensor:
        dim = 2 ** self.nq
        U = torch.eye(dim)
        for c in range(self.nq):
            t = (c + 1) % self.nq
            P = torch.zeros(dim, dim)
            for b in range(dim):
                bits = [(b >> (self.nq - 1 - i)) & 1 for i in range(self.nq)]
                if bits[c] == 1:
                    bits[t] ^= 1
                nb = 0
                for bit in bits:
                    nb = (nb << 1) | bit
                P[nb, b] = 1.0
            U = P @ U
        return U.to(torch.complex64)

    @staticmethod
    def _ry(a):  # (B,) -> (B,2,2) complex
        c, s = torch.cos(a / 2), torch.sin(a / 2)
        return torch.stack(
            [torch.stack([c, -s], -1), torch.stack([s, c], -1)], -2
        ).to(torch.complex64)

    @staticmethod
    def _rz(a):
        e = torch.exp(-0.5j * a.to(torch.complex64))
        z = torch.zeros_like(e)
        return torch.stack(
            [torch.stack([e, z], -1), torch.stack([z, e.conj()], -1)], -2
        )

    def _apply_single_qubit(self, state, gates):
        """state: (B, 2^nq) complex; gates: (B, nq, 2, 2). Applies gate q to qubit q."""
        B = state.shape[0]
        for q in range(self.nq):
            s = state.reshape(B, 2 ** q, 2, 2 ** (self.nq - q - 1))
            s = torch.einsum("bij,bajc->baic", gates[:, q], s)
            state = s.reshape(B, -1)
        return state

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        B = x.shape[0]
        state = torch.zeros(B, 2 ** self.nq, dtype=torch.complex64, device=x.device)
        state[:, 0] = 1.0
        # angle embedding: RY(pi * x_q) per qubit
        emb = torch.stack([self._ry(math.pi * x[:, q]) for q in range(self.nq)], dim=1)
        state = self._apply_single_qubit(state, emb)
        for layer in range(self.nl):
            ry = torch.stack(
                [self._ry(self.theta[layer, 0, q].expand(B)) for q in range(self.nq)], 1
            )
            rz = torch.stack(
                [self._rz(self.theta[layer, 1, q].expand(B)) for q in range(self.nq)], 1
            )
            fused = torch.matmul(rz, ry)  # RZ·RY applied as one 2x2 per qubit
            state = self._apply_single_qubit(state, fused)
            state = state @ self._cnot_ring.T
        # <Z_q> for each qubit
        z = torch.stack(
            [torch.einsum("bi,ij,bj->b", state.conj(), self._z_ops[q], state).real
             for q in range(self.nq)], dim=1
        )
        return z


# ------------------------------ architectures ------------------------------ #

class ActorCritic(nn.Module):
    """Common interface: forward(obs) -> (logits [B, n_nodes, n_cap_levels], value [B])."""

    def __init__(self, core: nn.Module, core_out: int, n_nodes: int, n_levels: int, head_width: int):
        super().__init__()
        self.core = core
        self.pi = nn.Sequential(
            nn.Linear(core_out, head_width), nn.Tanh(),
            nn.Linear(head_width, n_nodes * n_levels),
        )
        self.v = nn.Sequential(
            nn.Linear(core_out, head_width), nn.Tanh(), nn.Linear(head_width, 1)
        )
        self.n_nodes, self.n_levels = n_nodes, n_levels

    def forward(self, obs):
        h = self.core(obs)
        logits = self.pi(h).view(-1, self.n_nodes, self.n_levels)
        return logits, self.v(h).squeeze(-1)


def _mlp_core(obs_dim, width, out_dim):
    return nn.Sequential(nn.Linear(obs_dim, width), nn.Tanh(), nn.Linear(width, out_dim), nn.Tanh())


class HybridCore(nn.Module):
    """encoder (obs -> n_qubits features in [-1,1]) -> PQC -> decoder."""

    def __init__(self, obs_dim, n_qubits, n_layers, dec_width):
        super().__init__()
        self.enc = nn.Sequential(nn.Linear(obs_dim, n_qubits), nn.Tanh())
        self.pqc = PQC(n_qubits, n_layers)
        self.dec = nn.Sequential(nn.Linear(n_qubits, dec_width), nn.Tanh())
        self.out_dim = dec_width

    def forward(self, x):
        return self.dec(self.pqc(self.enc(x)))


class AblatedCore(nn.Module):
    """Same encoder/decoder; PQC replaced by a classical block with ~equal parameter count.

    The PQC has 2*L*nq parameters and maps nq -> nq with tanh-like bounded output;
    we mimic it with a bounded residual block whose parameter count is trimmed to match.
    """

    def __init__(self, obs_dim, n_qubits, n_layers, dec_width):
        super().__init__()
        self.enc = nn.Sequential(nn.Linear(obs_dim, n_qubits), nn.Tanh())
        pqc_params = 2 * n_layers * n_qubits
        # diagonal-ish block: per-unit scales+biases stacked to match count exactly
        n_units = pqc_params // (2 * n_qubits)          # = n_layers
        self.scales = nn.Parameter(0.1 * torch.randn(n_units, n_qubits))
        self.biases = nn.Parameter(0.1 * torch.randn(n_units, n_qubits))
        self.dec = nn.Sequential(nn.Linear(n_qubits, dec_width), nn.Tanh())
        self.out_dim = dec_width

    def forward(self, x):
        h = self.enc(x)
        for i in range(self.scales.shape[0]):
            h = torch.tanh(h * (1 + self.scales[i]) + self.biases[i])
        return self.dec(h)


# --------------------------- parameter matching ---------------------------- #

def count_params(m: nn.Module) -> int:
    return sum(p.numel() for p in m.parameters() if p.requires_grad)


def build_policy(kind: str, obs_dim: int, n_nodes: int, n_levels: int,
                 budget: int = 5000, n_qubits: int = 6, n_layers: int = 3) -> ActorCritic:
    """Construct a policy of the requested kind, width-tuned to <= `budget` params
    and as close to it as possible (so all arms are size-matched from above)."""

    def make(kind, head_w, core_w):
        if kind == "classical":
            core = _mlp_core(obs_dim, core_w, core_w)
            return ActorCritic(core, core_w, n_nodes, n_levels, head_w)
        if kind == "hybrid":
            core = HybridCore(obs_dim, n_qubits, n_layers, core_w)
            return ActorCritic(core, core.out_dim, n_nodes, n_levels, head_w)
        if kind == "ablated":
            core = AblatedCore(obs_dim, n_qubits, n_layers, core_w)
            return ActorCritic(core, core.out_dim, n_nodes, n_levels, head_w)
        raise ValueError(kind)

    best = None
    for core_w in range(2, 64):
        for head_w in range(2, 64):
            m = make(kind, head_w, core_w)
            n = count_params(m)
            if n <= budget and (best is None or n > best[0]):
                best = (n, core_w, head_w)
    n, core_w, head_w = best
    model = make(kind, head_w, core_w)
    model.meta = dict(kind=kind, n_params=count_params(model), core_w=core_w, head_w=head_w)
    return model
