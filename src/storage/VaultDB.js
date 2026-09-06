/**
 * VaultDB - Tier 3 Persistent Storage Layer
 * Provides encrypted, versioned, and replicated data storage
 */

export class VaultDB {
    constructor(dbName = 'sovereign-vault', version = 1) {
        this.dbName = dbName;
        this.version = version;
        this.db = null;
        this.encryptionKey = null;
        this.storeNames = [
            'documents',
            'keys',
            'metadata',
            'replication-log',
            'vault-state'
        ];
        this.pendingWrites = new Map();
        this.replicationQueue = [];
        this.listeners = new Map();
    }

    /**
     * Initialize the database
     */
    async open() {
        return new Promise((resolve, reject) => {
            const request = indexedDB.open(this.dbName, this.version);

            request.onerror = () => {
                reject(new Error(`Failed to open VaultDB: ${request.error?.message}`));
            };

            request.onsuccess = () => {
                this.db = request.result;
                resolve(this);
            };

            request.onupgradeneeded = (event) => {
                const db = event.target.result;

                // Create object stores
                this.storeNames.forEach(storeName => {
                    if (!db.objectStoreNames.contains(storeName)) {
                        let store;
                        if (storeName === 'documents') {
                            store = db.createObjectStore(storeName, { keyPath: 'id' });
                            store.createIndex('type', 'type', { unique: false });
                            store.createIndex('createdAt', 'createdAt', { unique: false });
                            store.createIndex('updatedAt', 'updatedAt', { unique: false });
                            store.createIndex('tags', 'tags', { unique: false, multiEntry: true });
                        } else if (storeName === 'keys') {
                            store = db.createObjectStore(storeName, { keyPath: 'keyId' });
                            store.createIndex('type', 'type', { unique: false });
                        } else if (storeName === 'replication-log') {
                            store = db.createObjectStore(storeName, { keyPath: 'sequence' });
                            store.createIndex('timestamp', 'timestamp', { unique: false });
                        } else if (storeName === 'vault-state') {
                            db.createObjectStore(storeName, { keyPath: 'key' });
                        } else {
                            db.createObjectStore(storeName, { keyPath: 'id' });
                        }
                    }
                });
            };
        });
    }

    /**
     * Generate encryption key (simplified - in production use WebCrypto)
     */
    async generateEncryptionKey(password) {
        const encoder = new TextEncoder();
        const data = encoder.encode(password + this.dbName);
        const hashBuffer = await crypto.subtle.digest('SHA-256', data);
        this.encryptionKey = new Uint8Array(hashBuffer);
        return this.encryptionKey;
    }

    /**
     * Encrypt data before storage
     */
    async encrypt(data) {
        if (!this.encryptionKey) {
            throw new Error('Encryption key not set. Call generateEncryptionKey first.');
        }

        const encoder = new TextEncoder();
        const jsonData = JSON.stringify(data);
        const dataBuffer = encoder.encode(jsonData);

        // Simplified XOR encryption (in production use AES-GCM)
        const encrypted = new Uint8Array(dataBuffer.length);
        for (let i = 0; i < dataBuffer.length; i++) {
            encrypted[i] = dataBuffer[i] ^ this.encryptionKey[i % this.encryptionKey.length];
        }

        return encrypted;
    }

    /**
     * Decrypt data after retrieval
     */
    async decrypt(encryptedData) {
        if (!this.encryptionKey) {
            throw new Error('Encryption key not set. Call generateEncryptionKey first.');
        }

        // Simplified XOR decryption
        const decrypted = new Uint8Array(encryptedData.length);
        for (let i = 0; i < encryptedData.length; i++) {
            decrypted[i] = encryptedData[i] ^ this.encryptionKey[i % this.encryptionKey.length];
        }

        const decoder = new TextDecoder();
        const jsonStr = decoder.decode(decrypted);
        return JSON.parse(jsonStr);
    }

    /**
     * Store a document
     */
    async put(collection, doc) {
        if (!this.db) throw new Error('Database not opened');

        const now = Date.now();
        const document = {
            ...doc,
            createdAt: doc.createdAt || now,
            updatedAt: now,
            _version: doc._version ? doc._version + 1 : 1
        };

        // Encrypt if sensitive
        if (doc._encrypted) {
            document.data = await this.encrypt(doc.data);
        }

        return new Promise((resolve, reject) => {
            const tx = this.db.transaction(collection, 'readwrite');
            const store = tx.objectStore(collection);
            const request = store.put(document);

            request.onsuccess = () => {
                this.notifyListeners(collection, 'put', document);
                this.logReplication(collection, 'put', document);
                resolve(document);
            };

            request.onerror = () => reject(request.error);
        });
    }

    /**
     * Get a document by ID
     */
    async get(collection, id) {
        if (!this.db) throw new Error('Database not opened');

        return new Promise(async (resolve, reject) => {
            const tx = this.db.transaction(collection, 'readonly');
            const store = tx.objectStore(collection);
            const request = store.get(id);

            request.onsuccess = async () => {
                let doc = request.result;
                if (doc && doc._encrypted && doc.data) {
                    try {
                        doc.data = await this.decrypt(doc.data);
                    } catch (e) {
                        reject(new Error('Decryption failed'));
                        return;
                    }
                }
                resolve(doc || null);
            };

            request.onerror = () => reject(request.error);
        });
    }

    /**
     * Query documents with filters
     */
    async query(collection, options = {}) {
        if (!this.db) throw new Error('Database not opened');

        return new Promise(async (resolve, reject) => {
            const tx = this.db.transaction(collection, 'readonly');
            const store = tx.objectStore(collection);
            const index = options.index ? store.index(options.index) : store;
            
            const results = [];
            const request = index.openCursor(options.range);

            request.onsuccess = async (event) => {
                const cursor = event.target.result;
                if (cursor) {
                    let doc = cursor.value;
                    
                    // Apply filters
                    let matches = true;
                    if (options.filter) {
                        matches = Object.keys(options.filter).every(key => {
                            return doc[key] === options.filter[key];
                        });
                    }

                    if (matches) {
                        // Decrypt if needed
                        if (doc && doc._encrypted && doc.data) {
                            try {
                                doc.data = await this.decrypt(doc.data);
                            } catch (e) {
                                // Skip failed decryptions
                            }
                        }
                        results.push(doc);
                    }
                    
                    cursor.continue();
                } else {
                    resolve(results);
                }
            };

            request.onerror = () => reject(request.error);
        });
    }

    /**
     * Delete a document
     */
    async delete(collection, id) {
        if (!this.db) throw new Error('Database not opened');

        return new Promise((resolve, reject) => {
            const tx = this.db.transaction(collection, 'readwrite');
            const store = tx.objectStore(collection);
            const request = store.delete(id);

            request.onsuccess = () => {
                this.notifyListeners(collection, 'delete', { id });
                this.logReplication(collection, 'delete', { id });
                resolve(true);
            };

            request.onerror = () => reject(request.error);
        });
    }

    /**
     * Log operation for replication
     */
    logReplication(collection, operation, data) {
        if (!this.db) return;

        const entry = {
            sequence: Date.now() + Math.random(),
            collection,
            operation,
            data: { id: data.id || data.keyId },
            timestamp: Date.now(),
            synced: false
        };

        const tx = this.db.transaction('replication-log', 'readwrite');
        tx.objectStore('replication-log').put(entry);
        this.replicationQueue.push(entry);
    }

    /**
     * Get unsynced replication entries
     */
    async getUnsyncedEntries() {
        return new Promise((resolve, reject) => {
            const results = [];
            const tx = this.db.transaction('replication-log', 'readonly');
            const store = tx.objectStore('replication-log');
            const index = store.index('timestamp');
            const request = index.openCursor(IDBKeyRange.only(false));

            request.onsuccess = (event) => {
                const cursor = event.target.result;
                if (cursor) {
                    if (!cursor.value.synced) {
                        results.push(cursor.value);
                    }
                    cursor.continue();
                } else {
                    resolve(results);
                }
            };

            request.onerror = () => reject(request.error);
        });
    }

    /**
     * Mark entries as synced
     */
    async markSynced(sequences) {
        return new Promise((resolve, reject) => {
            const tx = this.db.transaction('replication-log', 'readwrite');
            const store = tx.objectStore('replication-log');

            sequences.forEach(seq => {
                const getRequest = store.get(seq);
                getRequest.onsuccess = () => {
                    const entry = getRequest.result;
                    if (entry) {
                        entry.synced = true;
                        store.put(entry);
                    }
                };
            });

            tx.oncomplete = () => resolve(true);
            tx.onerror = () => reject(tx.error);
        });
    }

    /**
     * Subscribe to collection changes
     */
    subscribe(collection, callback) {
        if (!this.listeners.has(collection)) {
            this.listeners.set(collection, new Set());
        }
        this.listeners.get(collection).add(callback);

        return () => {
            const set = this.listeners.get(collection);
            if (set) set.delete(callback);
        };
    }

    /**
     * Notify listeners of changes
     */
    notifyListeners(collection, operation, data) {
        const set = this.listeners.get(collection);
        if (set) {
            set.forEach(callback => {
                try {
                    callback({ operation, data, timestamp: Date.now() });
                } catch (e) {
                    console.error('Listener error:', e);
                }
            });
        }
    }

    /**
     * Export vault data
     */
    async exportVault() {
        const exportData = {};
        
        for (const storeName of this.storeNames) {
            exportData[storeName] = await this.query(storeName);
        }

        return exportData;
    }

    /**
     * Import vault data
     */
    async importVault(data) {
        for (const [storeName, docs] of Object.entries(data)) {
            if (this.storeNames.includes(storeName) && Array.isArray(docs)) {
                for (const doc of docs) {
                    await this.put(storeName, doc);
                }
            }
        }
    }

    /**
     * Get database stats
     */
    async getStats() {
        const stats = {};
        
        for (const storeName of this.storeNames) {
            stats[storeName] = await new Promise((resolve) => {
                const tx = this.db.transaction(storeName, 'readonly');
                const store = tx.objectStore(storeName);
                const request = store.count();
                request.onsuccess = () => resolve(request.result);
                request.onerror = () => resolve(0);
            });
        }

        stats.totalDocuments = Object.values(stats).reduce((a, b) => a + b, 0);
        stats.pendingReplication = this.replicationQueue.filter(r => !r.synced).length;

        return stats;
    }

    /**
     * Close the database
     */
    close() {
        if (this.db) {
            this.db.close();
            this.db = null;
        }
    }
}

export default VaultDB;
