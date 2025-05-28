class ReplayViewer {
    constructor(canvasId, timelineId) {
        this.canvas = document.getElementById(canvasId);
        this.ctx = this.canvas.getContext('2d');
        this.timeline = document.getElementById(timelineId);
        this.currentTime = 0;
        this.gameDuration = 0;
        this.replayData = null;
        this.isPlaying = false;
        this.playbackSpeed = 1;
        
        // Set up event listeners
        this.timeline.addEventListener('input', this.handleTimelineChange.bind(this));
        this.setupKeyboardControls();
    }
    
    async loadReplay(replayId) {
        try {
            const response = await fetch(`/api/replays/${replayId}`);
            if (!response.ok) {
                throw new Error('Failed to load replay data');
            }
            this.replayData = await response.json();
            this.gameDuration = this.replayData.game_duration;
            this.timeline.max = this.gameDuration;
            this.drawMap();
            this.updateGameState(0);
        } catch (error) {
            console.error('Error loading replay:', error);
        }
    }
    
    drawMap() {
        // Load and draw the map image
        const mapImage = new Image();
        mapImage.src = '/static/replay/maps/summoners_rift.svg';
        mapImage.onload = () => {
            this.ctx.drawImage(mapImage, 0, 0, this.canvas.width, this.canvas.height);
        };
    }
    
    async updateGameState(timestamp) {
        try {
            const response = await fetch(`/api/replays/${this.replayData.match_id}/gamestate?timestamp=${timestamp}`);
            if (!response.ok) {
                throw new Error('Failed to load game state');
            }
            const gameState = await response.json();
            this.drawGameState(gameState);
        } catch (error) {
            console.error('Error updating game state:', error);
        }
    }
    
    drawGameState(gameState) {
        // Clear the canvas
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Draw the map
        this.drawMap();
        
        // Draw champion positions
        for (const [puuid, state] of Object.entries(gameState.champion_states)) {
            const participant = this.replayData.participants.find(p => p.puuid === puuid);
            if (participant) {
                this.drawChampion(participant, state);
            }
        }
        
        // Draw recent events
        for (const event of gameState.recent_events) {
            this.drawEvent(event);
        }
    }
    
    drawChampion(participant, state) {
        const { x, y } = state.position;
        const scale = this.canvas.width / 15000; // Map is 15000x15000
        
        // Draw champion icon
        const icon = new Image();
        icon.src = `/static/replay/champions/${participant.champion_id}.png`;
        icon.onload = () => {
            this.ctx.drawImage(icon, x * scale - 25, y * scale - 25, 50, 50);
        };
        
        // Draw team color indicator
        this.ctx.beginPath();
        this.ctx.arc(x * scale, y * scale, 30, 0, Math.PI * 2);
        this.ctx.fillStyle = participant.team_id === 100 ? '#0000FF' : '#FF0000';
        this.ctx.fill();
    }
    
    drawEvent(event) {
        const scale = this.canvas.width / 15000;
        
        if (event.type === 'OBJECTIVE_TAKEN') {
            const { x, y } = event.position;
            this.ctx.beginPath();
            this.ctx.arc(x * scale, y * scale, 40, 0, Math.PI * 2);
            this.ctx.fillStyle = event.team_id === 100 ? '#0000FF' : '#FF0000';
            this.ctx.fill();
        }
    }
    
    handleTimelineChange(event) {
        const timestamp = parseInt(event.target.value);
        this.currentTime = timestamp;
        this.updateGameState(timestamp);
    }
    
    setupKeyboardControls() {
        document.addEventListener('keydown', (event) => {
            switch (event.key) {
                case ' ':
                    this.togglePlayback();
                    break;
                case 'ArrowLeft':
                    this.seek(-5000);
                    break;
                case 'ArrowRight':
                    this.seek(5000);
                    break;
                case '+':
                    this.setPlaybackSpeed(this.playbackSpeed * 2);
                    break;
                case '-':
                    this.setPlaybackSpeed(this.playbackSpeed / 2);
                    break;
            }
        });
    }
    
    togglePlayback() {
        this.isPlaying = !this.isPlaying;
        if (this.isPlaying) {
            this.startPlayback();
        } else {
            this.stopPlayback();
        }
    }
    
    startPlayback() {
        this.playbackInterval = setInterval(() => {
            this.currentTime += 1000 * this.playbackSpeed;
            if (this.currentTime >= this.gameDuration) {
                this.stopPlayback();
                return;
            }
            this.timeline.value = this.currentTime;
            this.updateGameState(this.currentTime);
        }, 1000);
    }
    
    stopPlayback() {
        clearInterval(this.playbackInterval);
        this.isPlaying = false;
    }
    
    seek(offset) {
        this.currentTime = Math.max(0, Math.min(this.gameDuration, this.currentTime + offset));
        this.timeline.value = this.currentTime;
        this.updateGameState(this.currentTime);
    }
    
    setPlaybackSpeed(speed) {
        this.playbackSpeed = Math.max(0.25, Math.min(4, speed));
        if (this.isPlaying) {
            this.stopPlayback();
            this.startPlayback();
        }
    }
}

// Initialize the replay viewer when the page loads
document.addEventListener('DOMContentLoaded', () => {
    const viewer = new ReplayViewer('replay-canvas', 'timeline');
    const replayId = document.getElementById('replay-data').dataset.replayId;
    viewer.loadReplay(replayId);
}); 