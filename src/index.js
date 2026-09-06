/**
 * Sovereign Mesh Network - Tier 3 Integration
 * Main entry point that wires together HUD, VaultDB, and mesh layers
 */

import { SovereignMeshHUD } from './ui/SovereignMeshHUD.js';
import { VaultDB } from './storage/VaultDB.js';

/**
 * SovereignMesh - Main coordinator for Tier 3
 */
export class SovereignMesh {
    constructor(options = {}) {
        this.nodeId = options.nodeId || this.generateNodeId();
        this.nodeName = options.nodeName || `Node-${this.nodeId.substring(0, 6)}`;
        
        // Initialize components
        this.hud = null;
        this.vault = null;
        
        // Mesh state
        this.peers = new Map();
        this.channels = new Map();
        this.isConnected = false;
        
        // Configuration
        this.config = {
            autoConnect: options.autoConnect ?? true,
            encryptionEnabled: options.encryptionEnabled ?? true,
            hudEnabled: options.hudEnabled ?? true,
            replicationInterval: options.replicationInterval ?? 5000
        };
        
        this.replicationTimer = null;
    }

    /**
     * Generate a unique node ID
     */
    generateNodeId() {
        return 'node-' + crypto.randomUUID();
    }

    /**
     * Initialize the Sovereign Mesh
     */
    async initialize() {
        console.log(`[${this.nodeName}] Initializing Sovereign Mesh...`);
        
        // Initialize HUD
        if (this.config.hudEnabled) {
            this.hud = new SovereignMeshHUD('mesh-hud');
            this.hud.registerNode(this.nodeId);
            this.hud.start();
            this.hud.logMessage(`Node ${this.nodeName} initialized`, 'success');
        }
        
        // Initialize VaultDB
        this.vault = new VaultDB(`sovereign-vault-${this.nodeId}`);
        await this.vault.open();
        
        if (this.config.encryptionEnabled) {
            const defaultPassword = 'sovereign-default-key-' + this.nodeId;
            await this.vault.generateEncryptionKey(defaultPassword);
        }
        
        // Store node identity
        await this.vault.put('documents', {
            id: 'self-identity',
            type: 'identity',
            nodeId: this.nodeId,
            nodeName: this.nodeName,
            createdAt: Date.now()
        });
        
        if (this.hud) {
            this.hud.logMessage('VaultDB initialized with encryption', 'success');
        }
        
        console.log(`[${this.nodeName}] Initialization complete`);
        return this;
    }

    /**
     * Connect to the mesh network
     */
    async connect() {
        if (this.isConnected) return;
        
        console.log(`[${this.nodeName}] Connecting to mesh...`);
        
        // Simulate connection process
        await this.simulateConnection();
        
        this.isConnected = true;
        
        if (this.hud) {
            this.hud.updateNodeStatus(this.nodeId, 'active');
            this.hud.logMessage('Connected to mesh network', 'success');
        }
        
        // Start replication cycle
        this.startReplication();
        
        return this;
    }

    /**
     * Simulate connecting to peers
     */
    async simulateConnection() {
        return new Promise(resolve => {
            setTimeout(() => {
                // Create some simulated peer nodes
                const peerCount = Math.floor(Math.random() * 4) + 2;
                
                for (let i = 0; i < peerCount; i++) {
                    const peerId = `peer-${crypto.randomUUID().substring(0, 8)}`;
                    this.peers.set(peerId, {
                        id: peerId,
                        status: 'connected',
                        latency: Math.floor(Math.random() * 100) + 10,
                        lastSeen: Date.now()
                    });
                    
                    if (this.hud) {
                        this.hud.registerNode(peerId);
                        this.hud.addConnection(this.nodeId, peerId, 0.5 + Math.random() * 0.5);
                    }
                }
                
                resolve();
            }, 500);
        });
    }

    /**
     * Disconnect from the mesh
     */
    disconnect() {
        this.isConnected = false;
        
        if (this.replicationTimer) {
            clearInterval(this.replicationTimer);
            this.replicationTimer = null;
        }
        
        this.peers.forEach((peer, peerId) => {
            peer.status = 'disconnected';
            if (this.hud) {
                this.hud.updateNodeStatus(peerId, 'offline');
            }
        });
        
        if (this.hud) {
            this.hud.updateNodeStatus(this.nodeId, 'offline');
            this.hud.logMessage('Disconnected from mesh', 'warning');
        }
        
        console.log(`[${this.nodeName}] Disconnected from mesh`);
    }

    /**
     * Start replication cycle
     */
    startReplication() {
        this.replicationTimer = setInterval(async () => {
            await this.replicate();
        }, this.config.replicationInterval);
    }

    /**
     * Perform replication with peers
     */
    async replicate() {
        if (!this.isConnected) return;
        
        const unsyncedEntries = await this.vault.getUnsyncedEntries();
        
        if (unsyncedEntries.length > 0) {
            console.log(`[${this.nodeName}] Replicating ${unsyncedEntries.length} entries...`);
            
            // Simulate syncing to peers
            for (const [peerId, peer] of this.peers) {
                if (peer.status === 'connected') {
                    // Simulate replication latency
                    const latency = peer.latency;
                    if (this.hud) {
                        this.hud.updateLatency(latency);
                    }
                    
                    // Mark as synced after "transmission"
                    const sequences = unsyncedEntries.map(e => e.sequence);
                    await this.vault.markSynced(sequences);
                    
                    if (this.hud) {
                        this.hud.logMessage(`Synced with ${peerId.substring(0, 8)}`, 'info');
                    }
                }
            }
        }
    }

    /**
     * Publish data to a channel
     */
    async publish(channelName, data) {
        const message = {
            id: crypto.randomUUID(),
            channel: channelName,
            sender: this.nodeId,
            data: data,
            timestamp: Date.now()
        };
        
        // Store in vault
        await this.vault.put('documents', {
            id: `msg-${message.id}`,
            type: 'message',
            ...message
        });
        
        // Update HUD
        if (this.hud) {
            this.hud.logMessage(`Published to ${channelName}`, 'info');
            this.hud.updateNodeStatus(this.nodeId, 'processing');
            setTimeout(() => this.hud.updateNodeStatus(this.nodeId, 'active'), 500);
        }
        
        return message;
    }

    /**
     * Subscribe to a channel
     */
    subscribe(channelName, callback) {
        if (!this.channels.has(channelName)) {
            this.channels.set(channelName, new Set());
        }
        
        this.channels.get(channelName).add(callback);
        
        if (this.hud) {
            this.hud.logMessage(`Subscribed to ${channelName}`, 'success');
        }
        
        return () => {
            const channel = this.channels.get(channelName);
            if (channel) channel.delete(callback);
        };
    }

    /**
     * Store encrypted data
     */
    async storeSecure(key, data) {
        await this.vault.put('documents', {
            id: `secure-${key}`,
            type: 'secure-data',
            key: key,
            data: data,
            _encrypted: true
        });
        
        if (this.hud) {
            this.hud.logMessage(`Stored encrypted: ${key}`, 'success');
        }
    }

    /**
     * Retrieve encrypted data
     */
    async retrieveSecure(key) {
        const doc = await this.vault.get('documents', `secure-${key}`);
        return doc ? doc.data : null;
    }

    /**
     * Get mesh statistics
     */
    getStats() {
        const hudStats = this.hud?.getStats() || {};
        
        return {
            nodeId: this.nodeId,
            nodeName: this.nodeName,
            isConnected: this.isConnected,
            peerCount: this.peers.size,
            channelCount: this.channels.size,
            ...hudStats
        };
    }

    /**
     * Export all data
     */
    async exportData() {
        return this.vault.exportVault();
    }

    /**
     * Import data
     */
    async importData(data) {
        return this.vault.importVault(data);
    }

    /**
     * Shutdown gracefully
     */
    async shutdown() {
        console.log(`[${this.nodeName}] Shutting down...`);
        
        this.disconnect();
        
        if (this.hud) {
            this.hud.stop();
            this.hud.logMessage('System shutdown', 'warning');
        }
        
        if (this.vault) {
            await this.vault.close();
        }
        
        console.log(`[${this.nodeName}] Shutdown complete`);
    }
}

// Auto-initialize when loaded in browser
if (typeof window !== 'undefined') {
    window.SovereignMesh = SovereignMesh;
    window.SovereignMeshHUD = SovereignMeshHUD;
    window.VaultDB = VaultDB;
}

export default SovereignMesh;
