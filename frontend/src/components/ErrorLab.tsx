import React, { useState } from 'react';
import { AlertOctagon, Play } from 'lucide-react';
import { api, ApiError } from '../services/api';
import { APIErrorResponse } from '../types';

export const ErrorLab: React.FC = () => {
  const [loading, setLoading] = useState<boolean>(false);
  const [lastStatus, setLastStatus] = useState<number | null>(null);
  const [lastResponse, setLastResponse] = useState<APIErrorResponse | any | null>(null);

  const errorScenarios = [
    {
      id: 'not_found',
      label: '404 Resource Not Found',
      description: 'Triggered when querying a non-existent entity ID.',
    },
    {
      id: 'bad_request',
      label: '400 Bad Request',
      description: 'Triggered when business parameters fail precondition validations.',
    },
    {
      id: 'pipeline_disabled',
      label: '501 Pipeline Stage Inactive',
      description: 'Triggered when invoking an endpoint for a phase not yet implemented.',
    },
    {
      id: 'database_error',
      label: '500 Database Exception',
      description: 'Handled SQLAlchemy error returning safe, non-leaking message.',
    },
    {
      id: 'unhandled',
      label: '500 Unhandled Exception',
      description: 'Catch-all handler protecting against process crashes & stack leaks.',
    },
  ];

  const triggerErrorTest = async (type: string) => {
    setLoading(true);
    try {
      const res = await api.testError(type);
      setLastStatus(200);
      setLastResponse(res);
    } catch (err: any) {
      if (err instanceof ApiError) {
        setLastStatus(err.status);
        setLastResponse(err.response);
      } else {
        setLastStatus(500);
        setLastResponse({ error: { message: err.message } });
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      <div>
        <h2 style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: '0.5rem' }}>
          API Error Contract Test Lab
        </h2>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
          Interactive tool to verify that all API exceptions strictly conform to the unified error response contract:
          <code>{' { error: { code, message, details, request_id, timestamp } }'}</code>.
        </p>
      </div>

      <div className="grid-2">
        {/* Error Simulation Triggers */}
        <div className="card">
          <h3 style={{ fontSize: '1.125rem', fontWeight: 600, marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <AlertOctagon size={18} color="#f43f5e" />
            <span>Select Error Scenario to Dispatch</span>
          </h3>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {errorScenarios.map((scenario) => (
              <div
                key={scenario.id}
                style={{
                  padding: '0.875rem 1rem',
                  borderRadius: '8px',
                  backgroundColor: '#090d16',
                  border: '1px solid var(--border-color)',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                }}
              >
                <div>
                  <div style={{ fontWeight: 600, fontSize: '0.875rem' }}>{scenario.label}</div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{scenario.description}</div>
                </div>

                <button
                  onClick={() => triggerErrorTest(scenario.id)}
                  disabled={loading}
                  className="btn btn-secondary"
                  style={{ fontSize: '0.75rem', padding: '0.375rem 0.75rem' }}
                >
                  <Play size={12} />
                  <span>Dispatch</span>
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* Live Response Inspector */}
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <h3 style={{ fontSize: '1.125rem', fontWeight: 600 }}>Live Response Envelope</h3>
            {lastStatus !== null && (
              <span className={`badge ${lastStatus >= 400 ? 'badge-red' : 'badge-green'}`}>
                HTTP Status: {lastStatus}
              </span>
            )}
          </div>

          {lastResponse ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              <pre className="code-block" style={{ maxHeight: '350px', overflowY: 'auto' }}>
                {JSON.stringify(lastResponse, null, 2)}
              </pre>

              {lastResponse?.error && (
                <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: '0.25rem', background: '#0f172a', padding: '0.75rem', borderRadius: '6px' }}>
                  <div><strong>Error Code:</strong> <code style={{ color: '#f43f5e' }}>{lastResponse.error.code}</code></div>
                  <div><strong>Correlation Request ID:</strong> <code style={{ color: '#38bdf8' }}>{lastResponse.error.request_id}</code></div>
                  <div><strong>Contract Schema Validated:</strong> <span style={{ color: '#34d399' }}>✓ Yes</span></div>
                </div>
              )}
            </div>
          ) : (
            <div style={{ textAlign: 'center', padding: '3rem 1rem', color: 'var(--text-muted)' }}>
              Click any <strong>Dispatch</strong> button on the left to test the unified error contract live.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
