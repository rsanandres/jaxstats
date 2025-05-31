import React, { useState } from 'react';
import { Tabs, Tab, Box, Typography } from '@mui/material';
import StatsTab from './components/StatsTab';
import ReplayTab from './components/ReplayTab';
import TerminalTab from './components/TerminalTab';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`simple-tabpanel-${index}`}
      aria-labelledby={`simple-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

function App() {
  const [tabValue, setTabValue] = useState(0);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  return (
    <Box sx={{ width: '100%' }}>
      <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Tabs value={tabValue} onChange={handleTabChange} aria-label="main tabs">
          <Tab label="Stats" />
          <Tab label="Replays" />
          <Tab label="Terminal" />
        </Tabs>
      </Box>
      <TabPanel value={tabValue} index={0}>
        <StatsTab />
      </TabPanel>
      <TabPanel value={tabValue} index={1}>
        <ReplayTab />
      </TabPanel>
      <TabPanel value={tabValue} index={2}>
        <TerminalTab />
      </TabPanel>
    </Box>
  );
}

export default App; 