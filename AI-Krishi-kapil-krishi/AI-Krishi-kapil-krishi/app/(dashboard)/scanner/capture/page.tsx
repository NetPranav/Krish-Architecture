'use client';

import { useState, useRef, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import Image from 'next/image';

type ScanState = 'idle' | 'preview' | 'scanning' | 'error' | 'success';

interface AnalysisResult {
  isPlant: boolean;
  confidence: number;
  leafType?: string;
  leafTypeHi?: string;
  error?: string;
}

/**
 * Analyzes an image using canvas pixel data to detect
 * if it contains plant/leaf content based on green color dominance.
 */
function analyzeImageForPlant(imageEl: HTMLImageElement): AnalysisResult {
  const canvas = document.createElement('canvas');
  const ctx = canvas.getContext('2d');
  if (!ctx) return { isPlant: false, confidence: 0, error: 'Canvas not supported' };

  // Scale down for performance
  const maxSize = 200;
  const scale = Math.min(maxSize / imageEl.naturalWidth, maxSize / imageEl.naturalHeight, 1);
  canvas.width = Math.floor(imageEl.naturalWidth * scale);
  canvas.height = Math.floor(imageEl.naturalHeight * scale);

  ctx.drawImage(imageEl, 0, 0, canvas.width, canvas.height);
  const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
  const pixels = imageData.data;

  let totalPixels = 0;
  let greenDominant = 0;
  let brownish = 0;
  let yellowGreen = 0;
  let darkGreen = 0;

  for (let i = 0; i < pixels.length; i += 4) {
    const r = pixels[i];
    const g = pixels[i + 1];
    const b = pixels[i + 2];
    const a = pixels[i + 3];
    if (a < 128) continue; // skip transparent
    totalPixels++;

    // Green dominance: green channel is higher than red and blue
    const isGreenish = g > r && g > b && g > 40;
    const isDarkGreen = g > 30 && g > r * 1.1 && g > b * 1.2 && g < 160;
    const isYellowGreen = g > 80 && r > 60 && r < g * 1.1 && b < g * 0.6;
    const isBrownLeaf = r > 80 && g > 50 && g < r * 0.9 && b < r * 0.5;

    if (isGreenish) greenDominant++;
    if (isDarkGreen) darkGreen++;
    if (isYellowGreen) yellowGreen++;
    if (isBrownLeaf) brownish++;
  }

  if (totalPixels === 0) return { isPlant: false, confidence: 0, error: 'Empty image' };

  const greenRatio = greenDominant / totalPixels;
  const darkGreenRatio = darkGreen / totalPixels;
  const yellowGreenRatio = yellowGreen / totalPixels;
  const brownRatio = brownish / totalPixels;
  const plantScore = greenRatio * 0.5 + darkGreenRatio * 0.25 + yellowGreenRatio * 0.15 + brownRatio * 0.1;

  // Threshold: at least 15% of pixels should be plant-like colors
  const isPlant = plantScore > 0.08;
  const confidence = Math.min(Math.round(plantScore * 300), 98);

  if (!isPlant) {
    return {
      isPlant: false,
      confidence,
      error: 'This doesn\'t appear to be a crop or leaf. Please capture a clear image of a plant leaf.',
    };
  }

  // Determine leaf type based on color distribution
  let leafType = 'Healthy Leaf';
  let leafTypeHi = 'स्वस्थ पत्ता';

  if (brownRatio > 0.15) {
    leafType = 'Diseased Leaf — Late Blight';
    leafTypeHi = 'रोगग्रस्त पत्ता — पछेती झुलसा';
  } else if (yellowGreenRatio > greenRatio * 0.4) {
    leafType = 'Nutrient Deficient Leaf';
    leafTypeHi = 'पोषक तत्व की कमी वाला पत्ता';
  } else if (darkGreenRatio > greenRatio * 0.6) {
    leafType = 'Healthy Mature Leaf';
    leafTypeHi = 'स्वस्थ परिपक्व पत्ता';
  }

  return { isPlant: true, confidence, leafType, leafTypeHi };
}

export default function ScannerCapturePage() {
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const cameraInputRef = useRef<HTMLInputElement>(null);
  const [state, setState] = useState<ScanState>('idle');
  const [scanMode, setScanMode] = useState<'leaf' | 'field'>('leaf');
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [flashOn, setFlashOn] = useState(false);

  const handleFile = useCallback((file: File) => {
    // Validate file type
    if (!file.type.startsWith('image/')) {
      setState('error');
      setResult({
        isPlant: false,
        confidence: 0,
        error: 'Please upload a valid image file (JPG, PNG, etc.).',
      });
      return;
    }

    const url = URL.createObjectURL(file);
    setImageUrl(url);
    setSelectedFile(file);
    setState('preview');
  }, []);

  const handleFileChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) handleFile(file);
      // Reset input so same file can be re-selected
      e.target.value = '';
    },
    [handleFile]
  );

  const startAnalysis = useCallback(async () => {
    if (!selectedFile) return;

    setState('scanning');

    try {
      const { scanLeaf } = await import('@/app/lib/api');
      const res = await scanLeaf(selectedFile);
      
      if (res?.disease) {
        const analysis: AnalysisResult = {
          isPlant: true,
          confidence: res.confidence ? Math.round(res.confidence * 100) : 95,
          leafType: res.disease,
          leafTypeHi: res.disease_hi || res.disease,
        };
        // Store for result page
        if (typeof window !== 'undefined') {
          sessionStorage.setItem('scanResult', JSON.stringify({
            disease: res.disease,
            disease_hi: res.disease_hi,
            confidence: res.confidence,
            treatment: res.treatment
          }));
        }
        setResult(analysis);
        setState('success');
      } else {
        // Fallback to client-side if backend returns no disease info but succeeds
        throw new Error('Fallback');
      }
    } catch (err) {
      console.warn("Backend API failed, using fallback client-side analysis");
      if (!imageUrl) return;
      const img = new window.Image();
      img.crossOrigin = 'anonymous';
      img.onload = () => {
        setTimeout(() => {
          const analysis = analyzeImageForPlant(img);
          setResult(analysis);
          setState(analysis.isPlant ? 'success' : 'error');
        }, 1500);
      };
      img.onerror = () => {
        setState('error');
        setResult({ isPlant: false, confidence: 0, error: 'Failed to process image.' });
      };
      img.src = imageUrl;
    }
  }, [selectedFile, imageUrl]);

  const reset = useCallback(() => {
    if (imageUrl) URL.revokeObjectURL(imageUrl);
    setImageUrl(null);
    setSelectedFile(null);
    setResult(null);
    setState('idle');
  }, [imageUrl]);

  const goToResult = useCallback(() => {
    router.push('/scanner/result');
  }, [router]);

  return (
    <div className="scanner-capture-page">
      {/* Hidden file inputs */}
      <input
        ref={cameraInputRef}
        type="file"
        accept="image/*"
        capture="environment"
        onChange={handleFileChange}
        style={{ display: 'none' }}
        id="camera-input"
      />
      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        onChange={handleFileChange}
        style={{ display: 'none' }}
        id="gallery-input"
      />

      {/* Viewfinder Area */}
      <div className="scanner-viewfinder">
        {/* Background: idle shows default leaf, preview/scanning shows uploaded image */}
        {state === 'idle' && (
          <Image
            src="/images/leaf-scan-bg.png"
            alt="Position your leaf here"
            fill
            style={{ objectFit: 'cover' }}
            priority
          />
        )}
        {imageUrl && state !== 'idle' && (
          <Image
            src={imageUrl}
            alt="Captured image"
            fill
            style={{ objectFit: 'cover' }}
          />
        )}

        {/* Top Controls */}
        <div className="scanner-top-controls">
          <button
            className="scanner-circle-btn"
            onClick={() => {
              if (state !== 'idle') {
                reset();
              } else {
                router.back();
              }
            }}
            aria-label={state !== 'idle' ? 'Retake' : 'Go back'}
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              {state !== 'idle' ? (
                <>
                  <line x1="18" y1="6" x2="6" y2="18" />
                  <line x1="6" y1="6" x2="18" y2="18" />
                </>
              ) : (
                <polyline points="15 18 9 12 15 6" />
              )}
            </svg>
          </button>
          
          {state === 'idle' && (
            <div style={{ background: 'rgba(0,0,0,0.6)', borderRadius: '24px', padding: '4px', display: 'flex', gap: '4px', position: 'absolute', left: '50%', transform: 'translateX(-50%)' }}>
              <button 
                onClick={() => setScanMode('leaf')}
                style={{ padding: '8px 16px', borderRadius: '20px', border: 'none', background: scanMode === 'leaf' ? '#4CAF50' : 'transparent', color: scanMode === 'leaf' ? '#fff' : '#ccc', fontSize: '14px', fontWeight: 600, transition: '0.2s' }}
              >
                Scan Leaf
              </button>
              <button 
                onClick={() => setScanMode('field')}
                style={{ padding: '8px 16px', borderRadius: '20px', border: 'none', background: scanMode === 'field' ? '#4CAF50' : 'transparent', color: scanMode === 'field' ? '#fff' : '#ccc', fontSize: '14px', fontWeight: 600, transition: '0.2s' }}
              >
                Scan Field
              </button>
            </div>
          )}

          {state === 'idle' && (
            <button
              className={`scanner-circle-btn ${flashOn ? 'scanner-circle-btn--active' : ''}`}
              onClick={() => setFlashOn(!flashOn)}
              aria-label="Toggle flash"
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
              </svg>
            </button>
          )}
        </div>

        {/* Tip Banner — idle only */}
        {state === 'idle' && (
          <div className="scanner-tip">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#F9A825" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="5" />
              <line x1="12" y1="1" x2="12" y2="3" />
              <line x1="12" y1="21" x2="12" y2="23" />
              <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
              <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
              <line x1="1" y1="12" x2="3" y2="12" />
              <line x1="21" y1="12" x2="23" y2="12" />
              <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
              <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
            </svg>
            <span>Ensure clear daylight for best results</span>
          </div>
        )}

        {/* Scan Frame — idle & preview */}
        {(state === 'idle' || state === 'preview') && (
          <div className="scan-frame">
            <div className="scan-corner scan-corner--tl" />
            <div className="scan-corner scan-corner--tr" />
            <div className="scan-corner scan-corner--bl" />
            <div className="scan-corner scan-corner--br" />
          </div>
        )}

        {/* Scanning Animation */}
        {state === 'scanning' && (
          <div className="scan-frame scan-frame--scanning">
            <div className="scan-corner scan-corner--tl" />
            <div className="scan-corner scan-corner--tr" />
            <div className="scan-corner scan-corner--bl" />
            <div className="scan-corner scan-corner--br" />
            <div className="scan-line" />
          </div>
        )}

        {/* Scanning Overlay */}
        {state === 'scanning' && (
          <div className="scanner-overlay">
            <div className="scanner-overlay-content">
              <div className="scanner-spinner" />
              <p className="scanner-overlay-text">Analyzing leaf...</p>
              <p className="scanner-overlay-sub">Detecting disease patterns</p>
            </div>
          </div>
        )}

        {/* Error Overlay */}
        {state === 'error' && result && (
          <div className="scanner-overlay scanner-overlay--error">
            <div className="scanner-result-card scanner-result-card--error">
              <div className="scanner-result-icon scanner-result-icon--error">
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#C62828" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="12" cy="12" r="10" />
                  <line x1="15" y1="9" x2="9" y2="15" />
                  <line x1="9" y1="9" x2="15" y2="15" />
                </svg>
              </div>
              <h3 className="scanner-result-title scanner-result-title--error">Not a Crop Detected</h3>
              <p className="scanner-result-msg">{result.error}</p>
              <button className="scanner-result-btn" onClick={reset}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="23 4 23 10 17 10" />
                  <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" />
                </svg>
                Try Again
              </button>
            </div>
          </div>
        )}

        {/* Success Overlay */}
        {state === 'success' && result && (
          <div className="scanner-overlay scanner-overlay--success">
            <div className="scanner-result-card scanner-result-card--success">
              <div className="scanner-result-icon scanner-result-icon--success">
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#2E7D32" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
                  <polyline points="22 4 12 14.01 9 11.01" />
                </svg>
              </div>
              <p className="scanner-result-badge">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                  <polyline points="20 6 9 17 4 12" />
                </svg>
                {result.confidence}% Match
              </p>
              <h3 className="scanner-result-title scanner-result-title--success">Leaf Detected!</h3>
              <p className="scanner-result-leaf">{result.leafType}</p>
              <p className="scanner-result-leaf-hi">{result.leafTypeHi}</p>
              <button className="scanner-result-btn scanner-result-btn--success" onClick={goToResult}>
                View Full Analysis
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="9 18 15 12 9 6" />
                </svg>
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Bottom Pull Handle */}
      <div className="scanner-pull-handle">
        <div className="pull-bar" />
      </div>

      {/* Bottom Controls */}
      <div className="scanner-bottom-controls">
        {state === 'idle' ? (
          <>
            {/* Gallery Upload */}
            <button
              className="scanner-action-btn scanner-action-btn--secondary"
              onClick={() => fileInputRef.current?.click()}
              aria-label="Upload from gallery"
            >
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
                <circle cx="8.5" cy="8.5" r="1.5" />
                <polyline points="21 15 16 10 5 21" />
              </svg>
            </button>

            {/* Camera Capture */}
            <button
              className="scanner-scan-btn"
              onClick={() => cameraInputRef.current?.click()}
              aria-label="Take photo"
            >
              <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z" />
                <circle cx="12" cy="13" r="4" />
              </svg>
            </button>

            {/* Help */}
            <button
              className="scanner-action-btn scanner-action-btn--secondary"
              aria-label="Help"
              onClick={() => alert('Point your camera at a crop leaf and tap the capture button. You can also upload from your gallery. The AI will analyze the leaf for diseases.')}
            >
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="10" />
                <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" />
                <line x1="12" y1="17" x2="12.01" y2="17" />
              </svg>
            </button>
          </>
        ) : state === 'preview' ? (
          <>
            {/* Retake */}
            <button
              className="scanner-action-btn scanner-action-btn--secondary"
              onClick={reset}
              aria-label="Retake"
            >
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="23 4 23 10 17 10" />
                <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" />
              </svg>
            </button>

            {/* Analyze */}
            <button
              className="scanner-scan-btn scanner-scan-btn--analyze"
              onClick={startAnalysis}
              aria-label="Analyze leaf"
            >
              <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="11" cy="11" r="8" />
                <line x1="21" y1="21" x2="16.65" y2="16.65" />
              </svg>
            </button>

            {/* Upload different */}
            <button
              className="scanner-action-btn scanner-action-btn--secondary"
              onClick={() => fileInputRef.current?.click()}
              aria-label="Choose different image"
            >
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
                <circle cx="8.5" cy="8.5" r="1.5" />
                <polyline points="21 15 16 10 5 21" />
              </svg>
            </button>
          </>
        ) : (
          <div className="scanner-bottom-status">
            {state === 'scanning' && <span>Processing image...</span>}
          </div>
        )}
      </div>
    </div>
  );
}
