'use client';

import { useEffect, useState } from 'react';

const BOOT_LINES = [
  { text: 'SENTINELX v2.4.1 — AUTONOMOUS THREAT HUNTING PLATFORM', delay: 0, color: '#00d4ff' },
  { text: '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', delay: 100, color: '#0f2a4a' },
  { text: '', delay: 200, color: '#fff' },
  { text: '[INIT] Loading threat intelligence modules...', delay: 400, color: '#475569' },
  { text: '[OK]   Sigma rule engine loaded — 2,847 rules active', delay: 700, color: '#22c55e' },
  { text: '[OK]   MITRE ATT&CK framework v14 loaded', delay: 1000, color: '#22c55e' },
  { text: '[OK]   Elasticsearch connection established', delay: 1300, color: '#22c55e' },
  { text: '[INIT] Starting correlation engine...', delay: 1600, color: '#475569' },
  { text: '[OK]   Event correlation engine online', delay: 1900, color: '#22c55e' },
  { text: '[OK]   Log ingestion pipeline active — 12,847 eps', delay: 2100, color: '#22c55e' },
  { text: '[INIT] Connecting to threat intelligence feeds...', delay: 2400, color: '#475569' },
  { text: '[OK]   VirusTotal feed connected', delay: 2600, color: '#22c55e' },
  { text: '[OK]   AlienVault OTX feed connected', delay: 2800, color: '#22c55e' },
  { text: '[OK]   Shodan feed connected', delay: 3000, color: '#22c55e' },
  { text: '[INIT] Loading AI investigation agent...', delay: 3300, color: '#475569' },
  { text: '[OK]   LLM agent initialized — Llama 3.3 70B', delay: 3600, color: '#22c55e' },
  { text: '[OK]   SOC analyst persona loaded', delay: 3800, color: '#22c55e' },
  { text: '', delay: 4000, color: '#fff' },
  { text: '[WARN] ACTIVE INCIDENT DETECTED — INC-2024-0115', delay: 4200, color: '#ffa502' },
  { text: '[WARN] Risk Score: 94/100 — CRITICAL', delay: 4400, color: '#ff4757' },
  { text: '[WARN] 4 hosts compromised — investigation required', delay: 4600, color: '#ff4757' },
  { text: '', delay: 4800, color: '#fff' },
  { text: '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', delay: 4900, color: '#0f2a4a' },
  { text: 'ALL SYSTEMS OPERATIONAL — LOADING DASHBOARD...', delay: 5000, color: '#00d4ff' },
];

interface BootSequenceProps {
  onComplete: () => void;
}

export default function BootSequence({ onComplete }: BootSequenceProps) {
  const [visibleLines, setVisibleLines] = useState<number[]>([]);
  const [done, setDone] = useState(false);
  const [fadeOut, setFadeOut] = useState(false);

  useEffect(() => {
    const timers: ReturnType<typeof setTimeout>[] = [];

    BOOT_LINES.forEach((line, i) => {
      timers.push(setTimeout(() => {
        setVisibleLines(prev => [...prev, i]);
      }, line.delay));
    });

    timers.push(setTimeout(() => {
      setFadeOut(true);
      timers.push(setTimeout(() => {
        setDone(true);
        onComplete();
      }, 800));
    }, 5600));

    return () => timers.forEach(clearTimeout);
  }, [onComplete]);

  if (done) return null;

  return (
    <div style={{
      position: 'fixed',
      inset: 0,
      background: '#050c1a',
      zIndex: 9999,
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'center',
      alignItems: 'center',
      opacity: fadeOut ? 0 : 1,
      transition: 'opacity 0.8s ease',
    }}>

      {/* Logo */}
      <div style={{ marginBottom: '40px', textAlign: 'center' }}>
        <div style={{ fontSize: '36px', fontWeight: 700, letterSpacing: '8px', color: '#fff', fontFamily: "'Courier New', monospace" }}>
          SENTINEL<span style={{ color: '#00d4ff' }}>X</span>
        </div>
        <div style={{ fontSize: '10px', color: '#334155', letterSpacing: '4px', marginTop: '6px', fontFamily: "'Courier New', monospace" }}>
          AUTONOMOUS THREAT HUNTING PLATFORM
        </div>
      </div>

      {/* Terminal */}
      <div style={{
        width: '600px',
        background: '#070f1f',
        border: '1px solid #0f2a4a',
        borderRadius: '8px',
        padding: '24px',
        fontFamily: "'Courier New', monospace",
        fontSize: '12px',
        lineHeight: 1.8,
        minHeight: '320px',
      }}>
        {BOOT_LINES.map((line, i) => (
          visibleLines.includes(i) && (
            <div
              key={i}
              style={{
                color: line.color,
                animation: 'fadeIn 0.2s ease-out',
              }}
            >
              {line.text || '\u00A0'}
            </div>
          )
        ))}

        {/* Blinking cursor */}
        <span style={{
          display: 'inline-block',
          width: '8px',
          height: '14px',
          background: '#00d4ff',
          animation: 'blink 1s infinite',
          verticalAlign: 'middle',
          marginLeft: '2px',
        }} />
      </div>

      {/* Skip button */}
      <button
        onClick={() => { setFadeOut(true); setTimeout(() => { setDone(true); onComplete(); }, 800); }}
        style={{
          marginTop: '24px',
          background: 'transparent',
          border: '1px solid #0f2a4a',
          borderRadius: '4px',
          padding: '6px 16px',
          color: '#1e3a5f',
          fontSize: '10px',
          cursor: 'pointer',
          fontFamily: "'Courier New', monospace",
          letterSpacing: '1px',
        }}>
        SKIP BOOT SEQUENCE
      </button>

      <style>{`
        @keyframes fadeIn { from{opacity:0;transform:translateY(4px)} to{opacity:1;transform:translateY(0)} }
        @keyframes blink { 0%,100%{opacity:1} 50%{opacity:0} }
      `}</style>
    </div>
  );
}
