'use client';

import { useEffect, useRef, useState } from 'react';
import { Bot, Send, Sparkles, UserRound } from 'lucide-react';
import AppShell from '../components/AppShell';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

const SUGGESTED = [
  'What attack pattern matches this incident?',
  'What MITRE techniques were used?',
  'How do I contain lateral movement?',
  'Generate an incident report summary',
  'What are the immediate mitigation steps?',
  'Is this consistent with APT29 behavior?',
];

const SYSTEM_PROMPT = `You are SentinelX AI, an expert cybersecurity analyst assistant built into an enterprise SOC platform.

If someone greets you or makes small talk, respond naturally and warmly. When asked about security, threats, incidents, or technical topics, switch into expert SOC analyst mode and be structured, technical, and actionable.

Current active incident:
- Incident ID: INC-2024-0115
- Attacker IP: 185.220.101.8 external, 10.0.0.45 internal
- Attack chain: Recon -> Brute Force T1110 -> Lateral Movement T1021 -> Data Access T1005 -> Exfiltration T1041
- Hosts hit: auth-server-01, web-server-02, file-server-03, db-server-01
- Data lost: 2.4GB to 45.33.32.156
- Time: 09:23 to 10:15 UTC
- Risk Score: 94/100`;

function formatMessage(text: string): string {
  return text
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/^\* (.+)/gm, '<div class="message-list-item">$1</div>')
    .replace(/^- (.+)/gm, '<div class="message-list-item">$1</div>')
    .replace(/^(\d+)\. (.+)/gm, '<div class="message-list-item numbered"><span>$1.</span>$2</div>')
    .replace(/\n\n/g, '<br/><br/>')
    .replace(/\n/g, '<br/>');
}

export default function Assistant() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'assistant',
      content: 'Hey, I am SentinelX AI. I can help explain the active incident, prioritize containment, or draft an executive-ready report.\n\nWhat would you like to investigate first?',
      timestamp: '',
    },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendMessage = async (text: string) => {
    if (!text.trim() || loading) return;
    const userMsg: Message = { role: 'user', content: text, timestamp: new Date().toLocaleTimeString('en-GB') };
    const updatedMessages = [...messages, userMsg];
    setMessages(updatedMessages);
    setInput('');
    setLoading(true);

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: [
            { role: 'system', content: SYSTEM_PROMPT },
            ...updatedMessages.map((m) => ({ role: m.role, content: m.content })),
          ],
        }),
      });
      const data = await response.json();
      const reply = data.choices?.[0]?.message?.content || 'No response received.';
      setMessages((prev) => [...prev, { role: 'assistant', content: reply, timestamp: new Date().toLocaleTimeString('en-GB') }]);
    } catch {
      setMessages((prev) => [...prev, { role: 'assistant', content: 'Connection error. Please try again.', timestamp: new Date().toLocaleTimeString('en-GB') }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <AppShell active="assistant" statusText="AI agent online">
      <section className="assistant-layout">
        <div className="chat-panel">
          <div className="chat-header">
            <div>
              <p className="section-label">SentinelX AI</p>
              <h1>Incident analyst workspace</h1>
            </div>
            <div className="status-chip internal"><span /> Model connected</div>
          </div>

          <div className="message-stream">
            {messages.map((msg, i) => (
              <div className={`message-row ${msg.role}`} key={`${msg.timestamp}-${i}`}>
                <div className="message-avatar">{msg.role === 'assistant' ? <Bot size={18} /> : <UserRound size={18} />}</div>
                <div className="message-body">
                  <div className="message-meta">{msg.role === 'assistant' ? 'SentinelX AI' : 'Analyst'} / {msg.timestamp}</div>
                  <div className="message-bubble" dangerouslySetInnerHTML={{ __html: formatMessage(msg.content) }} />
                </div>
              </div>
            ))}
            {loading && (
              <div className="message-row assistant">
                <div className="message-avatar"><Bot size={18} /></div>
                <div className="message-body">
                  <div className="message-meta">SentinelX AI / thinking</div>
                  <div className="message-bubble typing"><span /><span /><span /></div>
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          <div className="composer">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && sendMessage(input)}
              placeholder="Ask about containment, evidence, timeline, or reporting..."
            />
            <button className="primary-button" onClick={() => sendMessage(input)} disabled={loading}>
              <Send size={16} />
              Send
            </button>
          </div>
        </div>

        <aside className="assistant-sidebar">
          <article className="panel">
            <p className="section-label">Suggested queries</p>
            <div className="query-list">
              {SUGGESTED.map((query) => (
                <button key={query} onClick={() => sendMessage(query)}>
                  <Sparkles size={14} />
                  {query}
                </button>
              ))}
            </div>
          </article>

          <article className="panel">
            <p className="section-label">Incident snapshot</p>
            {[
              ['ID', 'INC-2024-0115'],
              ['Risk', '94 / 100'],
              ['Hosts', '4 compromised'],
              ['Data loss', '2.4 GB'],
              ['Duration', '52 minutes'],
              ['Stages', '5 detected'],
            ].map(([label, value]) => (
              <div className="list-row" key={label}>
                <span>{label}</span>
                <strong>{value}</strong>
              </div>
            ))}
          </article>
        </aside>
      </section>
    </AppShell>
  );
}
