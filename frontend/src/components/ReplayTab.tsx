import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  List,
  ListItem,
  ListItemText,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  CircularProgress,
  Alert,
  Paper,
  Grid
} from '@mui/material';
import { ReplayListItem, ProcessedReplay } from '../types/replay';
import ReplayVisualizer from './ReplayVisualizer';

const ReplayTab: React.FC = () => {
  const [replays, setReplays] = useState<ReplayListItem[]>([]);
  const [selectedReplay, setSelectedReplay] = useState<ProcessedReplay | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [uploadOpen, setUploadOpen] = useState(false);
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    fetchReplays();
  }, []);

  const fetchReplays = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await fetch('/api/replays');
      if (!response.ok) {
        throw new Error('Failed to fetch replays');
      }
      const data = await response.json();
      setReplays(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handleReplaySelect = async (matchId: string) => {
    try {
      setLoading(true);
      setError(null);
      const response = await fetch(`/api/replays/${matchId}`);
      if (!response.ok) {
        throw new Error('Failed to fetch replay data');
      }
      const data = await response.json();
      setSelectedReplay(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file && file.name.endsWith('.rofl')) {
      setUploadFile(file);
    } else {
      setError('Please select a valid .rofl file');
    }
  };

  const handleUpload = async () => {
    if (!uploadFile) return;

    try {
      setUploading(true);
      setError(null);

      const formData = new FormData();
      formData.append('file', uploadFile);

      const response = await fetch('/api/replays/upload', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Failed to upload replay');
      }

      setUploadOpen(false);
      setUploadFile(null);
      fetchReplays();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setUploading(false);
    }
  };

  return (
    <Box sx={{ p: 2 }}>
      <Grid container spacing={2}>
        <Grid item xs={12} md={4}>
          <Paper elevation={3} sx={{ p: 2, mb: 2 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6">Available Replays</Typography>
              <Button
                variant="contained"
                color="primary"
                onClick={() => setUploadOpen(true)}
              >
                Upload Replay
              </Button>
            </Box>
            {error && (
              <Alert severity="error" sx={{ mb: 2 }}>
                {error}
              </Alert>
            )}
            {loading ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', p: 2 }}>
                <CircularProgress />
              </Box>
            ) : (
              <List>
                {replays.map((replay) => (
                  <ListItem
                    key={replay.match_id}
                    button
                    onClick={() => handleReplaySelect(replay.match_id)}
                    selected={selectedReplay?.match_id === replay.match_id}
                  >
                    <ListItemText
                      primary={`Match ${replay.match_id}`}
                      secondary={`${replay.participant_count} players • ${Math.floor(replay.game_duration / 60)}:${(replay.game_duration % 60).toString().padStart(2, '0')}`}
                    />
                  </ListItem>
                ))}
              </List>
            )}
          </Paper>
        </Grid>
        <Grid item xs={12} md={8}>
          {selectedReplay ? (
            <ReplayVisualizer replay={selectedReplay} />
          ) : (
            <Paper elevation={3} sx={{ p: 2, textAlign: 'center' }}>
              <Typography variant="h6" color="textSecondary">
                Select a replay to view
              </Typography>
            </Paper>
          )}
        </Grid>
      </Grid>

      <Dialog open={uploadOpen} onClose={() => setUploadOpen(false)}>
        <DialogTitle>Upload Replay</DialogTitle>
        <DialogContent>
          <input
            type="file"
            accept=".rofl"
            onChange={handleFileSelect}
            style={{ marginTop: '1rem' }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setUploadOpen(false)}>Cancel</Button>
          <Button
            onClick={handleUpload}
            disabled={!uploadFile || uploading}
            variant="contained"
            color="primary"
          >
            {uploading ? <CircularProgress size={24} /> : 'Upload'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ReplayTab; 