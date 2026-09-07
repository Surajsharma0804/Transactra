'use client';

import { useState } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import {
  Shield, CheckCircle, XCircle, Hash, ArrowRight, Link2,
  Loader2, ArrowLeft, Lock, Eye,
} from 'lucide-react';
import toast from 'react-hot-toast';
import { evidenceApi } from '@/lib/api';

interface EvidenceRecord {
  sequence: number;
  event_type: string;
  data: Record<string, unknown>;
  timestamp: string;
  record_hash: string;
  prev_hash: string;
}

interface VerifyResult {
  sequence: number;
  event_type: string;
  expected_hash: string;
  actual_hash: string;
  passed: boolean;
}

export default function VerifyPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const initialOrderId = searchParams.get('orderId') || '';

  const [orderId, setOrderId] = useState(initialOrderId);
  const [chain, setChain] = useState<{ chain_id: string; length: number; head_hash: string; records: EvidenceRecord[] } | null>(null);
  const [verifyResults, setVerifyResults] = useState<{ chain_valid: boolean; message: string; record_results: VerifyResult[] } | null>(null);
  const [loading, setLoading] = useState(false);
  const [verifying, setVerifying] = useState(false);

  const fetchChain = async () => {
    if (!orderId.trim()) {
      toast.error('Enter an order ID');
      return;
    }
    setLoading(true);
    setVerifyResults(null);
    try {
      const data = await evidenceApi.getChain(orderId.trim());
      setChain(data);
    } catch (err: any) {
      toast.error(err?.detail || 'Chain not found');
      setChain(null);
    } finally {
      setLoading(false);
    }
  };

  const verifyChain = async () => {
    if (!orderId.trim()) return;
    setVerifying(true);
    try {
      const data = await evidenceApi.verify(orderId.trim());
      setVerifyResults(data);
      if (data.chain_valid) {
        toast.success('Evidence chain verified — tamper-free');
      } else {
        toast.error('Chain verification FAILED — tampering detected');
      }
    } catch (err: any) {
      toast.error(err?.detail || 'Verification failed');
    } finally {
      setVerifying(false);
    }
  };

  const formatHash = (hash: string) => {
    if (!hash) return '—';
    return hash.slice(0, 8) + '···' + hash.slice(-8);
  };

  const formatEventType = (t: string) => {
    return t.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
  };

  return (
    <div className="max-w-3xl space-y-6">
      <button
        onClick={() => router.back()}
        className="flex items-center gap-1.5 text-sm"
        style={{ color: 'var(--text-muted)' }}
      >
        <ArrowLeft className="w-3.5 h-3.5" /> Back
      </button>

      <div>
        <h1 className="text-2xl font-semibold flex items-center gap-2" style={{ color: 'var(--text)' }}>
          <Shield className="w-6 h-6" style={{ color: 'var(--accent)' }} />
          Verify Transaction
        </h1>
        <p className="text-sm mt-1" style={{ color: 'var(--text-secondary)' }}>
          Re-compute SHA-256 hashes and verify the evidence chain is tamper-free
        </p>
      </div>

      {/* Order ID Input */}
      <div className="card p-5">
        <label className="text-xs font-medium block mb-2" style={{ color: 'var(--text-muted)' }}>
          Order ID
        </label>
        <div className="flex gap-3">
          <input
            type="text"
            value={orderId}
            onChange={(e) => setOrderId(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && fetchChain()}
            placeholder="Enter order UUID"
            className="input flex-1"
          />
          <button onClick={fetchChain} disabled={loading} className="btn-primary" style={{ minWidth: 100 }}>
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Load Chain'}
          </button>
        </div>
      </div>

      {/* Evidence Chain */}
      {chain && (
        <>
          <div className="card p-5">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-sm font-medium" style={{ color: 'var(--text)' }}>
                  Evidence Chain · {chain.length} record{chain.length !== 1 ? 's' : ''}
                </h2>
                <p className="text-xs mt-0.5 font-mono" style={{ color: 'var(--text-muted)' }}>
                  Head: {formatHash(chain.head_hash)}
                </p>
              </div>
              <button onClick={verifyChain} disabled={verifying} className="btn-primary flex items-center gap-2">
                {verifying ? <Loader2 className="w-4 h-4 animate-spin" /> : <Lock className="w-4 h-4" />}
                Verify Chain
              </button>
            </div>

            {/* Chain Records */}
            <div className="space-y-0">
              {chain.records.map((record, idx) => {
                const vr = verifyResults?.record_results.find(r => r.sequence === record.sequence);
                const passed = vr?.passed;

                return (
                  <div key={record.sequence}>
                    {/* Connector Line */}
                    {idx > 0 && (
                      <div className="flex items-center gap-2 py-1.5 pl-5">
                        <Link2 className="w-3 h-3" style={{ color: 'var(--border)' }} />
                        <span className="text-[10px] font-mono" style={{ color: 'var(--text-muted)' }}>
                          prev_hash: {formatHash(record.prev_hash)}
                        </span>
                      </div>
                    )}

                    {/* Record Block */}
                    <div
                      className="card p-4"
                      style={{
                        borderLeft: vr
                          ? `3px solid ${passed ? '#10b981' : '#ef4444'}`
                          : '3px solid var(--border)',
                      }}
                    >
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <span className="text-[10px] font-mono font-semibold px-1.5 py-0.5 rounded"
                            style={{ background: 'var(--bg-subtle)', color: 'var(--text-muted)' }}>
                            #{record.sequence}
                          </span>
                          <span className="text-sm font-medium" style={{ color: 'var(--text)' }}>
                            {formatEventType(record.event_type)}
                          </span>
                        </div>
                        {vr && (
                          passed
                            ? <CheckCircle className="w-4 h-4" style={{ color: '#10b981' }} />
                            : <XCircle className="w-4 h-4" style={{ color: '#ef4444' }} />
                        )}
                      </div>

                      <div className="flex items-center gap-1.5 mb-2">
                        <Hash className="w-3 h-3" style={{ color: 'var(--text-muted)' }} />
                        <span className="text-[10px] font-mono" style={{ color: 'var(--text-muted)' }}>
                          {formatHash(record.record_hash)}
                        </span>
                      </div>

                      {/* Data */}
                      <details className="text-xs">
                        <summary
                          className="cursor-pointer flex items-center gap-1"
                          style={{ color: 'var(--text-muted)' }}
                        >
                          <Eye className="w-3 h-3" /> View data
                        </summary>
                        <pre
                          className="mt-2 p-3 rounded text-[11px] overflow-x-auto"
                          style={{ background: 'var(--bg-subtle)', color: 'var(--text-secondary)' }}
                        >
                          {JSON.stringify(record.data, null, 2)}
                        </pre>
                      </details>

                      <p className="text-[10px] mt-2" style={{ color: 'var(--text-muted)' }}>
                        {new Date(record.timestamp).toLocaleString()}
                      </p>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Verification Summary */}
          {verifyResults && (
            <div
              className="card p-5"
              style={{
                borderLeft: `3px solid ${verifyResults.chain_valid ? '#10b981' : '#ef4444'}`,
              }}
            >
              <div className="flex items-center gap-2 mb-2">
                {verifyResults.chain_valid
                  ? <CheckCircle className="w-5 h-5" style={{ color: '#10b981' }} />
                  : <XCircle className="w-5 h-5" style={{ color: '#ef4444' }} />
                }
                <span className="text-sm font-semibold" style={{ color: 'var(--text)' }}>
                  {verifyResults.chain_valid ? 'Chain Verified — Tamper-Free' : 'CHAIN BROKEN — Tampering Detected'}
                </span>
              </div>
              <p className="text-xs" style={{ color: 'var(--text-muted)' }}>
                {verifyResults.message}
              </p>
              <div className="mt-3 flex gap-4 text-xs" style={{ color: 'var(--text-secondary)' }}>
                <span>Records: {verifyResults.record_results.length}</span>
                <span>Passed: {verifyResults.record_results.filter(r => r.passed).length}</span>
                <span>Failed: {verifyResults.record_results.filter(r => !r.passed).length}</span>
              </div>
            </div>
          )}
        </>
      )}

      {/* Empty state */}
      {!chain && !loading && (
        <div className="card p-12 text-center">
          <Shield className="w-10 h-10 mx-auto mb-3" style={{ color: 'var(--border)' }} />
          <h2 className="text-lg font-medium mb-1" style={{ color: 'var(--text)' }}>
            Verify Any Transaction
          </h2>
          <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
            Enter an order ID to load and verify its SHA-256 hash-linked evidence chain.
            Every authorization step is cryptographically proven — not just claimed.
          </p>
        </div>
      )}
    </div>
  );
}
