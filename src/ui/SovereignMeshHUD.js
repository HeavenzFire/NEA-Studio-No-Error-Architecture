/**
 * SovereignMeshHUD - Tier 3 Visual Overlay Layer
 * Provides real-time visual feedback for the mesh network state
 */

export class SovereignMeshHUD {
    constructor(canvasId = 'mesh-hud') {
        this.canvas = document.getElementById(canvasId);
        this.ctx = this.canvas?.getContext('2d');
        this.nodes = new Map();
        this.connections = [];
        this.messages = [];
        this.stats = {
            totalNodes: 0,
            activeConnections: 0,
            messagesProcessed: 0,
            latency: 0
        };
        this.animationFrame = null;
        this.visible = true;
        
        if (this.canvas) {
            this.resize();
            window.addEventListener('resize', () => this.resize());
        }
    }

    resize() {
        if (!this.canvas) return;
        this.canvas.width = window.innerWidth;
        this.canvas.height = window.innerHeight;
    }

    /**
     * Register a node in the HUD
     */
    registerNode(nodeId, position = { x: 0, y: 0 }) {
        this.nodes.set(nodeId, {
            id: nodeId,
            x: position.x || Math.random() * (this.canvas?.width || 800),
            y: position.y || Math.random() * (this.canvas?.height || 600),
            vx: (Math.random() - 0.5) * 0.5,
            vy: (Math.random() - 0.5) * 0.5,
            status: 'active',
            lastSeen: Date.now(),
            dataPackets: 0
        });
        this.stats.totalNodes = this.nodes.size;
    }

    /**
     * Update node status
     */
    updateNodeStatus(nodeId, status, data = {}) {
        const node = this.nodes.get(nodeId);
        if (node) {
            node.status = status;
            node.lastSeen = Date.now();
            Object.assign(node, data);
        }
    }

    /**
     * Add a connection between nodes
     */
    addConnection(fromId, toId, strength = 1) {
        const connKey = `${fromId}-${toId}`;
        const exists = this.connections.some(c => 
            (c.from === fromId && c.to === toId) || 
            (c.from === toId && c.to === fromId)
        );
        
        if (!exists) {
            this.connections.push({ from: fromId, to: toId, strength, age: 0 });
            this.stats.activeConnections = this.connections.length;
        }
    }

    /**
     * Remove a connection
     */
    removeConnection(fromId, toId) {
        this.connections = this.connections.filter(c => 
            !((c.from === fromId && c.to === toId) || 
              (c.from === toId && c.to === fromId))
        );
        this.stats.activeConnections = this.connections.length;
    }

    /**
     * Log a message in the HUD
     */
    logMessage(message, type = 'info') {
        this.messages.push({
            text: message,
            type,
            timestamp: Date.now(),
            life: 5000
        });
        this.stats.messagesProcessed++;
        
        // Keep only recent messages
        if (this.messages.length > 50) {
            this.messages.shift();
        }
    }

    /**
     * Update latency stats
     */
    updateLatency(latency) {
        this.stats.latency = latency;
    }

    /**
     * Render the HUD
     */
    render() {
        if (!this.visible || !this.ctx) return;

        const ctx = this.ctx;
        const width = this.canvas.width;
        const height = this.canvas.height;

        // Clear with fade effect
        ctx.fillStyle = 'rgba(10, 15, 30, 0.2)';
        ctx.fillRect(0, 0, width, height);

        // Draw connections
        this.connections.forEach(conn => {
            const fromNode = this.nodes.get(conn.from);
            const toNode = this.nodes.get(conn.to);
            
            if (fromNode && toNode) {
                conn.age++;
                const alpha = Math.min(1, conn.age / 100) * conn.strength;
                
                ctx.beginPath();
                ctx.moveTo(fromNode.x, fromNode.y);
                ctx.lineTo(toNode.x, toNode.y);
                ctx.strokeStyle = `rgba(0, 255, 150, ${alpha})`;
                ctx.lineWidth = 1 + conn.strength;
                ctx.stroke();
            }
        });

        // Draw nodes
        this.nodes.forEach(node => {
            // Update position
            node.x += node.vx;
            node.y += node.vy;
            
            // Bounce off walls
            if (node.x < 0 || node.x > width) node.vx *= -1;
            if (node.y < 0 || node.y > height) node.vy *= -1;
            
            // Clamp position
            node.x = Math.max(0, Math.min(width, node.x));
            node.y = Math.max(0, Math.min(height, node.y));

            // Node glow based on status
            const colors = {
                active: '#00ff96',
                syncing: '#ffd700',
                offline: '#ff4444',
                processing: '#00bfff'
            };
            
            const color = colors[node.status] || colors.active;
            
            // Outer glow
            const gradient = ctx.createRadialGradient(node.x, node.y, 0, node.x, node.y, 20);
            gradient.addColorStop(0, color);
            gradient.addColorStop(1, 'transparent');
            ctx.fillStyle = gradient;
            ctx.beginPath();
            ctx.arc(node.x, node.y, 20, 0, Math.PI * 2);
            ctx.fill();

            // Core
            ctx.fillStyle = color;
            ctx.beginPath();
            ctx.arc(node.x, node.y, 4, 0, Math.PI * 2);
            ctx.fill();

            // Node ID label
            ctx.fillStyle = 'rgba(255, 255, 255, 0.7)';
            ctx.font = '10px monospace';
            ctx.fillText(node.id.substring(0, 8), node.x + 8, node.y - 8);
        });

        // Draw stats panel
        this.renderStatsPanel(ctx);

        // Draw message log
        this.renderMessageLog(ctx);

        // Continue animation
        this.animationFrame = requestAnimationFrame(() => this.render());
    }

    renderStatsPanel(ctx) {
        const panelX = 10;
        const panelY = 10;
        const panelWidth = 220;
        const panelHeight = 120;

        // Background
        ctx.fillStyle = 'rgba(0, 20, 40, 0.8)';
        ctx.fillRect(panelX, panelY, panelWidth, panelHeight);
        
        // Border
        ctx.strokeStyle = '#00ff96';
        ctx.lineWidth = 1;
        ctx.strokeRect(panelX, panelY, panelWidth, panelHeight);

        // Title
        ctx.fillStyle = '#00ff96';
        ctx.font = 'bold 14px monospace';
        ctx.fillText('SOVEREIGN MESH HUD', panelX + 10, panelY + 25);

        // Stats
        ctx.fillStyle = '#ffffff';
        ctx.font = '11px monospace';
        const stats = [
            `Nodes: ${this.stats.totalNodes}`,
            `Connections: ${this.stats.activeConnections}`,
            `Messages: ${this.stats.messagesProcessed}`,
            `Latency: ${this.stats.latency}ms`
        ];
        
        stats.forEach((stat, i) => {
            ctx.fillText(stat, panelX + 10, panelY + 50 + (i * 20));
        });
    }

    renderMessageLog(ctx) {
        const panelX = 10;
        const panelY = this.canvas.height - 150;
        const panelWidth = 400;
        const panelHeight = 140;

        // Background
        ctx.fillStyle = 'rgba(0, 20, 40, 0.8)';
        ctx.fillRect(panelX, panelY, panelWidth, panelHeight);
        
        // Border
        ctx.strokeStyle = '#00bfff';
        ctx.lineWidth = 1;
        ctx.strokeRect(panelX, panelY, panelWidth, panelHeight);

        // Title
        ctx.fillStyle = '#00bfff';
        ctx.font = 'bold 12px monospace';
        ctx.fillText('MESSAGE LOG', panelX + 10, panelY + 20);

        // Messages (newest first, limited display)
        ctx.font = '10px monospace';
        const recentMessages = this.messages.slice(-6).reverse();
        
        recentMessages.forEach((msg, i) => {
            const colors = {
                info: '#ffffff',
                success: '#00ff96',
                warning: '#ffd700',
                error: '#ff4444'
            };
            
            ctx.fillStyle = colors[msg.type] || colors.info;
            const timeStr = new Date(msg.timestamp).toLocaleTimeString();
            ctx.fillText(`[${timeStr}] ${msg.text}`, panelX + 10, panelY + 45 + (i * 18));
        });
    }

    /**
     * Start the HUD rendering
     */
    start() {
        if (this.animationFrame) return;
        this.visible = true;
        this.render();
        this.logMessage('SovereignMeshHUD initialized', 'success');
    }

    /**
     * Stop the HUD rendering
     */
    stop() {
        if (this.animationFrame) {
            cancelAnimationFrame(this.animationFrame);
            this.animationFrame = null;
        }
    }

    /**
     * Toggle visibility
     */
    toggle() {
        this.visible = !this.visible;
        if (this.visible && !this.animationFrame) {
            this.render();
        }
    }

    /**
     * Get current stats
     */
    getStats() {
        return { ...this.stats };
    }

    /**
     * Clear all data
     */
    clear() {
        this.nodes.clear();
        this.connections = [];
        this.messages = [];
        this.stats = {
            totalNodes: 0,
            activeConnections: 0,
            messagesProcessed: 0,
            latency: 0
        };
    }
}

export default SovereignMeshHUD;
