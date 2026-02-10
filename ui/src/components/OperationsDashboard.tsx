import { useEffect, useState } from 'react'
import { useOperationsStore, type Job, type JobStatus } from '../stores/operationsStore'
import { useAppStore } from '../store'
import './OperationsDashboard.css'

interface OperationsDashboardProps {
  isOpen: boolean
  onClose: () => void
}

export function OperationsDashboard({ isOpen, onClose }: OperationsDashboardProps) {
  const {
    systemMetrics,
    jobs,
    usageMetrics,
    budgetSettings,
    privacySettings,
    isLoadingMetrics,
    isLoadingJobs,
    isLoadingUsage,
    activeTab,
    setActiveTab,
    refreshSystemMetrics,
    refreshJobs,
    refreshUsage,
    cancelJob,
    retryJob,
    clearCompletedJobs,
    updateBudgetSettings,
    updatePrivacySettings,
    getPendingJobsCount,
    getInProgressJobsCount,
    getCompletedJobsCount,
    getFailedJobsCount,
    getBudgetPercentage,
    getBudgetStatus,
  } = useOperationsStore()
  
  const { addToast } = useAppStore()
  const [showBudgetWarning, setShowBudgetWarning] = useState(false)
  
  // Refresh data when panel opens
  useEffect(() => {
    if (isOpen) {
      refreshSystemMetrics()
      refreshJobs()
      refreshUsage()
    }
  }, [isOpen, refreshSystemMetrics, refreshJobs, refreshUsage])
  
  // Check budget warning
  useEffect(() => {
    const status = getBudgetStatus()
    if (status === 'critical' || status === 'exceeded') {
      setShowBudgetWarning(true)
    }
  }, [budgetSettings.currentSpent, getBudgetStatus])
  
  if (!isOpen) return null
  
  const budgetPercentage = getBudgetPercentage()
  const budgetStatus = getBudgetStatus()
  
  const tabs = [
    { id: 'metrics' as const, label: '📊 Metrics', icon: '📈' },
    { id: 'jobs' as const, label: '⚙️ Jobs', icon: '⚙️' },
    { id: 'usage' as const, label: '💰 Usage', icon: '💳' },
    { id: 'privacy' as const, label: '🔒 Privacy', icon: '🛡️' },
  ]
  
  const getStatusColor = (status: JobStatus) => {
    switch (status) {
      case 'completed': return '#4caf50'
      case 'processing': return '#4a9eff'
      case 'pending': return '#ff9800'
      case 'failed': return '#ef4444'
      case 'cancelled': return '#888'
      default: return '#888'
    }
  }
  
  const getJobTypeIcon = (type: Job['type']) => {
    switch (type) {
      case 'text_generation': return '✍️'
      case 'image_generation': return '🎨'
      case 'lora_training': return '🧠'
      case 'analysis': return '🔍'
      default: return '⚙️'
    }
  }
  
  return (
    <div className="operations-dashboard-overlay" onClick={onClose}>
      <div className="operations-dashboard" onClick={e => e.stopPropagation()}>
        {/* Header */}
        <div className="operations-header">
          <h2>🔧 Operations Dashboard</h2>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>
        
        {/* Budget Warning Banner */}
        {showBudgetWarning && (
          <div className={`budget-banner ${budgetStatus}`}>
            <span className="banner-icon">
              {budgetStatus === 'exceeded' ? '⛔' : '⚠️'}
            </span>
            <span className="banner-text">
              {budgetStatus === 'exceeded'
                ? `Budget exceeded! You've spent $${budgetSettings.currentSpent.toFixed(2)} of $${budgetSettings.monthlyBudget}`
                : `Budget warning: ${budgetPercentage.toFixed(0)}% used ($${budgetSettings.currentSpent.toFixed(2)} of $${budgetSettings.monthlyBudget})`}
            </span>
            <button className="banner-dismiss" onClick={() => setShowBudgetWarning(false)}>×</button>
          </div>
        )}
        
        {/* Tabs */}
        <div className="operations-tabs">
          {tabs.map(tab => (
            <button
              key={tab.id}
              className={`tab-btn ${activeTab === tab.id ? 'active' : ''}`}
              onClick={() => setActiveTab(tab.id)}
            >
              <span>{tab.icon}</span>
              <span>{tab.label}</span>
            </button>
          ))}
        </div>
        
        {/* Content */}
        <div className="operations-content">
          {/* Metrics Tab */}
          {activeTab === 'metrics' && (
            <div className="metrics-tab">
              {isLoadingMetrics ? (
                <div className="loading-state">Loading metrics...</div>
              ) : systemMetrics ? (
                <>
                  {/* Latency Section */}
                  <div className="metric-section">
                    <h3>⏱️ Latency</h3>
                    <div className="latency-stats">
                      <div className="latency-stat">
                        <span className="stat-label">P50</span>
                        <span className="stat-value">{systemMetrics.latency.p50}ms</span>
                      </div>
                      <div className="latency-stat">
                        <span className="stat-label">P95</span>
                        <span className="stat-value">{systemMetrics.latency.p95}ms</span>
                      </div>
                      <div className="latency-stat">
                        <span className="stat-label">P99</span>
                        <span className="stat-value">{systemMetrics.latency.p99}ms</span>
                      </div>
                    </div>
                    <div className="mini-chart">
                      {systemMetrics.latency.history.map((point, i) => (
                        <div
                          key={i}
                          className="chart-bar"
                          style={{
                            height: `${Math.min(100, (point.value / 500) * 100)}%`,
                            background: point.value > 300 ? '#ef4444' : point.value > 150 ? '#ff9800' : '#4caf50',
                          }}
                          title={`${new Date(point.timestamp).toLocaleTimeString()}: ${point.value.toFixed(0)}ms`}
                        />
                      ))}
                    </div>
                  </div>
                  
                  {/* Success Rate Gauge */}
                  <div className="metric-section">
                    <h3>✅ Success Rate</h3>
                    <div className="gauge-container">
                      <div className="gauge">
                        <svg viewBox="0 0 100 50">
                          <path
                            d="M 10 50 A 40 40 0 0 1 90 50"
                            fill="none"
                            stroke="#333"
                            strokeWidth="10"
                          />
                          <path
                            d="M 10 50 A 40 40 0 0 1 90 50"
                            fill="none"
                            stroke={systemMetrics.successRate.current > 95 ? '#4caf50' : systemMetrics.successRate.current > 90 ? '#ff9800' : '#ef4444'}
                            strokeWidth="10"
                            strokeDasharray={`${systemMetrics.successRate.current * 1.26} 126`}
                            className="gauge-fill"
                          />
                        </svg>
                        <div className="gauge-value">{systemMetrics.successRate.current.toFixed(1)}%</div>
                      </div>
                    </div>
                  </div>
                  
                  {/* Error Rate */}
                  <div className="metric-section">
                    <h3>❌ Error Rate</h3>
                    <div className="error-rate-main">{systemMetrics.errorRate.current.toFixed(2)}%</div>
                    <div className="error-breakdown">
                      {Object.entries(systemMetrics.errorRate.byType).map(([type, rate]) => (
                        <div key={type} className="error-type">
                          <span className="error-type-name">{type.replace('_', ' ')}</span>
                          <span className="error-type-rate">{rate.toFixed(1)}%</span>
                          <div className="error-bar">
                            <div
                              className="error-bar-fill"
                              style={{ width: `${(rate / systemMetrics.errorRate.current) * 100}%` }}
                            />
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </>
              ) : (
                <div className="empty-state">No metrics available</div>
              )}
            </div>
          )}
          
          {/* Jobs Tab */}
          {activeTab === 'jobs' && (
            <div className="jobs-tab">
              {/* Job Stats */}
              <div className="job-stats">
                <div className="job-stat">
                  <span className="stat-icon">⏳</span>
                  <span className="stat-count">{getPendingJobsCount()}</span>
                  <span className="stat-label">Pending</span>
                </div>
                <div className="job-stat">
                  <span className="stat-icon">⚙️</span>
                  <span className="stat-count">{getInProgressJobsCount()}</span>
                  <span className="stat-label">In Progress</span>
                </div>
                <div className="job-stat">
                  <span className="stat-icon">✅</span>
                  <span className="stat-count">{getCompletedJobsCount()}</span>
                  <span className="stat-label">Completed</span>
                </div>
                <div className="job-stat">
                  <span className="stat-icon">❌</span>
                  <span className="stat-count">{getFailedJobsCount()}</span>
                  <span className="stat-label">Failed</span>
                </div>
              </div>
              
              {/* Job List */}
              {isLoadingJobs ? (
                <div className="loading-state">Loading jobs...</div>
              ) : jobs.length > 0 ? (
                <>
                  <div className="jobs-list">
                    {jobs.map(job => (
                      <div key={job.id} className={`job-item ${job.status}`}>
                        <div className="job-icon">{getJobTypeIcon(job.type)}</div>
                        <div className="job-info">
                          <div className="job-description">{job.description}</div>
                          <div className="job-meta">
                            <span className="job-status" style={{ color: getStatusColor(job.status) }}>
                              {job.status}
                            </span>
                            <span className="job-time">
                              {new Date(job.createdAt).toLocaleTimeString()}
                            </span>
                          </div>
                          {job.status === 'processing' && (
                            <div className="job-progress">
                              <div
                                className="progress-bar"
                                style={{ width: `${job.progress}%` }}
                              />
                            </div>
                          )}
                          {job.error && (
                            <div className="job-error">{job.error}</div>
                          )}
                        </div>
                        <div className="job-actions">
                          {job.status === 'pending' && (
                            <button
                              className="job-action-btn"
                              onClick={() => cancelJob(job.id)}
                              title="Cancel"
                            >
                              ✕
                            </button>
                          )}
                          {job.status === 'processing' && (
                            <button
                              className="job-action-btn"
                              onClick={() => cancelJob(job.id)}
                              title="Cancel"
                            >
                              ⏹️
                            </button>
                          )}
                          {job.status === 'failed' && (
                            <button
                              className="job-action-btn retry"
                              onClick={() => retryJob(job.id)}
                              title="Retry"
                            >
                              🔄
                            </button>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                  
                  <button
                    className="clear-completed-btn"
                    onClick={clearCompletedJobs}
                  >
                    Clear Completed
                  </button>
                </>
              ) : (
                <div className="empty-state">No jobs in queue</div>
              )}
            </div>
          )}
          
          {/* Usage Tab */}
          {activeTab === 'usage' && (
            <div className="usage-tab">
              {isLoadingUsage ? (
                <div className="loading-state">Loading usage data...</div>
              ) : usageMetrics ? (
                <>
                  {/* Current Period */}
                  <div className="usage-section">
                    <h3>📅 Current Period</h3>
                    <div className="usage-summary">
                      <div className="usage-card">
                        <span className="usage-label">Total Cost</span>
                        <span className="usage-value">${usageMetrics.currentPeriod.totalCost.toFixed(2)}</span>
                      </div>
                      <div className="usage-card">
                        <span className="usage-label">Tokens</span>
                        <span className="usage-value">{(usageMetrics.currentPeriod.totalTokens / 1000).toFixed(1)}k</span>
                      </div>
                      <div className="usage-card">
                        <span className="usage-label">Requests</span>
                        <span className="usage-value">{usageMetrics.currentPeriod.requestCount}</span>
                      </div>
                    </div>
                  </div>
                  
                  {/* Budget Progress */}
                  <div className="usage-section">
                    <h3>💰 Budget</h3>
                    <div className="budget-progress">
                      <div className="budget-info">
                        <span>${budgetSettings.currentSpent.toFixed(2)} spent</span>
                        <span>${budgetSettings.monthlyBudget.toFixed(2)} limit</span>
                      </div>
                      <div className="progress-track">
                        <div
                          className={`progress-fill ${budgetStatus}`}
                          style={{ width: `${Math.min(100, budgetPercentage)}%` }}
                        />
                        {/* Threshold markers */}
                        <div
                          className="threshold-marker warning"
                          style={{ left: `${budgetSettings.warningThresholds.warning}%` }}
                          title="50% Warning"
                        />
                        <div
                          className="threshold-marker critical"
                          style={{ left: `${budgetSettings.warningThresholds.critical}%` }}
                          title="80% Critical"
                        />
                      </div>
                      <div className="budget-percentage">{budgetPercentage.toFixed(1)}%</div>
                    </div>
                    
                    {/* Budget Settings */}
                    <div className="budget-settings">
                      <label>
                        Monthly Budget ($)
                        <input
                          type="number"
                          min="1"
                          max="10000"
                          value={budgetSettings.monthlyBudget}
                          onChange={(e) => updateBudgetSettings({ monthlyBudget: Number(e.target.value) })}
                        />
                      </label>
                    </div>
                  </div>
                  
                  {/* Usage by Branch */}
                  <div className="usage-section">
                    <h3>🌿 Usage by Branch</h3>
                    <div className="branch-usage-list">
                      {usageMetrics.byBranch.map(branch => (
                        <div key={branch.branchId} className="branch-usage-item">
                          <span className="branch-name">{branch.branchId}</span>
                          <div className="branch-bar-container">
                            <div
                              className="branch-bar"
                              style={{
                                width: `${(branch.tokens / usageMetrics.currentPeriod.totalTokens) * 100}%`,
                              }}
                            />
                          </div>
                          <span className="branch-cost">${branch.cost.toFixed(2)}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                  
                  {/* Usage by Operation */}
                  <div className="usage-section">
                    <h3>⚙️ Usage by Operation</h3>
                    <div className="operation-usage-list">
                      {usageMetrics.byOperation.map(op => (
                        <div key={op.operation} className="operation-usage-item">
                          <span className="operation-name">{op.operation}</span>
                          <span className="operation-stats">
                            {op.requests} requests • ${op.cost.toFixed(2)}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                </>
              ) : (
                <div className="empty-state">No usage data available</div>
              )}
            </div>
          )}
          
          {/* Privacy Tab */}
          {activeTab === 'privacy' && (
            <div className="privacy-tab">
              {/* Local-Only Mode */}
              <div className="privacy-section">
                <h3>🏠 Local-Only Mode</h3>
                <label className="privacy-toggle">
                  <input
                    type="checkbox"
                    checked={privacySettings.localOnly}
                    onChange={(e) => updatePrivacySettings({ localOnly: e.target.checked })}
                  />
                  <span className="toggle-slider" />
                  <span className="toggle-label">
                    {privacySettings.localOnly ? 'Enabled' : 'Disabled'}
                  </span>
                </label>
                <p className="privacy-description">
                  When enabled, all processing happens locally. No data is sent to external servers.
                </p>
              </div>
              
              {/* External Providers */}
              <div className="privacy-section">
                <h3>☁️ External Providers</h3>
                <label className="privacy-toggle">
                  <input
                    type="checkbox"
                    checked={privacySettings.externalProviders.enabled}
                    onChange={(e) =>
                      updatePrivacySettings({
                        externalProviders: {
                          ...privacySettings.externalProviders,
                          enabled: e.target.checked,
                        },
                      })
                    }
                    disabled={privacySettings.localOnly}
                  />
                  <span className="toggle-slider" />
                  <span className="toggle-label">
                    {privacySettings.externalProviders.enabled ? 'Enabled' : 'Disabled'}
                  </span>
                </label>
                
                {privacySettings.externalProviders.enabled && !privacySettings.localOnly && (
                  <div className="provider-select">
                    <label>Provider</label>
                    <select
                      value={privacySettings.externalProviders.provider || ''}
                      onChange={(e) =>
                        updatePrivacySettings({
                          externalProviders: {
                            ...privacySettings.externalProviders,
                            provider: e.target.value as any,
                          },
                        })
                      }
                    >
                      <option value="openai">OpenAI</option>
                      <option value="anthropic">Anthropic</option>
                      <option value="custom">Custom</option>
                    </select>
                  </div>
                )}
              </div>
              
              {/* Data Retention */}
              <div className="privacy-section">
                <h3>🗑️ Data Retention</h3>
                <label className="privacy-toggle">
                  <input
                    type="checkbox"
                    checked={privacySettings.dataRetention.enabled}
                    onChange={(e) =>
                      updatePrivacySettings({
                        dataRetention: {
                          ...privacySettings.dataRetention,
                          enabled: e.target.checked,
                        },
                      })
                    }
                  />
                  <span className="toggle-slider" />
                  <span className="toggle-label">
                    Auto-delete old data
                  </span>
                </label>
                
                {privacySettings.dataRetention.enabled && (
                  <div className="retention-setting">
                    <label>Keep data for</label>
                    <select
                      value={privacySettings.dataRetention.retentionDays}
                      onChange={(e) =>
                        updatePrivacySettings({
                          dataRetention: {
                            ...privacySettings.dataRetention,
                            retentionDays: Number(e.target.value),
                          },
                        })
                      }
                    >
                      <option value={7}>7 days</option>
                      <option value={30}>30 days</option>
                      <option value={90}>90 days</option>
                      <option value={365}>1 year</option>
                    </select>
                  </div>
                )}
              </div>
              
              {/* Data Export/Delete */}
              <div className="privacy-section danger-zone">
                <h3>⚠️ Danger Zone</h3>
                <div className="danger-actions">
                  <button
                    className="danger-btn secondary"
                    onClick={() => addToast({ message: 'Export started...', type: 'info' })}
                  >
                    📥 Export All Data
                  </button>
                  <button
                    className="danger-btn"
                    onClick={() => {
                      if (confirm('Are you sure? This will permanently delete all your data.')) {
                        addToast({ message: 'All data deleted', type: 'warning' })
                      }
                    }}
                  >
                    🗑️ Delete All Data
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
