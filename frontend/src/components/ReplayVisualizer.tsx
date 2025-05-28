import React, { useEffect, useRef, useState } from 'react';
import { Box, Slider, Typography, Paper } from '@mui/material';
import { ProcessedReplay, GameState } from '../types/replay';

interface ReplayVisualizerProps {
    replay: ProcessedReplay;
}

const MAP_WIDTH = 15000;
const MAP_HEIGHT = 15000;
const CANVAS_WIDTH = 800;
const CANVAS_HEIGHT = 800;

const ReplayVisualizer: React.FC<ReplayVisualizerProps> = ({ replay }) => {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const [currentTime, setCurrentTime] = useState(0);
    const [currentState, setCurrentState] = useState<GameState | null>(null);

    useEffect(() => {
        if (!replay.game_states.length) return;
        setCurrentState(replay.game_states[0]);
    }, [replay]);

    useEffect(() => {
        if (!currentState) return;
        drawGameState();
    }, [currentState]);

    const drawGameState = () => {
        const canvas = canvasRef.current;
        if (!canvas || !currentState) return;

        const ctx = canvas.getContext('2d');
        if (!ctx) return;

        // Clear canvas
        ctx.clearRect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT);

        // Draw map background (simplified)
        ctx.fillStyle = '#1a1a1a';
        ctx.fillRect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT);

        // Draw champions
        const drawChampion = (x: number, y: number, team: 'blue' | 'red') => {
            const size = 20;
            ctx.beginPath();
            ctx.arc(x, y, size, 0, Math.PI * 2);
            ctx.fillStyle = team === 'blue' ? '#3498db' : '#e74c3c';
            ctx.fill();
            ctx.strokeStyle = '#fff';
            ctx.stroke();
        };

        // Draw blue team
        Object.entries(currentState.blue_team).forEach(([name, state]) => {
            const x = (state.position.x / MAP_WIDTH) * CANVAS_WIDTH;
            const y = (state.position.y / MAP_HEIGHT) * CANVAS_HEIGHT;
            drawChampion(x, y, 'blue');
        });

        // Draw red team
        Object.entries(currentState.red_team).forEach(([name, state]) => {
            const x = (state.position.x / MAP_WIDTH) * CANVAS_WIDTH;
            const y = (state.position.y / MAP_HEIGHT) * CANVAS_HEIGHT;
            drawChampion(x, y, 'red');
        });
    };

    const handleTimeChange = (_: Event, newValue: number | number[]) => {
        const time = newValue as number;
        setCurrentTime(time);
        
        // Find the closest game state
        const closestState = replay.game_states.reduce((prev, curr) => {
            return Math.abs(curr.timestamp - time) < Math.abs(prev.timestamp - time) ? curr : prev;
        });
        setCurrentState(closestState);
    };

    return (
        <Box sx={{ width: '100%', p: 2 }}>
            <Paper elevation={3} sx={{ p: 2, mb: 2 }}>
                <Typography variant="h6" gutterBottom>
                    Game Time: {Math.floor(currentTime / 60)}:{(currentTime % 60).toString().padStart(2, '0')}
                </Typography>
                <Slider
                    value={currentTime}
                    onChange={handleTimeChange}
                    min={0}
                    max={replay.game_duration}
                    step={1}
                    valueLabelDisplay="auto"
                    valueLabelFormat={(value) => `${Math.floor(value / 60)}:${(value % 60).toString().padStart(2, '0')}`}
                />
            </Paper>
            <Paper elevation={3} sx={{ p: 2 }}>
                <canvas
                    ref={canvasRef}
                    width={CANVAS_WIDTH}
                    height={CANVAS_HEIGHT}
                    style={{ width: '100%', height: 'auto' }}
                />
            </Paper>
        </Box>
    );
};

export default ReplayVisualizer; 