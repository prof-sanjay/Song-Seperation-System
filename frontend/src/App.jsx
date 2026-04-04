import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { UploadCloud, Music, Download, Mic2, AlertCircle, Loader2 } from 'lucide-react';

export default function App() {
  const [file, setFile] = useState(null);
  const [fileId, setFileId] = useState(null);
  const [status, setStatus] = useState('idle'); // idle, uploading, processing, completed, error
  const [errorMessage, setErrorMessage] = useState('');
  const [results, setResults] = useState(null);
  const [keyInfo, setKeyInfo] = useState(null);
  const [activeModule, setActiveModule] = useState('separation'); // 'separation' | 'scale'
  const fileInputRef = useRef(null);

  // Poll for status when in 'processing' state
  useEffect(() => {
    let intervalId;
    
    if (status === 'processing' && fileId) {
      intervalId = setInterval(async () => {
        try {
          const res = await axios.get(`/api/status/${fileId}`);
          if (res.data.status === 'completed') {
            setStatus('completed');
            setResults(res.data.files_available);
            fetchKeyInfo(fileId);
            clearInterval(intervalId);
          } else if (res.data.status === 'not_found') {
             // In case backend wiped or failed fatally
             setStatus('error');
             setErrorMessage('Processing session lost. Please try uploading again.');
             clearInterval(intervalId);
          }
        } catch (err) {
          console.error("Polling error", err);
        }
      }, 3000); // Poll every 3 seconds
    }
    
    return () => clearInterval(intervalId);
  }, [status, fileId]);

  const fetchKeyInfo = async (id) => {
    try {
      const res = await axios.get(`/api/download/${id}/key.json`);
      setKeyInfo(res.data || null);
    } catch (e) {
      console.warn("Could not load key info", e);
    }
  };

  const handleFileSelect = (e) => {
    const selected = e.target.files[0];
    if (selected && (selected.type.includes('audio') || selected.name.match(/\.(mp3|wav|flac|m4a|ogg)$/i))) {
      setFile(selected);
      setErrorMessage('');
      setStatus('idle');
      setFileId(null);
    } else {
      setFile(null);
      setErrorMessage('Please select a valid audio file (.mp3, .wav)');
    }
  };

  const handleUploadClick = () => {
    if (fileInputRef.current) fileInputRef.current.click();
  };

  const handleUploadSubmit = async () => {
    if (!file) return;
    
    setStatus('uploading');
    const formData = new FormData();
    formData.append('file', file);
    
    try {
      const res = await axios.post('/api/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setFileId(res.data.file_id);
      setStatus('processing');
    } catch (err) {
      setStatus('error');
      setErrorMessage(err.response?.data?.detail || 'An error occurred during upload.');
    }
  };

  const handleScaleSubmit = async () => {
    if (!file) return;
    
    setStatus('processing');
    const formData = new FormData();
    formData.append('file', file);
    
    try {
      const res = await axios.post('/api/scale', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      // Skip the polling loop entirely, this API returned instantly!
      setKeyInfo(res.data);
      setStatus('completed');
    } catch (err) {
      setStatus('error');
      setErrorMessage(err.response?.data?.detail || 'An error occurred during scale detection.');
    }
  };

  const handleDownload = (fileName) => {
    window.location.href = `/api/download/${fileId}/${fileName}`;
  };

  const renderUploadState = () => (
    <div className="upload-card" onClick={handleUploadClick}>
      <input 
        type="file" 
        className="upload-input" 
        ref={fileInputRef}
        onChange={handleFileSelect}
        accept="audio/*"
      />
      <UploadCloud className="upload-icon" />
      <h2>{file ? file.name : "Select Audio File"}</h2>
      <p className="subtitle">Supported formats: MP3, WAV, FLAC, M4A</p>
      
      <button 
        className="btn-primary" 
        onClick={(e) => {
          e.stopPropagation();
          activeModule === 'separation' ? handleUploadSubmit() : handleScaleSubmit();
        }}
        disabled={!file}
      >
        {activeModule === 'separation' ? 'Start Separation' : 'Detect Scale'}
      </button>

      {errorMessage && (
        <div className="error-message">
          <AlertCircle size={18} style={{marginRight: '8px', verticalAlign: 'middle'}}/>
          {errorMessage}
        </div>
      )}
    </div>
  );

  const renderProcessingState = () => (
    <div className="status-container">
      <div className="spinner"></div>
      <h2>{status === 'uploading' ? 'Uploading Track...' : 'Demuxing AI Audio Pipeline...'}</h2>
      <p className="subtitle">
        {status === 'processing' ? 'This usually takes a moment. Applying Demucs and YIN Pitch detection.' : 'Transferring file securely.'}
      </p>
      {fileId && <div className="file-id-badge">ID: {fileId}</div>}
    </div>
  );

  const renderCompletedState = () => (
    <div className="results-container">
      <h2>{activeModule === 'separation' ? 'Studio Stems Ready!' : 'Scale Analysis Complete!'}</h2>
      
      {activeModule === 'separation' && ['vocals.wav', 'drums.wav', 'bass.wav', 'guitar.wav', 'piano.wav'].map((trackName) => (
        <div key={trackName} className="track-card">
          <div className="track-info">
            {trackName === 'vocals.wav' ? <Mic2 className="track-icon" size={28}/> : <Music className="track-icon" size={28}/>}
            <div style={{fontWeight: 600, textTransform: 'capitalize'}}>{trackName.replace('.wav', '')}</div>
          </div>
          
          <audio controls src={`/api/download/${fileId}/${trackName}`} />
          
          <button className="btn-download" onClick={() => handleDownload(trackName)}>
            <Download size={16} /> Download
          </button>
        </div>
      ))}
      
      {activeModule === 'scale' && keyInfo && (
        <div className="notes-container">
          <h3 style={{marginTop: 0, display: 'flex', alignItems: 'center', gap: '8px'}}>
            <Music size={18} color="#c084fc"/> Detected Musical Key
          </h3>
          <div className="notes-list" style={{padding: '2rem 0', justifyContent: 'center'}}>
            <span className="note-badge" style={{fontSize: '1.5rem', padding: '1rem 2rem'}}>
              {keyInfo.key} <span style={{opacity: 0.7, fontSize: '1rem', marginLeft: '0.5rem'}}>(Confidence: {(keyInfo.confidence * 100).toFixed(1)}%)</span>
            </span>
          </div>
        </div>
      )}
      
      <div style={{textAlign: 'center', marginTop: '1rem'}}>
        <button className="btn-primary" onClick={() => {
            setFile(null);
            setStatus('idle');
            setFileId(null);
            setKeyInfo(null);
        }}>Process Another Track</button>
      </div>
    </div>
  );

  return (
    <div className="app-container">
      <header>
        <h1>Acoustica</h1>
        <p className="subtitle">AI-Powered Source Separation & Pitch Analysis</p>
      </header>
      
      {status === 'idle' && (
        <div className="tabs-container">
          <button 
            className={`tab-btn ${activeModule === 'separation' ? 'active' : ''}`} 
            onClick={() => setActiveModule('separation')}
          >
            Stem Separation
          </button>
          <button 
            className={`tab-btn ${activeModule === 'scale' ? 'active' : ''}`} 
            onClick={() => setActiveModule('scale')}
          >
            Scale & Key Detection
          </button>
        </div>
      )}

      <main>
        {(status === 'idle' || status === 'error') && renderUploadState()}
        {(status === 'uploading' || status === 'processing') && renderProcessingState()}
        {status === 'completed' && renderCompletedState()}
      </main>
    </div>
  );
}
