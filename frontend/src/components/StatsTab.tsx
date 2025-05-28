import React, { useState } from 'react';
import {
  Box,
  TextField,
  Button,
  Typography,
  Paper,
  CircularProgress,
  Alert,
} from '@mui/material';

interface PlayerStats {
  champion: string;
  position: string;
  win: boolean;
  kills: number;
  deaths: number;
  assists: number;
  kda: number;
  damage_dealt: number;
  damage_taken: number;
  gold_earned: number;
  vision_score: number;
  time_ccing_others: number;
}

const StatsTab: React.FC = () => {
  const [summonerName, setSummonerName] = useState('');
  const [stats, setStats] = useState<PlayerStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSearch = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          summoner_name: 'aphae#raph',
          region: 'na1',
          match_count: 5
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to fetch stats');
      }

      const data = await response.json();
      setStats(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Player Statistics
      </Typography>

      <Box mb={3}>
        <TextField
          label="Summoner Name"
          value={summonerName}
          onChange={(e) => setSummonerName(e.target.value)}
          fullWidth
          margin="normal"
        />
        <Button
          variant="contained"
          onClick={handleSearch}
          disabled={loading}
          sx={{ mt: 2 }}
        >
          {loading ? <CircularProgress size={24} /> : 'Search'}
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {stats && (
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Match Statistics
          </Typography>
          <Box display="grid" gridTemplateColumns="repeat(2, 1fr)" gap={2}>
            <Typography>
              Champion: {stats.champion}
            </Typography>
            <Typography>
              Position: {stats.position}
            </Typography>
            <Typography>
              Result: {stats.win ? 'Victory' : 'Defeat'}
            </Typography>
            <Typography>
              KDA: {stats.kills}/{stats.deaths}/{stats.assists} ({stats.kda.toFixed(2)})
            </Typography>
            <Typography>
              Damage Dealt: {stats.damage_dealt.toLocaleString()}
            </Typography>
            <Typography>
              Damage Taken: {stats.damage_taken.toLocaleString()}
            </Typography>
            <Typography>
              Gold Earned: {stats.gold_earned.toLocaleString()}
            </Typography>
            <Typography>
              Vision Score: {stats.vision_score}
            </Typography>
            <Typography>
              Time CCing Others: {stats.time_ccing_others}s
            </Typography>
          </Box>
        </Paper>
      )}
    </Box>
  );
};

export default StatsTab; 