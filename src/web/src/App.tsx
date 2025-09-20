import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';

import Dashboard from './pages/Dashboard';
import AnswerSubmission from './pages/AnswerSubmission';
import ScoringList from './pages/ScoringList';
import ScoringDetail from './pages/ScoringDetail';
import ScoringReview from './pages/ScoringReview';
import BatchUpload from './pages/BatchUpload';
import AdminPanel from './pages/AdminPanel';
import Navigation from './components/Navigation';

const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
  typography: {
    fontFamily: '"Noto Sans JP", "Roboto", "Helvetica", "Arial", sans-serif',
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Navigation />
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/answer" element={<AnswerSubmission />} />
          <Route path="/scoring" element={<ScoringList />} />
          <Route path="/scoring/:id" element={<ScoringDetail />} />
          <Route path="/scoring/:id/review" element={<ScoringReview />} />
          <Route path="/batch-upload" element={<BatchUpload />} />
          <Route path="/admin" element={<AdminPanel />} />
        </Routes>
      </Router>
    </ThemeProvider>
  );
}

export default App;