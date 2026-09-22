// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title EvidenceAnchor
 * @dev Cryptographically anchors digital evidence hashes to the blockchain
 * for immutable chain of custody and tamper detection in NetraLink.
 */
contract EvidenceAnchor {
    struct EvidenceRecord {
        bytes32 contentHash;
        uint256 timestamp;
        string caseNumber;
        address recordedBy;
    }

    // Mapping from recordId (e.g. SHA-256 string or UUID) to EvidenceRecord
    mapping(string => EvidenceRecord) private _records;
    
    // Ordered list of all anchored record IDs
    string[] private _recordIds;

    address public owner;

    event EvidenceAnchored(
        string indexed recordId,
        bytes32 indexed contentHash,
        string caseNumber,
        uint256 timestamp,
        address indexed recordedBy
    );

    modifier onlyOwner() {
        require(msg.sender == owner, "EvidenceAnchor: caller is not the owner");
        _;
    }

    constructor() {
        owner = msg.sender;
    }

    /**
     * @notice Anchor an evidence hash onto the ledger.
     * @param recordId Unique identifier of the evidence item
     * @param contentHash SHA-256 hash of the evidence content
     * @param caseNumber Case or incident identifier
     */
    function anchorEvidence(
        string calldata recordId,
        bytes32 contentHash,
        string calldata caseNumber
    ) external {
        require(_records[recordId].timestamp == 0, "EvidenceAnchor: record already exists");
        require(contentHash != bytes32(0), "EvidenceAnchor: invalid hash");

        _records[recordId] = EvidenceRecord({
            contentHash: contentHash,
            timestamp: block.timestamp,
            caseNumber: caseNumber,
            recordedBy: msg.sender
        });

        _recordIds.push(recordId);

        emit EvidenceAnchored(
            recordId,
            contentHash,
            caseNumber,
            block.timestamp,
            msg.sender
        );
    }

    /**
     * @notice Verify whether an evidence hash matches the on-chain anchor.
     */
    function verifyEvidence(
        string calldata recordId,
        bytes32 contentHash
    ) external view returns (bool isValid, uint256 timestamp, string memory caseNumber) {
        EvidenceRecord memory rec = _records[recordId];
        if (rec.timestamp == 0) {
            return (false, 0, "");
        }
        return (rec.contentHash == contentHash, rec.timestamp, rec.caseNumber);
    }

    function totalAnchored() external view returns (uint256) {
        return _recordIds.length;
    }
}
