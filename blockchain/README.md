# NetraLink Blockchain Anchoring Module

Phase 7 optional evidence integrity and blockchain anchoring layer.

## Overview

NetraLink computes cryptographic SHA-256 digests of all investigative artifacts (call detail records, transaction trails, FIR matches) and anchors them onto an EVM-compatible blockchain via the `EvidenceAnchor` smart contract.

## Contents

- **`contracts/EvidenceAnchor.sol`**: Solidity contract providing `anchorEvidence()` and `verifyEvidence()` for tamper detection.
- **`scripts/anchor_evidence.py`**: Python script to compute SHA-256 hashes and submit verification transactions.

## Deployment

1. Compile the contract using Hardhat, Foundry, or Remix:
   ```bash
   npx hardhat compile
   ```
2. Deploy to Ethereum, Polygon, or local testnet:
   ```bash
   python scripts/anchor_evidence.py
   ```
